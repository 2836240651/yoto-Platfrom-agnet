"""Social media publish skill wiring tests."""

from __future__ import annotations

from agent.constants import BLACKBOX_SKILLS, SKILL_PLANS, is_blackbox_skill
from agent.nodes.validate import _report_valid
from agent.tools.tool_registry import tool_registry


def test_social_skill_plan_exists():
    plan = SKILL_PLANS["social-media-publish"]
    assert plan[0]["tool"] == "social_publish_submit"
    assert plan[1]["action"] == "finalize_social_publish"


def test_social_is_blackbox():
    assert "social-media-publish" in BLACKBOX_SKILLS
    assert is_blackbox_skill("social-media-publish")


def test_social_registry_requires_mcp():
    submit = tool_registry.resolve("social_publish_submit")
    status = tool_registry.resolve("social_publish_status")
    assert submit.mcp_tool == "social_publish_submit"
    assert status.mcp_tool == "social_publish_status"
    assert "social-media-publish" in submit.allow_in_skills
    tool_registry.assert_allowed(submit, "social-media-publish")


def test_social_report_validate():
    report = {
        "kind": "social_publish",
        "ok": True,
        "status": "success",
        "message": "ok",
        "job_id": "j1",
    }
    assert _report_valid(report)
