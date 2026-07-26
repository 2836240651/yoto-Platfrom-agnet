"""Shared Temu seller session helpers for login assist, status probe, and crawl."""
from __future__ import annotations

from typing import Any


def session_ready(status: dict[str, Any]) -> bool:
    if status.get("ready"):
        return True
    if status.get("logged_in") or status.get("ready_hint"):
        mall_id = str(status.get("mall_id") or "").strip()
        if mall_id:
            return True
        return int(status.get("mall_count") or 0) > 0
    if status.get("requires_auth"):
        return False
    mall_id = str(status.get("mall_id") or "").strip()
    if mall_id:
        return True
    return int(status.get("mall_count") or 0) > 0


def build_session_payload(
    tenant_id: int,
    status: dict[str, Any],
    *,
    profile_busy: bool = False,
) -> dict[str, Any]:
    ready = session_ready(status)
    payload: dict[str, Any] = {
        "tenant_id": tenant_id,
        "ready": ready,
        "requires_auth": bool(status.get("requires_auth")),
        "logged_in": bool(status.get("logged_in")),
        "profile_busy": profile_busy,
        "mall_id": status.get("mall_id") or "",
        "mall_count": int(status.get("mall_count") or 0),
        "malls": status.get("malls") or [],
        "url": status.get("url") or "",
        "title": status.get("title") or "",
    }
    if profile_busy and not ready:
        payload["message"] = (
            "登录窗口已打开。请在 CrossHub 弹出的浏览器中完成登录并选择店铺，"
            "完成后点击「我已完成登录」或继续等待。"
        )
    elif not ready:
        payload["message"] = (
            "Temu 卖家后台尚未登录或未选择店铺。请点击「打开登录窗口」后，"
            "在弹出浏览器中完成登录。"
        )
    else:
        payload["message"] = "Temu 卖家后台已就绪，可以同步数据。"
    return payload


def cache_payload_from_status(tenant_id: int, status: dict[str, Any]) -> dict[str, Any]:
    return build_session_payload(tenant_id, status, profile_busy=False)
