# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2.0", "httpx>=0.27"]
# ///

"""Platform MCP gateway — long-running SSE / streamable-http.

Env:
  FASTMCP_HOST (default 127.0.0.1)
  FASTMCP_PORT (default 18765)
  FASTMCP_TRANSPORT (streamable-http | sse | stdio)
  COMMANDER_API_BASE / COMMANDER_ACCESS_TOKEN / COMMANDER_DEFAULT_AGENT_ID

Dev:
  python mcp/servers/platform_mcp_gateway.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow importing sibling modules when launched as a script.
_SERVERS_DIR = Path(__file__).resolve().parent
if str(_SERVERS_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVERS_DIR))

from commander_temu_client import (  # noqa: E402
    commander_product_issue_status,
    commander_product_issue_submit,
)
from mcp.server.fastmcp import FastMCP  # noqa: E402

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


if __name__ == "__main__":
    transport = os.environ.get("FASTMCP_TRANSPORT", "streamable-http")
    mcp.run(transport=transport)  # type: ignore[arg-type]
