"""Unit tests for Temu listing skill wiring."""

from __future__ import annotations

from agent.constants import SKILL_PLANS
from agent.nodes.generate import generate_report
from agent.nodes.validate import validate_report_schema
from agent.tools.arg_builders import build_tool_args
from agent.tools.tool_registry import tool_registry


def test_temu_skill_plan_exists():
    plan = SKILL_PLANS["temu-product-listing"]
    assert plan[0]["tool"] == "temu_product_issue_submit"
    assert plan[1]["action"] == "finalize_temu_listing"


def test_temu_registry_requires_mcp():
    submit = tool_registry.resolve("temu_product_issue_submit")
    status = tool_registry.resolve("temu_product_issue_status")
    assert submit.use_mcp is True
    assert submit.requires_mcp is True
    assert "temu-product-listing" in submit.allow_in_skills
    assert status.mcp_tool == "temu_product_issue_status"
    tool_registry.assert_allowed(submit, "temu-product-listing")


def test_temu_arg_builder():
    args = build_tool_args(
        "temu_product_issue_submit",
        {"excel_path": "/tmp/a.xlsx", "shop_id": "8381218", "agent_id": "肉机"},
    )
    assert args["file_path"] == "/tmp/a.xlsx"
    assert args["shop_id"] == "8381218"
    assert args["precheck"] is True


def test_temu_report_validate_and_generate():
    draft = {
        "kind": "temu_listing",
        "ok": True,
        "status": "success",
        "message": "执行完成",
        "shop_id": "8381218",
        "agent_id": "肉机",
        "task_id": "t1",
    }
    out = generate_report({"collected_data": {"report_draft": draft, "finalize": draft}})
    assert out["report"]["kind"] == "temu_listing"
    assert out["report"]["ok"] is True
    validated = validate_report_schema({"report": out["report"], "generate_retry_count": 0})
    assert validated["validate_route"] == "ok"
