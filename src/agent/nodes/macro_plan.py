"""Macro plan from skill."""

from __future__ import annotations

import copy

from agent.constants import SKILL_PLANS
from agent.nodes.helpers import append_event
from agent.state import AgentState


def macro_plan(state: AgentState) -> dict:
    skill = state.get("skill") or "douyin-keyword-research"
    plan = copy.deepcopy(SKILL_PLANS.get(skill, SKILL_PLANS["douyin-keyword-research"]))
    return {
        "plan": plan,
        "current_step": 0,
        "status": "executing",
        "events": append_event(state, "macro_plan", f"已生成 {len(plan)} 步执行计划"),
    }
