"""
Temu 全托管运营数据爬虫

Playwright 持久化浏览器 + 卖家后台 API（与 Commander Agent 同路径）
"""
from __future__ import annotations

import time
from datetime import date

from app.browser.context import (
    close_tenant_profile_browsers,
    describe_session,
    ensure_logged_in,
    fetch_mall_list,
    get_or_open_seller_page,
    open_temu_context,
    set_mall_id,
    wait_for_login_and_mall,
)
from app.browser.profile_lock import (
    clear_profile_lock,
    clear_session_cache,
    is_profile_locked,
    read_session_cache,
    write_session_cache,
)
from app.browser.session_state import cache_payload_from_status, session_ready
from app.config import is_headless
from app.crawler.mapper import map_sales_batches
from app.crawler.temu_api import TemuApiClient


def ensure_profile_available(tenant_id: int, *, timeout_seconds: int = 30) -> None:
    cached = read_session_cache(tenant_id, max_age_seconds=1800)
    if cached and session_ready(cached) and is_profile_locked(tenant_id):
        close_tenant_profile_browsers(tenant_id)
        clear_profile_lock(tenant_id)
        time.sleep(1)
        return

    deadline = time.monotonic() + max(0, timeout_seconds)
    while is_profile_locked(tenant_id) and time.monotonic() < deadline:
        time.sleep(2)

    if is_profile_locked(tenant_id):
        cached = read_session_cache(tenant_id, max_age_seconds=1800)
        if cached and session_ready(cached):
            close_tenant_profile_browsers(tenant_id)
            clear_profile_lock(tenant_id)
            time.sleep(1)
            return
        raise RuntimeError(
            "Temu 登录窗口仍在使用中。请关闭 CrossHub 弹出的登录浏览器，再点击「刷新数据」。"
        )


def _resolve_malls(page, fallback_mall_id: str) -> list[dict]:
    malls = fetch_mall_list(page)
    if malls:
        return malls
    if fallback_mall_id:
        return [{"mallId": fallback_mall_id, "mallName": ""}]
    raise RuntimeError("未获取到可同步的 Temu 店铺列表，请重新登录并选择店铺。")


def crawl_temu_sales_live(report_day: str | None = None, *, tenant_id: int = 1) -> dict:
    report_time = report_day or date.today().isoformat()
    cached = read_session_cache(tenant_id, max_age_seconds=1800)

    ensure_profile_available(tenant_id)
    close_tenant_profile_browsers(tenant_id)

    with open_temu_context(tenant_id, headless=is_headless()) as (_, context):
        page = get_or_open_seller_page(context)
        try:
            if cached and session_ready(cached):
                mall_id = ensure_logged_in(page)
            else:
                mall_id = wait_for_login_and_mall(
                    page,
                    tenant_id=tenant_id,
                    timeout_seconds=90,
                    on_poll=lambda status: write_session_cache(
                        tenant_id,
                        cache_payload_from_status(tenant_id, status),
                    ),
                )
        except RuntimeError:
            clear_session_cache(tenant_id)
            raise

        client = TemuApiClient(page)
        client.ensure_sales_context()
        malls = _resolve_malls(page, mall_id)
        all_rows: list[dict] = []
        shops: list[dict] = []
        seen_shop_ids: set[str] = set()

        for mall in malls:
            current_mall_id = str(mall.get("mallId") or "").strip()
            if not current_mall_id:
                continue
            client.switch_mall(current_mall_id)
            shop_name, shop_id = client.get_shop_info()
            if not shop_name:
                shop_name = str(mall.get("mallName") or shop_id)
            batches = client.fetch_all_sales()
            all_rows.extend(
                map_sales_batches(
                    batches,
                    shop_id=shop_id,
                    shop_name=shop_name,
                    report_time=report_time,
                    tenant_id=tenant_id,
                )
            )
            if shop_id not in seen_shop_ids:
                seen_shop_ids.add(shop_id)
                shops.append(
                    {
                        "shop_id": shop_id,
                        "shop_name": shop_name,
                        "is_upload": True,
                        "tenant_id": tenant_id,
                    }
                )

        if not shops:
            raise RuntimeError("未同步到任何 Temu 店铺数据，请确认卖家后台已登录并选择店铺。")

        # 写回当前选中店铺，避免登录窗口/下次会话丢失 mall
        set_mall_id(page, str(shops[0]["shop_id"]))
        session = describe_session(page)
        write_session_cache(
            tenant_id,
            cache_payload_from_status(
                tenant_id,
                {
                    **session,
                    "logged_in": True,
                    "mall_id": shops[0]["shop_id"],
                    "mall_count": len(shops),
                    "malls": [
                        {"mallId": s["shop_id"], "mallName": s["shop_name"]}
                        for s in shops
                    ],
                    "requires_auth": False,
                },
            ),
        )
        return {"report_time": report_time, "shops": shops, "rows": all_rows}


def crawl_temu_sales(report_day: str | None = None, *, use_seed: bool = False, tenant_id: int = 1) -> dict:
    if use_seed:
        raise RuntimeError("种子数据模式已关闭，请完成 Temu 登录后使用真实爬取")
    return crawl_temu_sales_live(report_day, tenant_id=tenant_id)
