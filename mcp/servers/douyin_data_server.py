# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2.0", "playwright>=1.40"]
# ///

"""Douyin / Chanmama data MCP.

Transports:
  stdio (default, local dev)
  streamable-http / sse — meat-machine remote (FASTMCP_*)
"""

from __future__ import annotations

import concurrent.futures
import os
import sys
from pathlib import Path
from typing import Any, Callable

_SERVERS_DIR = Path(__file__).resolve().parent
if str(_SERVERS_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVERS_DIR))

from douyin_chanmama_client import (  # noqa: E402
    check_login,
    collect_hot_keywords,
)
from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP(
    "douyin_data",
    host=os.environ.get("FASTMCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("FASTMCP_PORT", "18766")),
)


def _run_sync(fn: Callable[[], dict], timeout_s: float = 240) -> dict[str, Any]:
    """Playwright Sync API cannot run inside the MCP asyncio loop."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(fn).result(timeout=timeout_s)


@mcp.tool()
def douyin_chanmama_auth_status() -> dict:
    """Check whether Chanmama personal-edition session is logged in."""
    headed = (os.environ.get("CHANMAMA_HEADED") or "").strip().lower() in {"1", "true", "yes"}
    return _run_sync(lambda: check_login(headed=headed), timeout_s=60)


@mcp.tool()
def douyin_collect_hot_keywords(
    seed: str,
    date_range_days: int = 30,
    include_video: bool = True,
    include_product: bool = True,
) -> dict:
    """Collect Douyin video/product hot & potential keywords via Chanmama personal cookie session."""
    headed = (os.environ.get("CHANMAMA_HEADED") or "").strip().lower() in {"1", "true", "yes"}

    def _job() -> dict:
        return collect_hot_keywords(
            seed,
            date_range_days=date_range_days,
            include_video=include_video,
            include_product=include_product,
            headed=headed,
        )

    try:
        return _run_sync(_job, timeout_s=240)
    except concurrent.futures.TimeoutError:
        return {"ok": False, "error": "蝉妈妈采集超时（240s）", "seed": seed}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"蝉妈妈采集异常：{exc}", "seed": seed}


if __name__ == "__main__":
    transport = (os.environ.get("FASTMCP_TRANSPORT") or "stdio").strip().lower()
    if transport in {"streamable-http", "streamable_http", "http"}:
        mcp.run(transport="streamable-http")
    elif transport == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run()
