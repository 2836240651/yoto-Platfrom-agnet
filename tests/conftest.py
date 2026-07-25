"""Pytest fixtures — deterministic graph without live MCP / Playwright."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_API = _ROOT / "apps" / "api"
_SRC = _ROOT / "src"
for p in (_SRC, _API):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


def _fixture_collect(seed: str, date_range_days: int = 30) -> dict[str, Any]:
    """Deterministic MCP-shaped collect payload (not production stub path)."""
    words = [
        f"{seed}装备",
        f"专业{seed}",
        f"{seed}推荐",
        f"入门{seed}",
        f"碳素{seed}",
        f"{seed}套装",
        f"轻量化{seed}",
        f"远投{seed}",
    ]
    video_hot = [{"word": w, "hot_level": 100_000 - i * 1000} for i, w in enumerate(words[:4])]
    video_potential = [
        {"word": w, "hot_level": 40_000 - i * 500} for i, w in enumerate(words[4:6])
    ]
    product_hot = [{"word": w, "hot_level": 80_000 - i * 800} for i, w in enumerate(words[6:7])]
    product_potential = [
        {"word": w, "hot_level": 30_000 - i * 400} for i, w in enumerate(words[7:8])
    ]
    keywords = [
        {"word": x["word"], "hot_level": x["hot_level"], "side": "video", "bucket": "hot"}
        for x in video_hot
    ] + [
        {
            "word": x["word"],
            "hot_level": x["hot_level"],
            "side": "video",
            "bucket": "potential",
        }
        for x in video_potential
    ] + [
        {"word": x["word"], "hot_level": x["hot_level"], "side": "product", "bucket": "hot"}
        for x in product_hot
    ] + [
        {
            "word": x["word"],
            "hot_level": x["hot_level"],
            "side": "product",
            "bucket": "potential",
        }
        for x in product_potential
    ]
    return {
        "ok": True,
        "seed": seed,
        "seed_mode": "direct",
        "bridges_used": [],
        "date_range_days": date_range_days,
        "keywords": keywords,
        "count": len(keywords),
        "video_hot": video_hot,
        "video_potential": video_potential,
        "product_hot": product_hot,
        "product_potential": product_potential,
        "data_source": {
            "source": "mcp",
            "tool": "douyin_collect_hot_keywords",
            "provider": "test_fixture",
        },
    }


@pytest.fixture(autouse=True)
def mock_mcp_collect_in_tests():
    """Douyin collect is requires_mcp — never stub_fallback. Mock MCP invoke for tests."""
    from agent.config.settings import settings
    from agent.tools.mcp_runtime import MCPInvokeResult, mcp_runtime

    prev_enabled = settings.mcp_runtime_enabled
    settings.mcp_runtime_enabled = True

    def fake_invoke(logical_name: str, arguments: dict[str, Any]) -> MCPInvokeResult:
        args = arguments or {}
        if logical_name == "douyin_collect_hot_keywords":
            seed = str(args.get("seed") or "渔具")
            days = int(args.get("date_range_days") or 30)
            data = _fixture_collect(seed, days)
            return MCPInvokeResult(
                ok=True,
                data=data,
                resolved_tool="douyin_collect_hot_keywords",
                logical_name=logical_name,
            )
        if logical_name == "douyin_chanmama_auth_status":
            return MCPInvokeResult(
                ok=True,
                data={"ok": True, "logged_in": True, "nickname": "test", "worker_id": "肉机"},
                resolved_tool=logical_name,
                logical_name=logical_name,
            )
        return MCPInvokeResult(
            ok=False,
            error=f"unmocked MCP tool in tests: {logical_name}",
            logical_name=logical_name,
        )

    with patch.object(mcp_runtime, "invoke_logical", side_effect=fake_invoke):
        yield

    settings.mcp_runtime_enabled = prev_enabled
