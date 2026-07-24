"""Terminal failure node — operator-safe message only."""

from __future__ import annotations

from agent.nodes.helpers import append_event
from agent.state import AgentState


def fail_terminal(state: AgentState) -> dict:
    msg = state.get("user_error_message") or "分析未能完成，请稍后重试"
    errors = list(state.get("errors") or [])
    if msg not in errors:
        errors.append(msg)
    return {
        "status": "failed",
        "user_error_message": msg,
        "errors": errors,
        "events": append_event(state, "fail_terminal", msg),
    }
