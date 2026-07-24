"""Configurable step handlers (score / report / temu finalize)."""

from __future__ import annotations

import time
from typing import Any, Callable

from agent.state import AgentState
from agent.tools import douyin_stub
from agent.tools.mcp_runtime import mcp_runtime

Handler = Callable[[AgentState, dict[str, Any]], tuple[dict[str, Any], float, bool]]


def _gather_keywords(collected: dict) -> list[str]:
    words: list[str] = []
    c = collected.get("collect") or {}
    for item in c.get("keywords") or []:
        if isinstance(item, dict) and item.get("word"):
            words.append(item["word"])
    e = collected.get("expand") or {}
    words.extend(e.get("suggest_words") or [])
    seen: set[str] = set()
    out: list[str] = []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def handle_score(state: AgentState, collected: dict[str, Any]) -> tuple[dict[str, Any], float, bool]:
    seed = state.get("seed") or "渔具"
    result = douyin_stub.score_keywords(
        seed,
        raw_keywords=_gather_keywords(collected),
        include_video=state.get("include_video", True),
        include_product=state.get("include_product", True),
    )
    alerts = list(result.get("alerts") or [])
    alerts.insert(
        0,
        {"type": "warn", "text": "当前采集步骤为 stub 数据，尚未接入原子 MCP"},
    )
    result["alerts"] = alerts
    tags = list(result.get("tags") or [])
    if "数据源：stub" not in tags:
        tags.append("数据源：stub")
    result["tags"] = tags
    return {"score": result}, (0.85 if result.get("ok") else 0.3), False


def handle_report_douyin(
    state: AgentState, collected: dict[str, Any]
) -> tuple[dict[str, Any], float, bool]:
    score = collected.get("score") or {}
    draft = {
        "kind": "douyin_keyword",
        "summary": score.get("summary"),
        "tags": score.get("tags"),
        "alerts": score.get("alerts"),
        "categories": score.get("categories"),
        "data_source": {"source": "stub", "tool": "score"},
    }
    return {"report_draft": draft}, (0.9 if score.get("ok") else 0.2), False


def handle_finalize_temu_listing(
    state: AgentState, collected: dict[str, Any]
) -> tuple[dict[str, Any], float, bool]:
    """Poll Commander via MCP until terminal status, then build report_draft."""
    submit = collected.get("submit") or {}
    if submit.get("ok") is False:
        msg = submit.get("error") or "提交上架失败"
        draft = {
            "kind": "temu_listing",
            "ok": False,
            "status": "failed",
            "message": msg,
            "shop_id": state.get("shop_id") or submit.get("shop_id"),
            "agent_id": state.get("agent_id") or submit.get("agent_id") or "肉机",
            "task_id": None,
            "data_source": {"source": "mcp", "tool": "temu_product_issue_submit"},
        }
        return {"report_draft": draft, "finalize": draft}, 0.2, True

    agent_id = state.get("agent_id") or submit.get("agent_id") or ""
    platform = state.get("platform") or "temu"
    candidates = submit.get("candidate_task_ids") or []
    task_id = str(candidates[0]) if candidates else ""

    last: dict[str, Any] = {}
    terminal = {"success", "failed", "cancelled"}
    # One graph step: poll inside handler (~10 min). Do not micro-retry at graph level.
    poll_rounds = 40
    poll_interval_s = 15
    for _ in range(poll_rounds):
        result = mcp_runtime.invoke_logical(
            "temu_product_issue_status",
            {
                "agent_id": agent_id,
                "platform": platform,
                "task_id": task_id,
                "list_scope": "all",
            },
        )
        if not result.ok:
            last = {
                "ok": False,
                "status": "failed",
                "message": result.error or "状态查询失败",
                "task_id": task_id or None,
            }
            break
        data = dict(result.data or {})
        if task_id and data.get("tasks"):
            match = next(
                (t for t in data["tasks"] if str(t.get("taskId") or "") == task_id),
                None,
            )
            if match:
                data["status"] = match.get("status")
                data["message"] = match.get("message")
                data["task_id"] = match.get("taskId")
                data["tasks_ahead"] = match.get("tasksAhead")
        last = data
        status = (data.get("status") or "").lower()
        if status in terminal:
            break
        time.sleep(poll_interval_s)

    status = (last.get("status") or "unknown").lower()
    ok = status == "success"
    msg = last.get("message") or last.get("error") or status
    if status == "processing":
        msg = f"仍在处理中（已单步轮询结束）：{msg}"
        ok = False

    draft = {
        "kind": "temu_listing",
        "ok": ok,
        "status": status
        if status in ("processing", "success", "failed", "cancelled")
        else "unknown",
        "message": str(msg),
        "shop_id": state.get("shop_id") or submit.get("shop_id"),
        "agent_id": agent_id or "肉机",
        "task_id": last.get("task_id") or task_id or None,
        "data_source": {"source": "mcp", "tool": "temu_product_issue_status"},
    }
    hard_fail = status in ("failed", "cancelled") or (last.get("ok") is False)
    # processing after in-handler poll: exit graph once (do not micro-retry); quality high enough to pass threshold
    if ok:
        quality = 0.95
    elif status == "processing":
        quality = 0.9
    else:
        quality = 0.25
    return {"report_draft": draft, "finalize": draft}, quality, hard_fail


STEP_HANDLERS: dict[str, Handler] = {
    "score": handle_score,
    "report_douyin": handle_report_douyin,
    "finalize_temu_listing": handle_finalize_temu_listing,
}


def run_step_action(
    action: str, state: AgentState, collected: dict[str, Any]
) -> tuple[dict[str, Any], float, bool]:
    handler = STEP_HANDLERS.get(action)
    if not handler:
        return {state.get("current_step", "unknown"): {"status": "skipped"}}, 0.5, False
    return handler(state, collected)
