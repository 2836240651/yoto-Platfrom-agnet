"""Enter a macro step — reset per-step micro counters."""

from __future__ import annotations

from agent.budget import step_micro_default, step_micro_max
from agent.nodes.helpers import append_event, current_step_def, progress_snapshot
from agent.state import AgentState


def step_enter(state: AgentState) -> dict:
    step = current_step_def(state)
    if not step:
        return {"micro_route": "macro_done"}

    name = step.get("name", "unknown")
    plan = list(state.get("plan") or [])
    idx = state.get("current_step", 0)
    plan[idx] = {**step, "status": "running"}

    updates: dict = {
        "plan": plan,
        "micro_budget_default": step_micro_default(name),
        "micro_budget_current": step_micro_default(name),
        "micro_budget_max": step_micro_max(name),
        "micro_budget_used": 0,
        "last_step_quality": None,
        "last_tool_error": None,
        "failure_class": None,
        "micro_route": None,
        "consecutive_no_gain": 0,
        "events": append_event(state, "step_enter", f"进入步骤：{step.get('label', name)}"),
    }
    updates.update(progress_snapshot({**state, **updates}))
    return updates
