"""Tests for tool registry."""

from agent.tools.tool_registry import tool_registry


def test_resolve_alias_with_null_mcp_tool():
    resolved = tool_registry.resolve("douyin_expand_suggest_words")
    assert resolved.use_mcp is False
    assert resolved.mcp_tool is None


def test_collect_is_intentional_stub():
    resolved = tool_registry.resolve("douyin_collect_hot_keywords")
    assert resolved.use_mcp is False
    assert resolved.mcp_tool is None
    assert "douyin-keyword-research" in resolved.allow_in_skills


def test_keyword_cards_pipeline_not_registered():
    resolved = tool_registry.resolve("keyword_cards_pipeline")
    assert resolved.registered is False


def test_assert_allowed_rejects_unregistered():
    resolved = tool_registry.resolve("keyword_cards_pipeline")
    try:
        tool_registry.assert_allowed(resolved, "douyin-keyword-research")
    except PermissionError:
        return
    assert False, "expected PermissionError"
