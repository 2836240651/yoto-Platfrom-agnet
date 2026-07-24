"""Shared constants for skills."""

from __future__ import annotations

MACRO_STEP_LABELS: dict[str, str] = {
    "collect": "采集数据",
    "expand": "扩展联想词",
    "score": "打分分类",
    "report": "生成报告",
    "submit": "提交上架",
    "finalize": "确认结果",
}

MACRO_STEP_ORDER = ["collect", "expand", "score", "report"]

# Pure MCP black-box skills: no platform chat model; ignore session model_id.
BLACKBOX_SKILLS: frozenset[str] = frozenset(
    {
        "temu-product-listing",
    }
)

# Session model picker allowlist (explicit pin).
ALLOWED_MODEL_IDS: frozenset[str] = frozenset(
    {
        "agnes-2.0-flash",
        "gpt-5.6-luna",
        "gpt-5.6-sol",
        "gpt-5.6-terra",
    }
)

# Plan steps:
# - tool: logical MCP/stub tool name (→ action tool:<name>)
# - action: non-tool handler key in step_handlers.STEP_HANDLERS
SKILL_PLANS: dict[str, list[dict]] = {
    "douyin-keyword-research": [
        {
            "id": "1",
            "name": "collect",
            "label": "采集数据",
            "tool": "douyin_collect_hot_keywords",
            "status": "pending",
        },
        {
            "id": "2",
            "name": "expand",
            "label": "扩展联想词",
            "tool": "douyin_expand_suggest_words",
            "status": "pending",
        },
        {
            "id": "3",
            "name": "score",
            "label": "打分分类",
            "tool": None,
            "action": "score",
            "status": "pending",
        },
        {
            "id": "4",
            "name": "report",
            "label": "生成报告",
            "tool": None,
            "action": "report_douyin",
            "status": "pending",
        },
    ],
    "temu-product-listing": [
        {
            "id": "1",
            "name": "submit",
            "label": "提交上架",
            "tool": "temu_product_issue_submit",
            "status": "pending",
        },
        {
            "id": "2",
            "name": "finalize",
            "label": "确认结果",
            "tool": None,
            "action": "finalize_temu_listing",
            "status": "pending",
        },
    ],
}


def is_blackbox_skill(skill: str | None) -> bool:
    return bool(skill) and skill in BLACKBOX_SKILLS


def normalize_model_id(model_id: str | None) -> str | None:
    """Return stripped id or None. Does not validate allowlist."""
    if model_id is None:
        return None
    value = str(model_id).strip()
    return value or None
