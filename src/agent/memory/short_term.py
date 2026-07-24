"""Short-term session memory helpers."""

from __future__ import annotations

from langchain_core.messages import BaseMessage, trim_messages


def trim_session_messages(
    messages: list[BaseMessage],
    *,
    max_tokens: int = 4000,
) -> list[BaseMessage]:
    """Keep recent messages within token budget."""
    return trim_messages(messages, max_tokens=max_tokens, strategy="last")
