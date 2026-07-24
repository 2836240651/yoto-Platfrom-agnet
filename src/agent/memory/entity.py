"""Entity (user/shop profile) memory — placeholder store."""

from __future__ import annotations

from typing import Any


class EntityStore:
    """Key-value entity profiles. Replace with SQL/Redis in production."""

    def __init__(self) -> None:
        self._entities: dict[str, dict[str, Any]] = {}

    def get(self, user_id: str) -> dict[str, Any]:
        return self._entities.get(user_id, {})

    def upsert(self, user_id: str, attributes: dict[str, Any]) -> None:
        current = self._entities.get(user_id, {})
        current.update(attributes)
        self._entities[user_id] = current


entity_store = EntityStore()
