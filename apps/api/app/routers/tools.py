"""Read-only tools status API (business-safe)."""

from __future__ import annotations

from fastapi import APIRouter

from app.services.tools_status import ToolsStatusResponse, get_tools_status

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("/status", response_model=ToolsStatusResponse)
def tools_status() -> ToolsStatusResponse:
    """MCP + Commander Agent online probes. No secrets; no write ops."""
    return get_tools_status()
