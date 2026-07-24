"""Episodic (task history) memory — placeholder store."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Episode:
    """One completed task summary."""

    task_id: str
    skill: str
    query: str
    summary: str
    outcome: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EpisodicStore:
    """In-memory episodic store. Replace with SQL in production."""

    def __init__(self) -> None:
        self._episodes: list[Episode] = []

    def add(self, episode: Episode) -> None:
        self._episodes.append(episode)

    def search(self, query: str, *, limit: int = 3) -> list[Episode]:
        q = query.lower()
        hits = [e for e in self._episodes if q in e.summary.lower() or q in e.query.lower()]
        return hits[:limit]


episodic_store = EpisodicStore()
