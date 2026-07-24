"""Plan fixed steps for a Skill."""

from __future__ import annotations

from agent.state import AgentState, StepPlan

# Hard-coded plans per skill (production: load from SKILL.md frontmatter).
SKILL_PLANS: dict[str, list[StepPlan]] = {
    "douyin-keyword-research": [
        {"id": "1", "name": "collect", "tool": "douyin_collect_hot_keywords", "status": "pending"},
        {"id": "2", "name": "expand", "tool": "douyin_expand_suggest_words", "status": "pending"},
        {"id": "3", "name": "score", "tool": None, "status": "pending"},
        {"id": "4", "name": "report", "tool": None, "status": "pending"},
    ],
    "general": [
        {"id": "1", "name": "answer", "tool": None, "status": "pending"},
    ],
}


def plan_steps(state: AgentState) -> dict:
    """Build a deterministic step list for the selected skill."""
    skill = state.get("skill") or "general"
    plan = SKILL_PLANS.get(skill, SKILL_PLANS["general"])
    return {
        "plan": plan,
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
