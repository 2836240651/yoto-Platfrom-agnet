"""requires_mcp tools must never stub_fallback."""

from __future__ import annotations

from unittest.mock import patch

from agent.config.settings import settings
from agent.nodes.act import _run_registered_tool
from agent.tools.mcp_runtime import MCPInvokeResult


def test_requires_mcp_no_stub_when_runtime_disabled():
    prev_en = settings.mcp_runtime_enabled
    prev_fb = settings.mcp_allow_stub_fallback
    settings.mcp_runtime_enabled = False
    settings.mcp_allow_stub_fallback = True
    try:
        payload, quality, hard_fail = _run_registered_tool(
            "douyin_collect_hot_keywords",
            "douyin-keyword-research",
            {"seed": "渔具", "date_range_days": 30},
        )
        assert hard_fail is True
        assert payload.get("ok") is False
        assert (payload.get("_meta") or {}).get("source") == "mcp"
        assert "stub" not in str((payload.get("_meta") or {}).get("source"))
        assert quality <= 0.2
    finally:
        settings.mcp_runtime_enabled = prev_en
        settings.mcp_allow_stub_fallback = prev_fb


def test_requires_mcp_no_stub_on_mcp_failure():
    prev_en = settings.mcp_runtime_enabled
    prev_fb = settings.mcp_allow_stub_fallback
    settings.mcp_runtime_enabled = True
    settings.mcp_allow_stub_fallback = True
    try:
        with patch(
            "agent.nodes.act.mcp_runtime.invoke_logical",
            return_value=MCPInvokeResult(ok=False, error="network down"),
        ):
            payload, _quality, hard_fail = _run_registered_tool(
                "douyin_collect_hot_keywords",
                "douyin-keyword-research",
                {"seed": "渔具"},
            )
        assert hard_fail is True
        assert payload.get("ok") is False
        assert (payload.get("_meta") or {}).get("source") == "mcp"
        assert (payload.get("_meta") or {}).get("mcp_error") == "network down"
    finally:
        settings.mcp_runtime_enabled = prev_en
        settings.mcp_allow_stub_fallback = prev_fb
