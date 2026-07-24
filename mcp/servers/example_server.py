# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2.0,<2"]
# ///

"""Example MCP server — replace with real domain tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example_tools")


@mcp.tool()
def ping(message: str = "hello") -> dict:
    """Health check tool."""
    return {"ok": True, "echo": message}


if __name__ == "__main__":
    mcp.run()
