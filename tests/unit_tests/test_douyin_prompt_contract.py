"""Prompt-contract tests for the Douyin keyword research flow."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_douyin_agent_tool_and_skill_require_diagnostic_grounding():
    analyzer = (ROOT / "src" / "agent" / "tools" / "douyin_analyze.py").read_text(encoding="utf-8")
    skill = (ROOT / "skills" / "douyin-keyword-research" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    registry = json.loads((ROOT / "config" / "tool_registry.json").read_text(encoding="utf-8"))
    collect_description = registry["aliases"]["douyin_collect_hot_keywords"]["description"]

    assert "不得将 no_data、upstream_error 或 parse_error 转成关键词建议" in analyzer
    assert "queried_term、query_level、query_source" in analyzer
    assert "55006" in skill
    assert "有头浏览器" in skill
    assert "先读取 status 与 diagnostics" in collect_description
