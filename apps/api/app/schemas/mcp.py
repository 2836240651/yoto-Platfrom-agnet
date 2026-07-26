"""MCP management API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MCPServer(BaseModel):
    id: str
    transport: str = "stdio"
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class MCPServerCreateRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    transport: str = "stdio"
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class MCPServerHealth(BaseModel):
    id: str
    ok: bool
    tool_count: int = 0
    latency_ms: int = 0
    error: str | None = None
    tools_sample: list[str] = Field(default_factory=list)


class MCPRuntimeStatus(BaseModel):
    ok: bool
    error: str | None = None
    tool_count: int = 0
    config_path: str


class ToolAlias(BaseModel):
    logical_name: str
    mcp_tool: str | None = None
    server: str | None = None
    description: str = ""
    arg_map: dict[str, str] = Field(default_factory=dict)
    defaults: dict[str, Any] = Field(default_factory=dict)
    use_mcp: bool = True
    allow_in_skills: list[str] = Field(default_factory=list)


class MCPOverviewResponse(BaseModel):
    runtime: MCPRuntimeStatus
    servers: list[MCPServer]
    server_health: list[MCPServerHealth]
    aliases: list[ToolAlias]
    tools: list[str]


class MCPReloadResponse(BaseModel):
    ok: bool
    runtime: MCPRuntimeStatus
    message: str
