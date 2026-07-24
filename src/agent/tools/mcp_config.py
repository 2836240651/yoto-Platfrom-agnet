"""Read/write MCP server configuration."""

from __future__ import annotations

import json
from typing import Any

from agent.config.settings import settings


def _read_raw() -> dict[str, Any]:
    path = settings.mcp_config_path
    if not path.exists():
        return {"mcpServers": {}}
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if "mcpServers" not in data:
        data = {"mcpServers": data}
    return data


def _write_raw(data: dict[str, Any]) -> None:
    path = settings.mcp_config_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _public_server(server_id: str, cfg: dict[str, Any]) -> dict[str, Any]:
    transport = cfg.get("transport", "stdio")
    out: dict[str, Any] = {
        "id": server_id,
        "transport": transport,
        "command": cfg.get("command"),
        "args": list(cfg.get("args") or []),
        "env": dict(cfg.get("env") or {}),
    }
    if cfg.get("url"):
        out["url"] = cfg["url"]
    if cfg.get("headers"):
        out["headers"] = dict(cfg["headers"])
    return out


def list_servers() -> list[dict[str, Any]]:
    servers = _read_raw().get("mcpServers") or {}
    out: list[dict[str, Any]] = []
    for server_id, cfg in servers.items():
        if not isinstance(cfg, dict):
            continue
        out.append(_public_server(server_id, cfg))
    return sorted(out, key=lambda x: x["id"])


def get_server(server_id: str) -> dict[str, Any] | None:
    cfg = (_read_raw().get("mcpServers") or {}).get(server_id)
    if not isinstance(cfg, dict):
        return None
    return _public_server(server_id, cfg)


def upsert_server(server_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = _read_raw()
    servers = data.setdefault("mcpServers", {})
    transport = payload.get("transport", "stdio")
    entry: dict[str, Any] = {"transport": transport}
    if transport in ("sse", "streamable_http", "streamable-http", "http"):
        entry["url"] = payload["url"]
        if payload.get("headers"):
            entry["headers"] = dict(payload["headers"])
    else:
        entry["command"] = payload["command"]
        entry["args"] = list(payload.get("args") or [])
        entry["env"] = dict(payload.get("env") or {})
    servers[server_id] = entry
    _write_raw(data)
    return get_server(server_id) or {"id": server_id}


def delete_server(server_id: str) -> bool:
    data = _read_raw()
    servers = data.get("mcpServers") or {}
    if server_id not in servers:
        return False
    del servers[server_id]
    _write_raw(data)
    return True
