"""Read-only cross-border synchronization job handler."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from config import MeatConfig


SUPPORTED_PLATFORMS = frozenset({"temu", "aliexpress"})


def handle_crossborder_sync(job: dict[str, Any], cfg: "MeatConfig") -> dict[str, Any]:
    args = job.get("args") if isinstance(job.get("args"), dict) else {}
    platform = str(args.get("platform") or "").strip().lower()
    if platform not in SUPPORTED_PLATFORMS:
        return {
            "ok": False,
            "need_login": False,
            "error": f"unsupported platform: {platform or 'empty'}",
        }
    account_ref = str(args.get("account_ref") or "").strip()
    scope = str(args.get("scope") or "").strip().lower()
    if not account_ref or not scope:
        return {
            "ok": False,
            "need_login": False,
            "error": "account_ref and scope are required",
        }
    from crossborder.dispatch import run_sync

    return run_sync(platform=platform, account_ref=account_ref, scope=scope, args=args, cfg=cfg)
