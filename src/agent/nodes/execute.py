"""Deprecated leftover from early draft graph — use act_tool_or_llm instead."""

from __future__ import annotations

from agent.state import AgentState


def execute_step(state: AgentState) -> dict:
    """Do not use. Kept only to avoid import breakage."""
    raise RuntimeError("execute_step is deprecated; graph uses act_tool_or_llm")
