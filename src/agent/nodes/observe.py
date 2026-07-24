"""Observe act output — compress for state."""

from __future__ import annotations

from agent.budget import bump_loop
from agent.nodes.helpers import append_event, current_step_def
from agent.state import AgentState


def observe(state: AgentState) -> dict:
    step = current_step_def(state)
    name = step.get("name", "?") if step else "?"
    q = state.get("quality_score")
    err = state.get("last_tool_error")
    msg = f"观察 {name}：质量={q:.2f}" if q is not None else f"观察 {name}"
    if err:
        msg = f"观察 {name}：{err}"

    no_gain = 0 if state.get("micro_budget_used", 0) <= 1 else state.get("consecutive_no_gain", 0)
    gain = state.get("last_gain_delta") or 0.0
    if gain <= 0:
        no_gain += 1
    else:
        no_gain = 0

    return {
        **bump_loop(state),
        "consecutive_no_gain": no_gain,
        "events": append_event(state, "observe", msg),
    }
