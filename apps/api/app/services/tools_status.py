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
    note: str = "抖音词分析依赖 MCP 网关和抖音肉机；跨境上架 Agent 为独立的 Temu 服务。密钥由服务端配置。"


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
    """Probe the Temu Agent WebSocket registration without user JWT."""
    agent = _default_agent()
    label = "跨境上架 Agent（Temu）"
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(f"{_commander_base()}/agent/status", params={"id": agent})
            resp.raise_for_status()
            payload = resp.json()
        if not isinstance(payload, dict) or payload.get("code") not in (0, "0", None):
            msg = payload.get("msg") if isinstance(payload, dict) else "状态响应非 JSON 对象"
            return ToolProbe(
                id="commander_agent",
                label=label,
                ok=False,
                online=False,
                detail=f"Temu Agent 状态查询失败：{msg or 'unknown error'}",
            )
        data = payload.get("data") or {}
        online = bool(data.get("online")) if isinstance(data, dict) else False
        name = str(data.get("name") or "").strip() if isinstance(data, dict) else ""
        return ToolProbe(
            id="commander_agent",
            label=label,
            ok=online,
            online=online,
            detail=f"在线{name and f' · {name}' or ''}" if online else "离线（未建立 Agent WebSocket 连接）",
        )
    except Exception as exc:  # noqa: BLE001
        return ToolProbe(
            id="commander_agent",
            label=label,
            ok=False,
            online=False,
            detail=f"跨境上架 Agent 状态探测失败：{exc}",
        )


def _douyin_worker_base() -> str:
    return (settings.douyin_worker_url or "https://www.yoto.work/platform-mcp").rstrip("/")


def _douyin_worker_token() -> str:
    return (settings.douyin_worker_token or "").strip()


def _probe_douyin_meat_worker() -> ToolProbe:
    """Douyin Playwright hand via platform_mcp /worker/status (not Commander WS)."""
    token = _douyin_worker_token()
    base = _douyin_worker_base()
    if not token:
        return ToolProbe(
            id="douyin_meat_worker",
            label="抖音肉机（蝉妈妈）",
            ok=False,
            online=False,
            detail="服务端未配置 DOUYIN_WORKER_TOKEN",
        )
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(
                f"{base}/worker/status",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
            resp.raise_for_status()
            payload = resp.json()
        if not isinstance(payload, dict):
            return ToolProbe(
                id="douyin_meat_worker",
                label="抖音肉机（蝉妈妈）",
                ok=False,
                online=False,
                detail="状态响应非 JSON 对象",
            )
        online = bool(payload.get("ok"))
        logged_in = bool(payload.get("logged_in"))
        nick = str(payload.get("nickname") or "").strip()
        err = str(payload.get("error") or payload.get("message") or "").strip()
        if online and logged_in:
            detail = f"在线已登录{f' · {nick}' if nick else ''}"
        elif online and not logged_in:
            detail = err or "在线但未登录蝉妈妈（need_login）"
            online = False
        else:
            detail = err or "离线（need_worker）"
        return ToolProbe(
            id="douyin_meat_worker",
            label="抖音肉机（蝉妈妈）",
            ok=online and logged_in,
            online=online and logged_in,
            detail=detail,
        )
    except Exception as exc:  # noqa: BLE001
        return ToolProbe(
            id="douyin_meat_worker",
            label="抖音肉机（蝉妈妈）",
            ok=False,
            online=False,
            detail=f"探测失败：{exc}",
        )


def get_tools_status() -> ToolsStatusResponse:
    probes = [_probe_mcp(), _probe_meat_machine(), _probe_douyin_meat_worker()]
    # Douyin ops gate: MCP + 蝉妈妈手. Temu Agent is shown but advisory (separate token/WS).
    required_ok = all(
        p.ok for p in probes if p.id in ("mcp_runtime", "douyin_meat_worker")
    )
    return ToolsStatusResponse(ok=required_ok, probes=probes)
