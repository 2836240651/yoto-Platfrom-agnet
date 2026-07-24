"""Exit a macro step — mark done and advance pointer."""

from __future__ import annotations

from agent.nodes.helpers import append_event, current_step_def, progress_snapshot
from agent.state import AgentState


def step_exit(state: AgentState) -> dict:
    step = current_step_def(state)
    plan = list(state.get("plan") or [])
    idx = state.get("current_step", 0)

    if step and idx < len(plan):
        plan[idx] = {**step, "status": "done"}

    next_idx = idx + 1
    updates: dict = {
        "plan": plan,
        "current_step": next_idx,
        "micro_budget_used": 0,
        "failure_class": None,
        "last_tool_error": None,
        "events": append_event(
            state,
            "step_exit",
            f"完成步骤：{step.get('label', step.get('name', '?')) if step else '?'}",
        ),
    }
    updates.update(progress_snapshot({**state, **updates}))
    return updates
