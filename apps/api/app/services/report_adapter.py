"""Map LangGraph state to API schemas."""

from __future__ import annotations

from typing import Any

from app.schemas.tasks import (
    AlertItem,
    DataSourceMeta,
    DouyinTaskReport,
    KeywordCard,
    MetricItem,
    ReportCategories,
    ReportSummary,
    SocialPublishReport,
    TaskProgress,
    TemuListingReport,
)


def graph_status_to_api(status: str | None) -> str:
    mapping = {
        "planning": "running",
        "executing": "running",
        "reviewing": "running",
        "done": "completed",
        "failed": "failed",
    }
    return mapping.get(status or "", "running")


def _card(raw: dict[str, Any]) -> KeywordCard:
    return KeywordCard(
        keyword=raw["keyword"],
        priority=raw["priority"],
        trend=raw["trend"],
        reason=raw["reason"],
        metrics=[MetricItem(label=m["label"], value=m["value"]) for m in raw.get("metrics") or []],
        evidence=list(raw.get("evidence") or []),
        action=raw.get("action") or "",
        queried_term=raw.get("queried_term"),
        query_level=raw.get("query_level"),
        query_source=raw.get("query_source"),
        query_dimension=raw.get("query_dimension"),
    )


def _data_source(raw: dict[str, Any] | None) -> DataSourceMeta | None:
    if not raw or not isinstance(raw, dict):
        return None
    source = raw.get("source")
    if source not in ("mcp", "stub", "stub_fallback"):
        return None
    return DataSourceMeta(
        source=source,
        tool=raw.get("tool"),
        resolved_tool=raw.get("resolved_tool"),
        mcp_error=raw.get("mcp_error"),
    )


def state_to_task_report(
    state: dict[str, Any],
) -> DouyinTaskReport | TemuListingReport | SocialPublishReport | None:
    report = state.get("report")
    if not report:
        return None

    kind = report.get("kind") or "douyin_keyword"
    if kind == "social_publish":
        status = report.get("status") or "unknown"
        if status not in ("pending", "running", "success", "failed", "unknown"):
            status = "unknown"
        return SocialPublishReport(
            kind="social_publish",
            ok=bool(report.get("ok")),
            status=status,  # type: ignore[arg-type]
            message=str(report.get("message") or ""),
            job_id=report.get("job_id"),
            platform_type=report.get("platform_type"),
            publish_runtime=report.get("publish_runtime"),
            title=report.get("title"),
            account_list=list(report.get("account_list") or []),
            data_source=_data_source(report.get("data_source")),
        )

    if kind == "temu_listing":
        status = report.get("status") or "unknown"
        if status not in ("processing", "success", "failed", "cancelled", "unknown"):
            status = "unknown"
        return TemuListingReport(
            kind="temu_listing",
            ok=bool(report.get("ok")),
            status=status,  # type: ignore[arg-type]
            message=str(report.get("message") or ""),
            shop_id=report.get("shop_id"),
            agent_id=report.get("agent_id"),
            task_id=report.get("task_id"),
            data_source=_data_source(report.get("data_source")),
        )

    cats = report.get("categories") or {}
    summary = report.get("summary") or {}
    ds = _data_source(report.get("data_source"))
    return DouyinTaskReport(
        kind="douyin_keyword",
        summary=ReportSummary(
            keyword_count=int(summary.get("keyword_count", 0)),
            video_sample_count=int(summary.get("video_sample_count", 0)),
            product_sku_count=int(summary.get("product_sku_count", 0)),
            p0_count=int(summary.get("p0_count", 0)),
        ),
        tags=list(report.get("tags") or []),
        alerts=[AlertItem(type=a["type"], text=a["text"]) for a in report.get("alerts") or []],
        categories=ReportCategories(
            video_hot=[_card(c) for c in cats.get("video_hot") or []],
            video_potential=[_card(c) for c in cats.get("video_potential") or []],
            product_hot=[_card(c) for c in cats.get("product_hot") or []],
            product_potential=[_card(c) for c in cats.get("product_potential") or []],
        ),
        data_source=ds or DataSourceMeta(source="stub", tool="legacy"),
    )


def state_to_progress(state: dict[str, Any]) -> TaskProgress:
    plan = state.get("plan") or []
    total = len(plan) or 4
    idx = int(state.get("current_step", 0))
    graph_status = state.get("status")

    if graph_status == "done":
        return TaskProgress(
            step=total,
            total_steps=total,
            step_name="完成",
            percent=100,
            micro_attempt=state.get("micro_attempt") or state.get("micro_budget_used") or 0,
            micro_budget=state.get("micro_budget_current") or 3,
            replan_used=state.get("replan_used") or state.get("replan_budget_used") or 0,
        )

    if idx >= len(plan) and plan:
        step = total
        step_name = state.get("progress_step_name") or "生成报告"
    else:
        step = min(idx + 1, total)
        if idx < len(plan):
            step_name = plan[idx].get("label") or plan[idx].get("name") or "处理中"
        else:
            step_name = state.get("progress_step_name") or "准备中"

    return TaskProgress(
        step=step,
        total_steps=total,
        step_name=step_name,
        percent=int(state.get("progress_percent") or 0),
        micro_attempt=int(state.get("micro_attempt") or state.get("micro_budget_used") or 0),
        micro_budget=int(state.get("micro_budget_current") or 3),
        replan_used=int(state.get("replan_used") or state.get("replan_budget_used") or 0),
    )


def state_to_debug(state: dict[str, Any]) -> dict[str, Any]:
    """Expose LangGraph loop internals for developer UI."""
    events = state.get("events") or []
    if isinstance(events, list):
        events = events[-120:]

    return {
        "status": state.get("status"),
        "skill": state.get("skill"),
        "current_action": state.get("current_action"),
        "micro_route": state.get("micro_route"),
        "failure_class": state.get("failure_class"),
        "user_error_message": state.get("user_error_message"),
        "last_tool_error": state.get("last_tool_error"),
        "quality_score": state.get("quality_score"),
        "consecutive_no_gain": state.get("consecutive_no_gain"),
        "global_loop_used": state.get("global_loop_used"),
        "micro_budget_default": state.get("micro_budget_default"),
        "micro_budget_current": state.get("micro_budget_current"),
        "micro_budget_max": state.get("micro_budget_max"),
        "micro_budget_used": state.get("micro_budget_used"),
        "replan_budget_used": state.get("replan_budget_used"),
        "replan_used": state.get("replan_used") or state.get("replan_budget_used"),
        "current_step": state.get("current_step"),
        "plan": state.get("plan"),
        "events": events,
        "collected_meta": {
            k: (v.get("_meta") if isinstance(v, dict) else None)
            for k, v in (state.get("collected_data") or {}).items()
        },
    }
