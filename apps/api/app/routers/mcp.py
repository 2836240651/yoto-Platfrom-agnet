"""MCP server management API."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query, Response

from app.schemas.mcp import (
    MCPOverviewResponse,
    MCPReloadResponse,
    MCPServer,
    MCPServerCreateRequest,
)
from app.services import mcp_service

router = APIRouter(prefix="/mcp", tags=["mcp"])


def _enforce_write(token: str | None, response: Response) -> None:
    try:
        warning = mcp_service.assert_write_allowed(token)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if warning:
        response.headers["X-MCP-Write-Warning"] = warning


@router.get("", response_model=MCPOverviewResponse)
def mcp_overview(health: bool = Query(False, description="Run per-server health checks")) -> MCPOverviewResponse:
    """Runtime status, servers, optional health, aliases, and discovered tools."""
    return mcp_service.get_overview(health=health)


@router.post("/reload", response_model=MCPReloadResponse)
def mcp_reload(
    response: Response,
    x_mcp_write_token: str | None = Header(default=None, alias="X-MCP-Write-Token"),
) -> MCPReloadResponse:
    _enforce_write(x_mcp_write_token, response)
    return mcp_service.reload_runtime()


@router.post("/servers", response_model=MCPServer, status_code=201)
def create_mcp_server(
    body: MCPServerCreateRequest,
    response: Response,
    x_mcp_write_token: str | None = Header(default=None, alias="X-MCP-Write-Token"),
) -> MCPServer:
    _enforce_write(x_mcp_write_token, response)
    return mcp_service.create_server(body)


@router.delete("/servers/{server_id}")
def delete_mcp_server(
    server_id: str,
    response: Response,
    x_mcp_write_token: str | None = Header(default=None, alias="X-MCP-Write-Token"),
) -> dict:
    _enforce_write(x_mcp_write_token, response)
    if not mcp_service.delete_server(server_id):
        raise HTTPException(status_code=404, detail="MCP server not found")
    return {"ok": True, "deleted": server_id}
