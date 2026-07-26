"""Fishing-gear taxonomy retrieval for explicit Douyin query planning."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_BROAD_TERMS = frozenset({"钓鱼", "渔具", "鱼竿"})
_ROOT = Path(__file__).resolve().parents[3]
_CATALOG_PATH = _ROOT / "knowledge" / "collections" / "fishing-gear" / "catalog.json"


def _normalized(value: str) -> str:
    return "".join(str(value or "").lower().split()).replace("杆", "竿").replace("勾", "钩")


@lru_cache(maxsize=1)
def _catalog() -> list[dict[str, Any]]:
    payload = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    entries: list[dict[str, Any]] = []
    for category in payload.get("categories") or []:
        category_name = str(category.get("name") or "")
        for entry in category.get("entries") or []:
            canonical = str(entry.get("canonical") or "").strip()
            if not canonical:
                continue
            aliases = [canonical, *[str(value).strip() for value in entry.get("aliases") or []]]
            entries.append(
                {
                    "category": category_name,
                    "canonical": canonical,
                    "aliases": [value for value in aliases if value],
                    "variants": [str(value).strip() for value in entry.get("variants") or [] if str(value).strip()],
                    "tags": [str(value).strip() for value in entry.get("tags") or [] if str(value).strip()],
                }
            )
    return entries


def _match(seed: str) -> tuple[dict[str, Any] | None, str]:
    needle = _normalized(seed)
    candidates: list[tuple[int, dict[str, Any], str]] = []
    for entry in _catalog():
        for alias in entry["aliases"]:
            normalized_alias = _normalized(alias)
            if normalized_alias and normalized_alias in needle:
                candidates.append((len(normalized_alias), entry, alias))
    if not candidates:
        return None, ""
    _, entry, alias = max(candidates, key=lambda item: item[0])
    return entry, alias


def plan_fishing_gear_queries(seed: str, *, max_expansions: int = 2) -> dict[str, Any]:
    """Resolve a gear seed into auditable, non-broad expansion terms.

    The collector always runs the exact seed. ``query_plan`` contains only
    additional terms from the local taxonomy and is safe to persist/log.
    """

    clean_seed = str(seed or "").strip()
    entry, matched_alias = _match(clean_seed)
    if not entry or _normalized(clean_seed) in {_normalized(term) for term in _BROAD_TERMS}:
        return {
            "matched": False,
            "category": "",
            "canonical": "",
            "matched_alias": "",
            "query_plan": [],
            "tags": [],
        }

    seed_key = _normalized(clean_seed)
    terms: list[tuple[str, str]] = []
    canonical = str(entry["canonical"])
    if _normalized(canonical) != seed_key:
        terms.append((canonical, "kb_canonical"))
    for variant in entry["variants"]:
        if _normalized(variant) != seed_key:
            terms.append((variant, "kb_narrow_variant"))

    seen = {seed_key}
    query_plan: list[dict[str, str]] = []
    for term, relation in terms:
        normalized_term = _normalized(term)
        if not normalized_term or normalized_term in seen or term in _BROAD_TERMS:
            continue
        seen.add(normalized_term)
        query_plan.append(
            {
                "term": term,
                "source": "fishing_gear_kb",
                "relation": relation,
                "matched_alias": matched_alias,
                "canonical": canonical,
            }
        )
        if len(query_plan) >= max(0, int(max_expansions)):
            break

    return {
        "matched": True,
        "category": entry["category"],
        "canonical": canonical,
        "matched_alias": matched_alias,
        "query_plan": query_plan,
        "tags": entry["tags"],
    }
