"""Graph node helpers."""

from __future__ import annotations

import time
from typing import Any

from agent.state import AgentState


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append_event(state: AgentState, node: str, message: str, **extra: Any) -> list[dict]:
    events = list(state.get("events") or [])
    events.append({"ts": _now_iso(), "node": node, "message": message, **extra})
    return events[-100:]


def current_step_def(state: AgentState) -> dict | None:
    plan = state.get("plan") or []
    idx = state.get("current_step", 0)
    if idx >= len(plan):
        return None
    return plan[idx]


def progress_snapshot(state: AgentState) -> dict:
    plan = state.get("plan") or []
    idx = state.get("current_step", 0)
    total = max(len(plan), 1)
    step_def = plan[idx] if idx < len(plan) else (plan[-1] if plan else {"label": "完成"})
    label = step_def.get("label") or step_def.get("name", "处理中")
    base_pct = int((idx / total) * 100)
    micro_used = state.get("micro_budget_used", 0)
    micro_cap = max(state.get("micro_budget_current", 1), 1)
    intra = int((micro_used / micro_cap) * (100 / total))
    percent = min(99, base_pct + intra) if state.get("status") != "done" else 100
    return {
        "progress_step_name": label,
        "progress_percent": percent,
        "micro_attempt": micro_used,
        "replan_used": state.get("replan_budget_used", 0),
    }
