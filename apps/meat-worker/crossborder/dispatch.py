"""Platform dispatch for the single meat worker."""

from __future__ import annotations

from typing import Any

from crossborder.contract import SyncRequest, normalize_result


def run_sync(*, platform: str, account_ref: str, scope: str, args: dict[str, Any], cfg: Any) -> dict[str, Any]:
    try:
        request = SyncRequest.from_args(platform, account_ref, scope, args)
    except ValueError as exc:
        return {"ok": False, "need_login": False, "error": str(exc)}
    if request.platform == "temu":
        from crossborder.temu_sync import run
    else:
        from crossborder.aliexpress_sync import run
    return normalize_result(
        platform=request.platform,
        account_ref=request.account_ref,
        scope=request.scope,
        payload=run(request, cfg),
    )
