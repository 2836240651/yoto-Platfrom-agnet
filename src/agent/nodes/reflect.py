"""Reflect on progress and decide next action."""

from __future__ import annotations

from agent.state import AgentState


def reflect(state: AgentState) -> dict:
    """Check if the task should continue, finish, or escalate."""
    plan = state.get("plan") or []
    current = state.get("current_step", 0)
    loop_count = state.get("loop_count", 0)
    max_loops = state.get("max_loops", 15)

    if loop_count >= max_loops:
        return {"status": "failed", "errors": (state.get("errors") or []) + ["max_loops exceeded"]}

    if current >= len(plan):
        return {"status": "reviewing"}

    return {"status": "executing"}
