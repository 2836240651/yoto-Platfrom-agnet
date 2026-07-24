"""Emit operator-visible progress snapshot."""

from __future__ import annotations

from agent.nodes.helpers import append_event, progress_snapshot
from agent.state import AgentState


def emit_progress(state: AgentState) -> dict:
    snap = progress_snapshot(state)
    snap["micro_attempt"] = state.get("micro_budget_used", 0)
    snap["replan_used"] = state.get("replan_budget_used", 0)
    return {
        **snap,
        "events": append_event(
            state,
            "emit_progress",
            f"{snap['progress_step_name']} · {snap['progress_percent']}%",
        ),
    }
