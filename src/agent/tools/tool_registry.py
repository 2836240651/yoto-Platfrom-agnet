"""Logical tool name -> MCP tool mapping."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from agent.config.settings import settings


@dataclass
class ResolvedTool:
    logical_name: str
    mcp_tool: str | None
    server: str | None
    description: str
    arg_map: dict[str, str]
    defaults: dict[str, Any]
    use_mcp: bool
    allow_in_skills: list[str] = field(default_factory=list)
    quality_rules: dict[str, Any] = field(default_factory=dict)
    requires_mcp: bool = False
    registered: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._path = settings.tool_registry_path
        self._cache: dict[str, Any] | None = None

    def reload(self) -> None:
        self._cache = None

    def _load(self) -> dict[str, Any]:
        if self._cache is not None:
            return self._cache
        if not self._path.exists():
            self._cache = {"version": 1, "aliases": {}}
            return self._cache
        with self._path.open(encoding="utf-8") as f:
            self._cache = json.load(f)
        return self._cache

    def list_aliases(self) -> list[dict[str, Any]]:
        data = self._load()
        out: list[dict[str, Any]] = []
        for name, meta in (data.get("aliases") or {}).items():
            if not isinstance(meta, dict):
                continue
            resolved = self.resolve(name)
            out.append(
                {
                    "logical_name": name,
                    "mcp_tool": resolved.mcp_tool,
                    "server": resolved.server,
                    "description": resolved.description,
                    "arg_map": resolved.arg_map,
                    "defaults": resolved.defaults,
                    "use_mcp": resolved.use_mcp,
                    "allow_in_skills": resolved.allow_in_skills,
                }
            )
        return sorted(out, key=lambda x: x["logical_name"])

    def resolve(self, logical_name: str) -> ResolvedTool:
        data = self._load()
        aliases = data.get("aliases") or {}
        meta = aliases.get(logical_name)
        if meta is None:
            # Unregistered tools are denied by allow_in_skills check (empty list).
            return ResolvedTool(
                logical_name=logical_name,
                mcp_tool=logical_name,
                server=None,
                description="",
                arg_map={},
                defaults={},
                use_mcp=True,
                allow_in_skills=[],
                registered=False,
            )
        if not isinstance(meta, dict):
            meta = {}
        allow = list(meta.get("allow_in_skills") or [])
        quality_rules = dict(meta.get("quality_rules") or {})
        requires_mcp = bool(meta.get("requires_mcp", False))
        if "mcp_tool" in meta and meta.get("mcp_tool") is None:
            return ResolvedTool(
                logical_name=logical_name,
                mcp_tool=None,
                server=meta.get("server"),
                description=str(meta.get("description") or ""),
                arg_map=dict(meta.get("arg_map") or {}),
                defaults=dict(meta.get("defaults") or {}),
                use_mcp=False,
                allow_in_skills=allow,
                quality_rules=quality_rules,
                requires_mcp=requires_mcp,
                registered=True,
            )
        mcp_tool = meta.get("mcp_tool") or logical_name
        return ResolvedTool(
            logical_name=logical_name,
            mcp_tool=mcp_tool,
            server=meta.get("server"),
            description=str(meta.get("description") or ""),
            arg_map=dict(meta.get("arg_map") or {}),
            defaults=dict(meta.get("defaults") or {}),
            use_mcp=True,
            allow_in_skills=allow,
            quality_rules=quality_rules,
            requires_mcp=requires_mcp,
            registered=True,
        )

    def assert_allowed(self, resolved: ResolvedTool, skill: str) -> None:
        if not resolved.registered:
            raise PermissionError(f"tool not registered: {resolved.logical_name}")
        if skill not in resolved.allow_in_skills:
            raise PermissionError(
                f"tool {resolved.logical_name} not allowed in skill {skill}"
            )

    def map_arguments(self, resolved: ResolvedTool, args: dict[str, Any]) -> dict[str, Any]:
        payload = dict(resolved.defaults)
        for key, value in args.items():
            target = resolved.arg_map.get(key, key)
            payload[target] = value
        return payload

    def quality_for(self, resolved: ResolvedTool, result: dict[str, Any]) -> float:
        rules = resolved.quality_rules or {}
        if "ok" in result:
            return float(rules.get("ok_true", 0.9) if result.get("ok") else rules.get("ok_false", 0.2))
        if "count" in result and isinstance(result.get("count"), (int, float)):
            return min(1.0, float(result["count"]) / 5.0)
        return 0.5


tool_registry = ToolRegistry()
