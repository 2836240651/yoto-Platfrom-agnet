"""Macro-level reflection before final report generation."""

from __future__ import annotations

from agent.nodes.helpers import append_event
from agent.state import AgentState


def macro_reflect(state: AgentState) -> dict:
    plan = state.get("plan") or []
    done = sum(1 for s in plan if s.get("status") == "done")
    dead = len(state.get("dead_ends") or [])
    return {
        "status": "reviewing",
        "progress_step_name": "汇总分析",
        "progress_percent": 95,
        "events": append_event(
            state,
            "macro_reflect",
            f"宏观步骤完成 {done}/{len(plan)}，重规划 {dead} 次",
        ),
    }
