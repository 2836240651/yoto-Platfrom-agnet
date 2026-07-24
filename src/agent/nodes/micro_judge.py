"""Micro-loop judge — code-owned routing."""

from __future__ import annotations

from agent.budget import (
    bump_loop,
    can_extend_micro_budget,
    extend_micro_budget,
    fuse_tripped,
)
from agent.nodes.helpers import append_event, current_step_def
from agent.state import AgentState


def micro_judge(state: AgentState) -> dict:
    tripped, reason = fuse_tripped(state)
    if tripped:
        return {
            **bump_loop(state),
            "micro_route": "fail",
            "status": "failed",
            "user_error_message": reason,
            "events": append_event(state, "micro_judge", f"保险丝触发：{reason}"),
        }

    step = current_step_def(state)
    if not step:
        return {**bump_loop(state), "micro_route": "macro_done"}

    name = step.get("name", "")
    quality = state.get("last_step_quality") or state.get("quality_score") or 0.0
    threshold = state.get("quality_threshold", 0.75)

    if state.get("failure_class") is None and quality >= threshold:
        return {
            **bump_loop(state),
            "micro_route": "done",
            "events": append_event(state, "micro_judge", f"步骤 {name} 达标", quality=quality),
        }

    used = state.get("micro_budget_used", 0)
    cap = state.get("micro_budget_current", 1)

    if used < cap:
        new_cap = cap
        if can_extend_micro_budget(state, name):
            new_cap = extend_micro_budget(state, name)
        return {
            **bump_loop(state),
            "micro_route": "retry_step",
            "micro_budget_current": new_cap,
            "events": append_event(
                state,
                "micro_judge",
                f"步骤 {name} 重试 ({used}/{new_cap})",
                failure_class=state.get("failure_class"),
            ),
        }

    # Budget exhausted for this step
    replan_used = state.get("replan_budget_used", 0)
    replan_max = state.get("replan_budget_max", 1)
    fc = state.get("failure_class")

    if fc in ("transient", "data_gap") and replan_used < replan_max:
        dead = list(state.get("dead_ends") or [])
        dead.append(
            {
                "step": name,
                "tool": step.get("tool"),
                "reason": state.get("last_tool_error") or "step budget exhausted",
                "failure_class": fc,
            }
        )
        return {
            **bump_loop(state),
            "micro_route": "replan",
            "replan_budget_used": replan_used + 1,
            "replan_used": replan_used + 1,
            "dead_ends": dead,
            "events": append_event(state, "micro_judge", f"步骤 {name} 触发重规划"),
        }

    msg = state.get("last_tool_error") or f"步骤「{step.get('label', name)}」未能完成"
    return {
        **bump_loop(state),
        "micro_route": "fail",
        "status": "failed",
        "user_error_message": msg,
        "failure_class": fc or "permanent",
        "events": append_event(state, "micro_judge", f"步骤 {name} 失败"),
    }
