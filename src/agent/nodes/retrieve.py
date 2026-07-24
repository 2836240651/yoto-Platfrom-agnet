"""Retrieve long-term memory context."""

from __future__ import annotations

from agent.state import AgentState


def retrieve_memory(state: AgentState) -> dict:
    """Placeholder: wire vector KB + episodic + entity stores here."""
    # TODO: semantic search, episodic lookup, entity profile
    return {
        "kb_context": state.get("kb_context") or [],
        "episodic_context": state.get("episodic_context") or [],
        "entity_context": state.get("entity_context") or {},
    }
