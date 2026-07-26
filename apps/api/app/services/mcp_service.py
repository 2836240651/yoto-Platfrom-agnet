"""MCP management service."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from agent.config.settings import settings
from agent.tools import mcp_config
from agent.tools.mcp_runtime import mcp_runtime
from agent.tools.tool_registry import tool_registry
from app.schemas.mcp import (
    MCPOverviewResponse,
    MCPReloadResponse,
    MCPRuntimeStatus,
    MCPServer,
    MCPServerCreateRequest,
    MCPServerHealth,
    ToolAlias,
)


def _runtime_status() -> MCPRuntimeStatus:
    runtime_raw = mcp_runtime.status()
    return MCPRuntimeStatus(
        ok=bool(runtime_raw.get("ok")),
        error=runtime_raw.get("error"),
        tool_count=int(runtime_raw.get("tool_count") or 0),
        config_path=str(runtime_raw.get("config_path") or ""),
    )


def get_overview(*, health: bool = False) -> MCPOverviewResponse:
    runtime = _runtime_status()
    servers = [MCPServer(**s) for s in mcp_config.list_servers()]
    server_health: list[MCPServerHealth] = []
    if health:
        server_health = [MCPServerHealth(**h) for h in mcp_runtime.health_check_servers()]
    aliases = [ToolAlias(**a) for a in tool_registry.list_aliases()]
    tools = mcp_runtime.available_tools() if settings.mcp_runtime_enabled else []
    return MCPOverviewResponse(
        runtime=runtime,
        servers=servers,
        server_health=server_health,
        aliases=aliases,
        tools=tools,
    )


def reload_runtime() -> MCPReloadResponse:
    mcp_runtime.reload()
    runtime = _runtime_status()
    return MCPReloadResponse(
        ok=runtime.ok,
        runtime=runtime,
        message="MCP runtime reloaded" if runtime.ok else (runtime.error or "reload failed"),
    )


def create_server(body: MCPServerCreateRequest) -> MCPServer:
    saved = mcp_config.upsert_server(
        body.id,
        {
            "transport": body.transport,
            "command": body.command,
            "args": body.args,
            "env": body.env,
        },
    )
    mcp_runtime.reload()
    return MCPServer(**saved)


def delete_server(server_id: str) -> bool:
    deleted = mcp_config.delete_server(server_id)
    if deleted:
        mcp_runtime.reload()
    return deleted


def assert_write_allowed(token: str | None) -> str | None:
    """Return optional warning header value; raise PermissionError if denied."""
    configured = (settings.mcp_write_token or "").strip()
    if configured:
        expiry = (os.environ.get("MCP_WRITE_TOKEN_EXPIRES_AT") or "").strip()
        if expiry:
            try:
                expires_at = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
            except ValueError as exc:
                raise PermissionError("MCP write token expiry is invalid") from exc
            if datetime.now(timezone.utc) >= expires_at.astimezone(timezone.utc):
                raise PermissionError("MCP write token expired")
        if (token or "").strip() != configured:
            raise PermissionError("invalid or missing X-MCP-Write-Token")
        return None
    if settings.agent_env == "dev":
        return "unprotected-dev"
    raise PermissionError("MCP write disabled (set MCP_WRITE_TOKEN or AGENT_ENV=dev)")
