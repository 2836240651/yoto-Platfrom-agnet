"""Generate final structured report — discriminated by draft.kind."""

from __future__ import annotations

from agent.nodes.helpers import append_event
from agent.state import AgentState


def generate_report(state: AgentState) -> dict:
    collected = state.get("collected_data") or {}
    draft = collected.get("report_draft") or {}
    kind = draft.get("kind") or (collected.get("finalize") or {}).get("kind")

    if kind == "social_publish":
        return _generate_social(state, collected, draft)
    if kind == "temu_listing" or (
        collected.get("finalize") and kind not in ("social_publish", "douyin_keyword")
    ):
        fin = collected.get("finalize") or draft or {}
        if fin.get("kind") == "social_publish" or (
            "platform_type" in fin and "shop_id" not in fin
        ):
            return _generate_social(state, collected, draft)
        return _generate_temu(state, collected, draft)

    if kind == "douyin_keyword" or collected.get("score"):
        return _generate_douyin(state, collected, draft)

    return {
        "report": None,
        "status": "reviewing",
        "events": append_event(state, "generate", "缺少可识别的报告草稿 kind"),
    }


def _generate_social(state: AgentState, collected: dict, draft: dict) -> dict:
    src = draft or collected.get("finalize") or {}
    status = src.get("status") or "unknown"
    ok = bool(src.get("ok")) and status == "success"
    report = {
        "kind": "social_publish",
        "ok": ok,
        "status": status,
        "message": src.get("message") or "",
        "job_id": src.get("job_id"),
        "platform_type": src.get("platform_type") or state.get("platform_type"),
        "publish_runtime": src.get("publish_runtime"),
        "title": src.get("title") or state.get("title"),
        "account_list": list(src.get("account_list") or state.get("account_list") or []),
        "data_source": src.get("data_source")
        or {"source": "mcp", "tool": "social_publish_status"},
    }
    title = report.get("title") or ""
    final = (
        f"社媒发布成功：{title}"
        if ok
        else f"社媒发布未成功：{report.get('message') or status}"
    )
    return {
        "report": report,
        "final_answer": final,
        "status": "reviewing",
        "events": append_event(state, "generate", "已生成社媒发布报告"),
    }


def _generate_temu(state: AgentState, collected: dict, draft: dict) -> dict:
    src = draft or collected.get("finalize") or {}
    status = src.get("status") or "unknown"
    ok = bool(src.get("ok")) and status == "success"
    report = {
        "kind": "temu_listing",
        "ok": ok,
        "status": status,
        "message": src.get("message") or "",
        "shop_id": src.get("shop_id") or state.get("shop_id"),
        "agent_id": src.get("agent_id") or state.get("agent_id") or "肉机",
        "task_id": src.get("task_id"),
        "data_source": src.get("data_source")
        or {"source": "mcp", "tool": "temu_product_issue_status"},
    }
    shop = report.get("shop_id") or ""
    final = (
        f"Temu 上架成功（店铺 {shop}）"
        if ok
        else f"Temu 上架未成功：{report.get('message') or status}"
    )
    return {
        "report": report,
        "final_answer": final,
        "status": "reviewing",
        "events": append_event(state, "generate", "Temu 上架结果已汇总"),
    }


def _generate_douyin(state: AgentState, collected: dict, draft: dict) -> dict:
    score = collected.get("score") or collected.get("analyze") or {}
    collect = collected.get("collect") or {}
    meta = (collect.get("_meta") or {}) if isinstance(collect, dict) else {}
    collect_ds = collect.get("data_source") if isinstance(collect.get("data_source"), dict) else {}
    draft_ds = draft.get("data_source") if isinstance(draft.get("data_source"), dict) else {}
    score_ds = score.get("data_source") if isinstance(score.get("data_source"), dict) else {}
    source = (
        draft_ds.get("source")
        or score_ds.get("source")
        or meta.get("source")
        or collect_ds.get("source")
        or "stub"
    )
    data_source = {
        "source": source,
        "tool": draft_ds.get("tool")
        or score_ds.get("tool")
        or meta.get("tool")
        or collect_ds.get("tool")
        or "douyin_analyze_keywords",
        "provider": draft_ds.get("provider")
        or score_ds.get("provider")
        or ("chanmama" if source == "mcp" else None),
        "mode": draft_ds.get("mode") or score_ds.get("mode"),
    }

    if score.get("ok"):
        report = {
            "kind": "douyin_keyword",
            "summary": score["summary"],
            "tags": score.get("tags") or [f"种子词：{state.get('seed', '')}"],
            "alerts": score.get("alerts") or [],
            "categories": score["categories"],
            "data_source": data_source,
        }
    elif draft:
        report = {
            "kind": draft.get("kind") or "douyin_keyword",
            "summary": draft.get("summary") or {},
            "tags": draft.get("tags") or [],
            "alerts": draft.get("alerts") or [],
            "categories": draft.get("categories") or {},
            "data_source": data_source,
        }
    else:
        return {
            "report": None,
            "status": "reviewing",
            "events": append_event(state, "generate", "缺少评分数据，无法生成报告"),
        }

    alerts = list(report.get("alerts") or [])
    if source in ("stub", "stub_fallback"):
        if not any(
            "stub" in (a.get("text") or "").lower() or "尚未接入" in (a.get("text") or "")
            for a in alerts
        ):
            alerts.insert(
                0,
                {"type": "warn", "text": "当前采集步骤为 stub 数据，尚未接入真实蝉妈妈会话"},
            )
    else:
        alerts = [
            a
            for a in alerts
            if "stub" not in (a.get("text") or "").lower()
            and "尚未接入" not in (a.get("text") or "")
        ]
    report["alerts"] = alerts
    report["kind"] = "douyin_keyword"
    report["data_source"] = data_source

    seed = state.get("seed", "")
    final_answer = f"「{seed}」关键词分析完成，共 {report['summary'].get('keyword_count', 0)} 个词卡"
    return {
        "report": report,
        "final_answer": final_answer,
        "status": "reviewing",
        "events": append_event(state, "generate", "结构化报告已生成"),
    }
