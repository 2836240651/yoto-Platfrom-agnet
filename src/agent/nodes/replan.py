"""Replan fragment after step failure — reset micro budget for current step."""

from __future__ import annotations

from agent.budget import step_micro_default, step_micro_max
from agent.nodes.helpers import append_event, current_step_def
from agent.state import AgentState


def replan_fragment(state: AgentState) -> dict:
    step = current_step_def(state)
    name = step.get("name", "collect") if step else "collect"
    return {
        "micro_budget_current": step_micro_default(name),
        "micro_budget_max": step_micro_max(name),
        "micro_budget_used": 0,
        "failure_class": None,
        "last_tool_error": None,
        "consecutive_no_gain": 0,
        "events": append_event(
            state,
            "replan_fragment",
            f"重规划步骤：{step.get('label', name) if step else name}",
        ),
    }
