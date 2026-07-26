"""AliExpress read-only sync adapter extracted from SaaS-HZ."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from crossborder.contract import SyncRequest


def run(request: SyncRequest, cfg: Any) -> dict[str, Any]:
    if not request.account_ref.isdigit() or int(request.account_ref) <= 0:
        return {"ok": False, "need_login": False, "error": "AliExpress account_ref must be the positive local profile ID"}
    vendor_root = Path(__file__).resolve().parent / "vendor"
    if str(vendor_root) not in sys.path:
        sys.path.insert(0, str(vendor_root))
    os.environ["AE_PROFILE_ROOT"] = (
        os.environ.get("CROSSBORDER_ALI_PROFILE_ROOT", "").strip()
        or str(cfg.profile_dir() / "crossborder" / "aliexpress")
    )
    os.environ["AE_HEADLESS"] = "1" if not cfg.headed else "0"
    os.environ["CROSSBORDER_ALI_STORES_JSON"] = json.dumps([{"store_id": request.account_ref, "store_name": request.account_ref}])
    try:
        from app.crawler.aliexpress_crawler import crawl_aliexpress_operational

        payload = crawl_aliexpress_operational(
            request.date_end or None, tenant_id=int(request.account_ref), scope=request.scope
        )
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        return {"ok": False, "need_login": "登录" in message or "login" in message.lower(), "error": message[:500]}
    orders = payload.get("orders") if isinstance(payload.get("orders"), list) else []
    violations = payload.get("violations") if isinstance(payload.get("violations"), list) else []
    return {"ok": True, "summary": {"report_time": payload.get("report_time"), "order_count": len(orders), "violation_count": len(violations)}, "diagnostics": {"source": "aliexpress_seller", "mode": "playwright"}}
