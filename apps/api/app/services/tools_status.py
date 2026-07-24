"""Read-only tool status for business + dev views (no MCP admin)."""

from __future__ import annotations

import httpx
from pydantic import BaseModel, Field

from agent.config.settings import settings
from agent.tools.mcp_runtime import mcp_runtime


class ToolProbe(BaseModel):
    id: str
    label: str
    ok: bool
    detail: str = ""
    online: bool | None = None


class ToolsStatusResponse(BaseModel):
    ok: bool
    probes: list[ToolProbe] = Field(default_factory=list)
    note: str = "密钥由服务端配置，用户无需填写 API Key"


def _commander_base() -> str:
    return (settings.commander_api_base or "https://www.yoto.work/api/v1").rstrip("/")


def _commander_token() -> str:
    return (settings.commander_access_token or "").strip()


def _default_agent() -> str:
    return (settings.commander_default_agent_id or "肉机").strip() or "肉机"


def _probe_mcp() -> ToolProbe:
    if not settings.mcp_runtime_enabled:
        return ToolProbe(
            id="mcp_runtime",
            label="MCP 运行时",
            ok=False,
            detail="MCP_RUNTIME_ENABLED=false",
        )
    st = mcp_runtime.status()
    ok = bool(st.get("ok"))
    err = st.get("error") or ""
    count = int(st.get("tool_count") or 0)
    tools = mcp_runtime.available_tools() if ok else []
    has_temu = any("temu" in t for t in tools)
    if ok and has_temu:
        detail = f"已加载 {count} 个工具（含 Temu）"
    elif ok:
        detail = f"已加载 {count} 个工具"
    else:
        detail = err or "不可用"
    return ToolProbe(id="mcp_runtime", label="MCP 网关 / 工具", ok=ok, detail=detail)


def _probe_meat_machine() -> ToolProbe:
    """Commander agent online probe via HTTP; reads COMMANDER_* from settings only."""
    token = _commander_token()
    agent = _default_agent()
    if not token:
        return ToolProbe(
            id="commander_agent",
            label=f"上架 Agent（{agent}）",
            ok=False,
            online=False,
            detail="服务端未配置 COMMANDER_ACCESS_TOKEN",
        )
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                f"{_commander_base()}/agent/list",
                headers={"Authorization": f"Bearer {token}"},
                json={},
            )
            resp.raise_for_status()
            payload = resp.json()
        if isinstance(payload, dict) and "code" in payload:
            code = payload.get("code")
            if code not in (0, "0", None):
                msg = payload.get("msg") or payload.get("message") or str(payload)
                return ToolProbe(
                    id="commander_agent",
                    label=f"上架 Agent（{agent}）",
                    ok=False,
                    online=False,
                    detail=f"Commander 业务失败 code={code}: {msg}",
                )
            data = payload.get("data")
        else:
            data = payload
        items = data if isinstance(data, list) else list((data or {}).get("list") or [])
        match = None
        for a in items:
            if not isinstance(a, dict):
                continue
            name = str(a.get("name") or a.get("agentId") or a.get("id") or "")
            if name == agent:
                match = a
                break
        if match is None:
            return ToolProbe(
                id="commander_agent",
                label=f"上架 Agent（{agent}）",
                ok=False,
                online=False,
                detail="未在 Agent 列表中找到",
            )
        st = match.get("status")
        online = st is True or str(st).lower() in ("true", "1", "online", "on")
        return ToolProbe(
            id="commander_agent",
            label=f"上架 Agent（{agent}）",
            ok=online,
            online=online,
            detail="在线" if online else "离线",
        )
    except Exception as exc:  # noqa: BLE001
        return ToolProbe(
            id="commander_agent",
            label=f"上架 Agent（{agent}）",
            ok=False,
            online=False,
            detail=f"探测失败：{exc}",
        )


def get_tools_status() -> ToolsStatusResponse:
    probes = [_probe_mcp(), _probe_meat_machine()]
    return ToolsStatusResponse(ok=all(p.ok for p in probes), probes=probes)
