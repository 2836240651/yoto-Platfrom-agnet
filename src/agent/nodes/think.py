"""Think or rule-route before act — driven by plan step.tool / step.action."""

from __future__ import annotations

from agent.budget import bump_loop
from agent.nodes.helpers import append_event, current_step_def
from agent.state import AgentState


def think_or_rule(state: AgentState) -> dict:
    step = current_step_def(state)
    if not step:
        return {**bump_loop(state), "micro_route": "fail", "failure_class": "permanent"}

    tool = step.get("tool")
    step_action = step.get("action")
    if tool:
        action = f"tool:{tool}"
    elif step_action:
        action = f"action:{step_action}"
    else:
        action = "noop"

    return {
        **bump_loop(state),
        "current_action": action,
        "events": append_event(state, "think_or_rule", f"下一步动作：{action}"),
    }
