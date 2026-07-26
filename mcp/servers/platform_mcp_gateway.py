# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2.0", "httpx>=0.27", "uvicorn>=0.30", "starlette>=0.37"]
# ///

"""Platform MCP gateway — long-running SSE / streamable-http.

Env:
  FASTMCP_HOST (default 127.0.0.1)
  FASTMCP_PORT (default 18765)
  FASTMCP_TRANSPORT (streamable-http | sse | stdio)
  COMMANDER_API_BASE / COMMANDER_ACCESS_TOKEN / COMMANDER_DEFAULT_AGENT_ID
  DOUYIN_WORKER_TOKEN / DOUYIN_JOB_DIR / DOUYIN_JOB_TIMEOUT_S

Dev:
  python mcp/servers/platform_mcp_gateway.py

Worker HTTP (same port, nginx /platform-mcp/):
  POST /worker/heartbeat | /worker/claim | /worker/complete
  GET  /worker/status
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Allow importing sibling modules when launched as a script.
_SERVERS_DIR = Path(__file__).resolve().parent
if str(_SERVERS_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVERS_DIR))

from commander_temu_client import (  # noqa: E402
    commander_product_issue_status,
    commander_product_issue_submit,
)
from social_automedia_client import (  # noqa: E402
    social_list_accounts as automedia_list_accounts,
    social_publish_status as automedia_publish_status,
    social_publish_submit as automedia_publish_submit,
)
import douyin_job_queue as djq  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402
from starlette.routing import Route  # noqa: E402

mcp = FastMCP(
    "platform_mcp",
    host=os.environ.get("FASTMCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("FASTMCP_PORT", "18765")),
)


@mcp.tool()
def ping(message: str = "hello") -> dict:
    """Health check for remote MCP mount."""
    return {"ok": True, "echo": message, "gateway": "platform_mcp"}


@mcp.tool()
def temu_product_issue_submit(
    file_path: str,
    shop_id: str,
    agent_id: str = "",
    platform: str = "temu",
    precheck: bool = True,
) -> dict:
    """Submit Temu listing Excel to Commander (black-box Job). file_path must be readable on the MCP host."""
    return commander_product_issue_submit(
        file_path=file_path,
        shop_id=shop_id,
        agent_id=agent_id or None,
        platform=platform or "temu",
        precheck=precheck,
    )


@mcp.tool()
def temu_product_issue_status(
    agent_id: str = "",
    platform: str = "temu",
    task_id: str = "",
    list_scope: str = "all",
) -> dict:
    """Poll Commander task_list for Temu / meat-machine listing status."""
    return commander_product_issue_status(
        agent_id=agent_id or None,
        platform=platform or "temu",
        task_id=task_id or None,
        list_scope=list_scope or "all",
    )


@mcp.tool()
def social_list_accounts() -> dict:
    """List automedia accounts + login-agent online status."""
    return automedia_list_accounts()


@mcp.tool()
def social_publish_submit(
    file_path: str = "",
    account_list_json: str = "[]",
    platform_type: int = 3,
    title: str = "",
    tags_json: str = "[]",
    agent_id: str = "",
    file_list_json: str = "[]",
) -> dict:
    """Upload (optional) + submit social publish to automedia. JSON array fields as strings."""
    import json

    def _arr(raw: str) -> list:
        try:
            val = json.loads(raw or "[]")
        except json.JSONDecodeError:
            return [x.strip() for x in (raw or "").split(",") if x.strip()]
        if isinstance(val, list):
            return val
        return []

    return automedia_publish_submit(
        file_path=file_path or "",
        file_list=_arr(file_list_json),
        account_list=_arr(account_list_json),
        platform_type=platform_type,
        title=title,
        tags=_arr(tags_json),
        agent_id=agent_id or "",
    )


@mcp.tool()
def social_publish_status(job_id: str) -> dict:
    """Poll automedia GET /publish/jobs/<job_id>."""
    return automedia_publish_status(job_id=job_id)


@mcp.tool()
def douyin_chanmama_auth_status() -> dict:
    """Meat-machine online + Chanmama login summary (no cookies)."""
    return djq.auth_status_summary()


@mcp.tool()
def crossborder_sync_submit(
    platform: str,
    account_ref: str,
    scope: str,
    date_start: str = "",
    date_end: str = "",
    force: bool = False,
) -> dict:
    """Queue a read-only Temu, AliExpress, or Amazon sync on the existing meat worker."""
    try:
        job = djq.enqueue_crossborder_sync(
            platform=platform,
            account_ref=account_ref,
            scope=scope,
            date_start=date_start,
            date_end=date_end,
            force=force,
        )
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "job_id": job["id"],
        "status": job["status"],
        "platform": job["args"]["platform"],
        "account_ref": job["args"]["account_ref"],
        "scope": job["args"]["scope"],
    }


@mcp.tool()
def crossborder_sync_status(job_id: str) -> dict:
    """Return sanitized status for a previously queued cross-border sync."""
    return djq.get_crossborder_sync(job_id)


@mcp.tool()
def crossborder_auth_status(platform: str = "", account_ref: str = "") -> dict:
    """Return worker/platform readiness without cookies, tokens, or browser OAuth values."""
    return djq.crossborder_auth_status(platform=platform, account_ref=account_ref)


@mcp.tool()
async def douyin_collect_hot_keywords(
    seed: str,
    date_range_days: int = 30,
    include_video: bool = True,
    include_product: bool = True,
    query_plan: list[dict[str, str]] | None = None,
) -> dict:
    """Enqueue Douyin collect job; poll until meat worker completes or timeout. Never fakes success.

    Runs wait/poll in a worker thread so /worker/claim HTTP stays responsive on the same process.
    """
    import anyio

    seed = (seed or "").strip()
    if not seed:
        return {"ok": False, "error": "seed 不能为空"}

    def _run() -> dict:
        return djq.collect_via_worker(
            seed,
            date_range_days=int(date_range_days or 30),
            include_video=bool(include_video),
            include_product=bool(include_product),
            query_plan=query_plan,
        )

    return await anyio.to_thread.run_sync(_run)


async def _read_json(request: Request) -> dict[str, Any]:
    try:
        data = await request.json()
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _unauthorized() -> JSONResponse:
    return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)


async def worker_heartbeat(request: Request) -> JSONResponse:
    if not djq.worker_token_ok(request.headers.get("authorization")):
        return _unauthorized()
    body = await _read_json(request)
    out = djq.record_heartbeat(
        worker_id=str(body.get("worker_id") or "肉机"),
        logged_in=body.get("logged_in") if "logged_in" in body else None,
        nickname=str(body.get("nickname") or "") or None,
        detail=body.get("detail") if isinstance(body.get("detail"), dict) else None,
    )
    return JSONResponse(out)


async def worker_claim(request: Request) -> JSONResponse:
    if not djq.worker_token_ok(request.headers.get("authorization")):
        return _unauthorized()
    body = await _read_json(request)
    job_types = body.get("job_types") if isinstance(body.get("job_types"), list) else None
    job = djq.claim_job(
        worker_id=str(body.get("worker_id") or "肉机"),
        job_types=[str(job_type) for job_type in job_types] if job_types is not None else None,
    )
    if not job:
        return JSONResponse({"ok": True, "job": None})
    return JSONResponse({"ok": True, "job": job})


async def worker_complete(request: Request) -> JSONResponse:
    if not djq.worker_token_ok(request.headers.get("authorization")):
        return _unauthorized()
    body = await _read_json(request)
    job_id = str(body.get("job_id") or "").strip()
    if not job_id:
        return JSONResponse({"ok": False, "error": "job_id required"}, status_code=400)
    out = djq.complete_job(
        job_id=job_id,
        worker_id=str(body.get("worker_id") or "肉机"),
        ok=bool(body.get("ok")),
        result=body.get("result") if isinstance(body.get("result"), dict) else None,
        error=str(body.get("error") or "") or None,
    )
    status = 200 if out.get("ok") else 400
    return JSONResponse(out, status_code=status)


async def worker_status(request: Request) -> JSONResponse:
    if not djq.worker_token_ok(request.headers.get("authorization")):
        return _unauthorized()
    return JSONResponse({"ok": True, **djq.auth_status_summary()})


def _attach_worker_routes(app) -> None:
    """Insert worker HTTP routes on the FastMCP Starlette app (same port as /mcp)."""
    extra = [
        Route("/worker/heartbeat", worker_heartbeat, methods=["POST"]),
        Route("/worker/claim", worker_claim, methods=["POST"]),
        Route("/worker/complete", worker_complete, methods=["POST"]),
        Route("/worker/status", worker_status, methods=["GET"]),
    ]
    # Prefer front of list so /worker/* wins over catch-alls.
    app.router.routes[0:0] = extra


def run_http(transport: str) -> None:
    host = os.environ.get("FASTMCP_HOST", "127.0.0.1")
    port = int(os.environ.get("FASTMCP_PORT", "18765"))
    if transport == "sse":
        mcp.run(transport="sse")  # type: ignore[arg-type]
        return
    # streamable-http with worker sidecar routes
    app = mcp.streamable_http_app()
    _attach_worker_routes(app)
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    transport = os.environ.get("FASTMCP_TRANSPORT", "streamable-http")
    if transport == "stdio":
        mcp.run(transport="stdio")  # type: ignore[arg-type]
    else:
        run_http(transport)
