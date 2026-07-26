"""AliExpress 卖家后台浏览器上下文（持久化 Profile）。"""
from __future__ import annotations

import sys
import time
from contextlib import contextmanager
from typing import Generator

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from app.browser.ae_session import ae_session_ready, is_login_page, persist_ae_session
from app.browser.context import human_pause
from app.browser.stealth import BROWSER_ARGS, IGNORE_DEFAULT_ARGS, STEALTH_INIT_SCRIPT
from app.config import (
    AE_CSP_HOME,
    AE_LOGIN_POLL_SECONDS,
    AE_LOGIN_WAIT_SECONDS,
    is_ae_headless,
    resolve_aliexpress_profile_dir,
)


def _ae_launch_kwargs(headless: bool) -> dict:
    """AliExpress 登录页对 Playwright 指纹更敏感，单独收紧启动参数。"""
    from app.config import BROWSER_CHANNEL

    args: list[str] = []
    for arg in BROWSER_ARGS:
        if arg.startswith("--window-size="):
            continue
        if arg == "--no-sandbox" and sys.platform.startswith("win") and not headless:
            continue
        args.append(arg)
    if not headless:
        args.append("--start-maximized")

    kwargs: dict = {
        "headless": headless,
        "args": args,
        "ignore_default_args": sorted(set(IGNORE_DEFAULT_ARGS) | {"--no-sandbox"}),
        "locale": "zh-CN",
        "timezone_id": "Asia/Shanghai",
    }
    if headless:
        kwargs["args"].append("--headless=new")
        kwargs["viewport"] = {"width": 1280, "height": 900}
    else:
        kwargs["no_viewport"] = True
        if BROWSER_CHANNEL:
            kwargs["channel"] = BROWSER_CHANNEL
    return kwargs


def wait_for_ae_login(page: Page, *, tenant_id: int, context: BrowserContext | None = None) -> None:
    ctx = context or page.context
    deadline = time.time() + AE_LOGIN_WAIT_SECONDS
    while time.time() < deadline:
        url = page.url or ""
        cookies = ctx.cookies()
        if ae_session_ready(url, cookies):
            persist_ae_session(tenant_id, page, ctx)
            human_pause()
            return
        if time.time() >= deadline:
            break
        time.sleep(AE_LOGIN_POLL_SECONDS)
    raise RuntimeError(
        f"AliExpress 卖家后台未登录（tenant={tenant_id}），"
        f"请先运行: py login_aliexpress.py --tenant-id {tenant_id}"
    )


@contextmanager
def open_aliexpress_context(
    tenant_id: int,
    *,
    headless: bool | None = None,
) -> Generator[tuple[Playwright, BrowserContext], None, None]:
    profile_dir = resolve_aliexpress_profile_dir(tenant_id)
    profile_dir.mkdir(parents=True, exist_ok=True)
    resolved_headless = is_ae_headless() if headless is None else headless

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile_dir),
            **(_ae_launch_kwargs(resolved_headless)),
        )
        context.add_init_script(STEALTH_INIT_SCRIPT)
        try:
            yield playwright, context
        finally:
            context.close()


def get_or_open_csp_page(context: BrowserContext) -> Page:
    preferred: Page | None = None
    fallback: Page | None = None
    for page in context.pages:
        url = page.url or ""
        if "aliexpress.com" not in url.lower():
            continue
        if is_login_page(url):
            fallback = fallback or page
            continue
        if "csp.aliexpress.com" in url.lower() or "gsp.aliexpress.com" in url.lower():
            preferred = page
            break
        fallback = fallback or page
    page = preferred or fallback
    if page is None:
        page = context.new_page()
    page.goto(AE_CSP_HOME, wait_until="domcontentloaded", timeout=120_000)
    human_pause()
    return page
