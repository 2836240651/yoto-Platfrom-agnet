"""Runtime MCP tool loader/invoker."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.config.settings import PROJECT_ROOT, settings
from agent.tools import mcp_config
from agent.tools.tool_registry import tool_registry


@dataclass
class MCPInvokeResult:
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    source: str = "mcp"
    tool_name: str | None = None
    logical_name: str | None = None
    resolved_tool: str | None = None


class MCPRuntime:
    """Lazy MCP client/registry wrapper."""

    def __init__(self) -> None:
        self._client: Any = None
        self._tools_by_name: dict[str, Any] = {}
        self._init_error: str | None = None

    def reset(self) -> None:
        self._client = None
        self._tools_by_name = {}
        self._init_error = None

    def reload(self) -> None:
        self.reset()
        tool_registry.reload()

    def _load_servers_config(self) -> dict[str, Any]:
        with settings.mcp_config_path.open(encoding="utf-8") as f:
            config_obj = json.load(f)
        servers = config_obj.get("mcpServers", config_obj)
        if not isinstance(servers, dict):
            raise ValueError("mcp config must contain object field 'mcpServers'")
        return _normalize_server_paths(servers)

    def _ensure_loaded(self) -> None:
        if self._tools_by_name or self._init_error:
            return
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except Exception as exc:  # noqa: BLE001
            self._init_error = f"langchain_mcp_adapters import failed: {exc}"
            return

        if not settings.mcp_config_path.exists():
            self._init_error = f"mcp config not found: {settings.mcp_config_path}"
            return

        # Load per-server so one dead remote gateway does not kill stdio tools.
        try:
            servers = self._load_servers_config()
        except Exception as exc:  # noqa: BLE001
            self._init_error = f"failed to read mcp config: {exc}"
            return

        tools_by_name: dict[str, Any] = {}
        errors: list[str] = []
        for server_id, cfg in servers.items():
            try:
                client = MultiServerMCPClient({server_id: cfg})
                tools = self._run_async(client.get_tools())
                for tool in tools:
                    tools_by_name[tool.name] = tool
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{server_id}: {exc}")

        self._tools_by_name = tools_by_name
        self._client = None
        if not tools_by_name:
            self._init_error = (
                "failed to load mcp tools: " + ("; ".join(errors) if errors else "no servers")
            )
        else:
            self._init_error = None

    @staticmethod
    def _run_async(awaitable: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(awaitable)
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(awaitable)
        finally:
            new_loop.close()

    def available_tools(self) -> list[str]:
        self._ensure_loaded()
        return sorted(self._tools_by_name.keys())

    def status(self) -> dict[str, Any]:
        self._ensure_loaded()
        return {
            "ok": bool(self._tools_by_name) and self._init_error is None,
            "error": self._init_error,
            "tool_count": len(self._tools_by_name),
            "config_path": str(settings.mcp_config_path),
            "tools": sorted(self._tools_by_name.keys()),
        }

    def health_check_servers(self) -> list[dict[str, Any]]:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        results: list[dict[str, Any]] = []
        servers = mcp_config.list_servers()
        all_servers = _normalize_server_paths({s["id"]: self._server_cfg(s) for s in servers})
        for server in servers:
            server_id = server["id"]
            started = __import__("time").time()
            try:
                client = MultiServerMCPClient({server_id: all_servers[server_id]})
                tools = self._run_async(client.get_tools())
                elapsed_ms = int((__import__("time").time() - started) * 1000)
                results.append(
                    {
                        "id": server_id,
                        "ok": True,
                        "tool_count": len(tools),
                        "latency_ms": elapsed_ms,
                        "tools_sample": sorted(t.name for t in tools)[:8],
                    }
                )
            except Exception as exc:  # noqa: BLE001
                elapsed_ms = int((__import__("time").time() - started) * 1000)
                results.append(
                    {
                        "id": server_id,
                        "ok": False,
                        "tool_count": 0,
                        "latency_ms": elapsed_ms,
                        "error": str(exc),
                    }
                )
        return results

    @staticmethod
    def _server_cfg(server: dict[str, Any]) -> dict[str, Any]:
        transport = server.get("transport", "stdio")
        cfg: dict[str, Any] = {"transport": transport}
        if transport in ("sse", "streamable_http", "streamable-http", "http"):
            if server.get("url"):
                cfg["url"] = server["url"]
            if server.get("headers"):
                cfg["headers"] = dict(server["headers"])
            return cfg
        cfg["command"] = server.get("command")
        cfg["args"] = list(server.get("args") or [])
        cfg["env"] = dict(server.get("env") or {})
        return cfg

    def invoke(self, tool_name: str, arguments: dict[str, Any]) -> MCPInvokeResult:
        self._ensure_loaded()
        if self._init_error:
            return MCPInvokeResult(ok=False, error=self._init_error, tool_name=tool_name)
        tool = self._tools_by_name.get(tool_name)
        if not tool:
            return MCPInvokeResult(
                ok=False,
                error=f"tool not found: {tool_name}",
                tool_name=tool_name,
                data={"available_tools": self.available_tools()[:50]},
            )
        try:
            if hasattr(tool, "invoke"):
                try:
                    out = tool.invoke(arguments)
                except NotImplementedError:
                    if hasattr(tool, "ainvoke"):
                        out = self._run_async(tool.ainvoke(arguments))
                    else:
                        raise
            elif hasattr(tool, "ainvoke"):
                out = self._run_async(tool.ainvoke(arguments))
            else:
                raise RuntimeError("tool has neither invoke nor ainvoke")
            normalized = _normalize_mcp_output(out)
            return MCPInvokeResult(ok=True, data=normalized, tool_name=tool_name)
        except Exception as exc:  # noqa: BLE001
            return MCPInvokeResult(
                ok=False,
                error=f"invoke failed for {tool_name}: {exc}",
                tool_name=tool_name,
            )

    def invoke_logical(self, logical_name: str, arguments: dict[str, Any]) -> MCPInvokeResult:
        resolved = tool_registry.resolve(logical_name)
        if not resolved.use_mcp or not resolved.mcp_tool:
            return MCPInvokeResult(
                ok=False,
                error=f"logical tool has no MCP mapping: {logical_name}",
                logical_name=logical_name,
            )
        mapped_args = tool_registry.map_arguments(resolved, arguments)
        result = self.invoke(resolved.mcp_tool, mapped_args)
        result.logical_name = logical_name
        result.resolved_tool = resolved.mcp_tool
        return result


mcp_runtime = MCPRuntime()


def _normalize_server_paths(servers: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for server_id, cfg in servers.items():
        if not isinstance(cfg, dict):
            continue
        transport = str(cfg.get("transport") or "stdio")
        if transport in ("sse", "streamable_http", "streamable-http", "http"):
            normalized: dict[str, Any] = {
                "transport": "streamable_http"
                if transport in ("streamable-http", "http")
                else transport,
                "url": cfg["url"],
            }
            if cfg.get("headers"):
                normalized["headers"] = dict(cfg["headers"])
            out[server_id] = normalized
            continue

        normalized = {
            "transport": "stdio",
            "command": cfg.get("command"),
            "env": dict(cfg.get("env") or {}),
        }
        args: list[str] = []
        for arg in cfg.get("args") or []:
            p = Path(str(arg))
            if not p.is_absolute():
                candidate = PROJECT_ROOT / p
                args.append(str(candidate if candidate.exists() else p))
            else:
                args.append(str(p))
        normalized["args"] = args
        out[server_id] = normalized
    return out


def _normalize_mcp_output(out: Any) -> dict[str, Any]:
    if isinstance(out, dict):
        # langchain-mcp may wrap FastMCP errors as {"result":[Content...]}
        if set(out.keys()) == {"result"}:
            nested = _normalize_mcp_output(out["result"])
            if nested.get("ok") is False or "error" in nested:
                return nested
            if "ok" in nested or "keywords" in nested or "count" in nested:
                return nested
        return out
    if isinstance(out, list):
        for item in out:
            text = None
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                text = item["text"].strip()
            elif hasattr(item, "text") and isinstance(getattr(item, "text"), str):
                text = str(getattr(item, "text")).strip()
            if not text:
                continue
            if text.startswith("{") or text.startswith("["):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        return parsed
                    return {"result": parsed}
                except json.JSONDecodeError:
                    continue
            if text.lower().startswith("error") or "Playwright" in text:
                return {"ok": False, "error": text}
        return {"result": out}
    if isinstance(out, str):
        text = out.strip()
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        if text.lower().startswith("error"):
            return {"ok": False, "error": text}
    return {"result": out}
