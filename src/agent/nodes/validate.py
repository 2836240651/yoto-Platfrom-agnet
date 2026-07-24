"""Validate structured report before consolidate."""

from __future__ import annotations

from agent.nodes.helpers import append_event
from agent.state import AgentState

_CATEGORY_KEYS = ("video_hot", "video_potential", "product_hot", "product_potential")


def _douyin_valid(report: dict) -> bool:
    for key in ("summary", "tags", "alerts", "categories"):
        if key not in report:
            return False
    cats = report.get("categories")
    if not isinstance(cats, dict):
        return False
    for key in _CATEGORY_KEYS:
        if key not in cats or not isinstance(cats[key], list):
            return False
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return False
    for field in ("keyword_count", "video_sample_count", "product_sku_count", "p0_count"):
        if field not in summary:
            return False
    return True


def _temu_valid(report: dict) -> bool:
    for key in ("ok", "status", "message"):
        if key not in report:
            return False
    status = report.get("status")
    return status in ("processing", "success", "failed", "cancelled", "unknown")


def _report_valid(report: dict | None) -> bool:
    if not report or not isinstance(report, dict):
        return False
    kind = report.get("kind") or "douyin_keyword"
    if kind == "douyin_keyword":
        return _douyin_valid(report)
    if kind == "temu_listing":
        return _temu_valid(report)
    return False


def validate_report_schema(state: AgentState) -> dict:
    report = state.get("report")
    if _report_valid(report):
        return {
            "validate_route": "ok",
            "status": "done",
            "progress_step_name": "完成",
            "progress_percent": 100,
            "events": append_event(state, "validate", "报告校验通过"),
        }

    retry = state.get("generate_retry_count", 0)
    retry_max = state.get("generate_retry_max", 2)
    if retry < retry_max:
        return {
            "validate_route": "retry_generate",
            "generate_retry_count": retry + 1,
            "events": append_event(
                state, "validate", f"报告校验失败，重试生成 ({retry + 1}/{retry_max})"
            ),
        }

    return {
        "validate_route": "fail",
        "status": "failed",
        "user_error_message": "报告生成失败，请稍后重试",
        "events": append_event(state, "validate", "报告校验失败，已达重试上限"),
    }
