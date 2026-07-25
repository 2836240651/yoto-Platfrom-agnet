"""Tests for tool registry."""

from agent.tools.tool_registry import tool_registry


def test_analyze_tool_registered_as_non_mcp():
    tool_registry.reload()
    resolved = tool_registry.resolve("douyin_analyze_keywords")
    assert resolved.use_mcp is False
    assert resolved.mcp_tool is None
    assert "douyin-keyword-research" in resolved.allow_in_skills


def test_expand_deprecated_not_in_skill():
    tool_registry.reload()
    resolved = tool_registry.resolve("douyin_expand_suggest_words")
    assert resolved.allow_in_skills == []


def test_collect_uses_platform_mcp():
    tool_registry.reload()
    resolved = tool_registry.resolve("douyin_collect_hot_keywords")
    assert resolved.use_mcp is True
    assert resolved.mcp_tool == "douyin_collect_hot_keywords"
    assert resolved.server == "platform_mcp"
    assert resolved.requires_mcp is True
    assert "douyin-keyword-research" in resolved.allow_in_skills


def test_collect_has_no_stub_factory():
    from agent.tools.stub_dispatch import STUB_FACTORIES

    assert "douyin_collect_hot_keywords" not in STUB_FACTORIES


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
