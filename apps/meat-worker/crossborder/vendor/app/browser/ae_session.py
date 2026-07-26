"""AliExpress 卖家后台会话缓存与 Cookie 快照（按租户 Profile 持久化）。"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page

from app.config import resolve_aliexpress_profile_dir

AE_SESSION_CACHE = ".crosshub-ae-session.json"
AE_COOKIE_SNAPSHOT = ".crosshub-ae-cookies.json"
AE_SESSION_COOKIE_NAMES = frozenset(
    {"gmp_sid", "xman_us_t", "JSESSIONID", "xman_us_f", "sgcookie", "cna"}
)
DEFAULT_CACHE_MAX_AGE = 30 * 86400


def is_login_page(url: str) -> bool:
    lowered = (url or "").lower()
    return "login.aliexpress.com" in lowered or "/login" in lowered


def _session_cache_path(tenant_id: int) -> Path:
    return resolve_aliexpress_profile_dir(tenant_id) / AE_SESSION_CACHE


def _cookie_snapshot_path(tenant_id: int) -> Path:
    return resolve_aliexpress_profile_dir(tenant_id) / AE_COOKIE_SNAPSHOT


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def filter_ae_cookies(cookies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cookie in cookies:
        domain = str(cookie.get("domain") or "")
        if "aliexpress" not in domain.lower():
            continue
        rows.append(
            {
                "name": cookie.get("name") or "",
                "value": cookie.get("value") or "",
                "domain": domain,
                "path": cookie.get("path") or "/",
                "expires": cookie.get("expires"),
                "httpOnly": bool(cookie.get("httpOnly")),
                "secure": bool(cookie.get("secure")),
                "sameSite": cookie.get("sameSite"),
            }
        )
    return rows


def ae_session_ready(url: str, cookies: list[dict[str, Any]]) -> bool:
    if is_login_page(url or ""):
        return False
    lowered = (url or "").lower()
    if "aliexpress.com" not in lowered:
        return False
    names = {str(c.get("name") or "") for c in filter_ae_cookies(cookies)}
    if not names & AE_SESSION_COOKIE_NAMES:
        return False
    return lowered.startswith("https://csp.aliexpress.com") or lowered.startswith(
        "https://gsp.aliexpress.com"
    )


def read_ae_session_cache(
    tenant_id: int,
    *,
    max_age_seconds: int = DEFAULT_CACHE_MAX_AGE,
) -> dict[str, Any] | None:
    cached = _read_json(_session_cache_path(tenant_id))
    if not cached:
        return None
    cached_at = float(cached.get("cached_at") or 0)
    if cached_at <= 0 or (time.time() - cached_at) > max_age_seconds:
        return None
    return cached


def read_ae_cookie_snapshot(tenant_id: int) -> dict[str, Any] | None:
    return _read_json(_cookie_snapshot_path(tenant_id))


def write_ae_session_cache(tenant_id: int, payload: dict[str, Any]) -> None:
    body = dict(payload)
    body["tenant_id"] = tenant_id
    body["cached_at"] = time.time()
    _write_json(_session_cache_path(tenant_id), body)


def write_ae_cookie_snapshot(tenant_id: int, cookies: list[dict[str, Any]], *, url: str = "") -> None:
    ae_cookies = filter_ae_cookies(cookies)
    _write_json(
        _cookie_snapshot_path(tenant_id),
        {
            "tenant_id": tenant_id,
            "saved_at": time.time(),
            "url": url,
            "cookie_count": len(ae_cookies),
            "cookie_names": sorted({c["name"] for c in ae_cookies if c.get("name")}),
            "cookies": ae_cookies,
        },
    )


def persist_ae_session(tenant_id: int, page: Page, context: BrowserContext) -> dict[str, Any]:
    url = page.url or ""
    cookies = context.cookies()
    ae_cookies = filter_ae_cookies(cookies)
    logged_in = ae_session_ready(url, cookies)
    payload = {
        "logged_in": logged_in,
        "ready": logged_in,
        "url": url,
        "title": "",
        "cookie_count": len(ae_cookies),
        "cookie_names": sorted({c["name"] for c in ae_cookies if c.get("name")}),
    }
    try:
        payload["title"] = page.title()
    except Exception:
        pass
    write_ae_session_cache(tenant_id, payload)
    if ae_cookies:
        write_ae_cookie_snapshot(tenant_id, cookies, url=url)
    return payload


def resolve_headless_for_ae_crawl(tenant_id: int) -> bool:
    """已有有效会话时优先无头复用 Profile Cookie，避免再次弹出登录窗。"""
    from app.config import is_ae_headless

    if is_ae_headless():
        return True
    cached = read_ae_session_cache(tenant_id)
    if cached and cached.get("logged_in"):
        return True
    cookies_file = (
        resolve_aliexpress_profile_dir(tenant_id) / "Default" / "Network" / "Cookies"
    )
    if cookies_file.is_file() and cookies_file.stat().st_size > 12_000:
        snapshot = read_ae_cookie_snapshot(tenant_id)
        if snapshot and snapshot.get("cookies"):
            return True
    return False
