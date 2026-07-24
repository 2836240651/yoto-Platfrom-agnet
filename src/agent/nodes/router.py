"""Conditional routing helpers for v0.2 graph."""

from __future__ import annotations

from agent.state import AgentState


def after_step_enter(state: AgentState) -> str:
    if state.get("micro_route") == "macro_done":
        return "macro_reflect"
    if state.get("status") == "failed":
        return "fail"
    return "think"


def after_micro_judge(state: AgentState) -> str:
    route = state.get("micro_route")
    if state.get("status") == "failed":
        return "fail"
    if route == "done":
        return "step_exit"
    if route == "retry_step":
        return "think"
    if route == "replan":
        return "replan"
    if route == "macro_done":
        return "macro_reflect"
    return "fail"


def after_emit_progress(state: AgentState) -> str:
    plan = state.get("plan") or []
    idx = state.get("current_step", 0)
    if idx < len(plan):
        return "step_enter"
    return "macro_reflect"


def after_validate(state: AgentState) -> str:
    route = state.get("validate_route")
    if route == "ok":
        return "consolidate"
    if route == "retry_generate":
        return "generate"
    return "fail"
