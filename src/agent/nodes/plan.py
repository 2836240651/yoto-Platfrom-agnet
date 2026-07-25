"""Plan fixed steps for a Skill."""

from __future__ import annotations

from agent.constants import SKILL_PLANS as CANONICAL_PLANS
from agent.state import AgentState


def plan_steps(state: AgentState) -> dict:
    """Build a deterministic step list for the selected skill."""
    skill = state.get("skill") or "general"
    plan = CANONICAL_PLANS.get(skill) or CANONICAL_PLANS.get("douyin-keyword-research") or []
    return {
        "plan": [dict(s) for s in plan],
        "current_step": 0,
        "loop_count": 0,
        "max_loops": state.get("max_loops", 15),
        "retry_count": 0,
        "max_retries": state.get("max_retries", 3),
        "status": "executing",
        "collected_data": state.get("collected_data") or {},
        "errors": state.get("errors") or [],
        "dead_ends": state.get("dead_ends") or [],
    }
