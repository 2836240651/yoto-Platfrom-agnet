"""Stub implementations keyed by logical tool name."""

from __future__ import annotations

from typing import Any, Callable

from agent.state import AgentState
from agent.tools import douyin_stub

StubFunc = Callable[[], dict[str, Any]]


def _collect(state: AgentState) -> StubFunc:
    seed = state.get("seed") or "渔具"
    days = state.get("date_range_days", 30)
    return lambda: douyin_stub.collect_hot_keywords(seed, date_range_days=days)


def _expand(state: AgentState) -> StubFunc:
    seed = state.get("seed") or "渔具"
    return lambda: douyin_stub.expand_suggest_words(seed, depth=2)


# logical tool → factory(state) -> callable stub
STUB_FACTORIES: dict[str, Callable[[AgentState], StubFunc]] = {
    "douyin_collect_hot_keywords": _collect,
    "douyin_expand_suggest_words": _expand,
}


def get_stub(logical: str, state: AgentState) -> StubFunc | None:
    factory = STUB_FACTORIES.get(logical)
    return factory(state) if factory else None
