"""Route user intent to a Skill."""

from __future__ import annotations

from pathlib import Path

from agent.config.settings import settings
from agent.state import AgentState

# Keyword routing until we add LLM-based intent classification.
SKILL_KEYWORDS: dict[str, list[str]] = {
    "temu-product-listing": ["temu", "店小秘", "上架", "批量上货", "肉机"],
    "douyin-keyword-research": ["抖音", "热搜", "潜力词", "渔具", "关键词"],
    "cross-border-listing": ["shopify", "amazon", "tiktok shop", "跨境"],
    "store-analytics": ["店铺", "运营", "gmv", "转化", "周报"],
}


def _load_skill_name(skill_id: str) -> str:
    skill_file = settings.skills_dir / skill_id / "SKILL.md"
    if skill_file.exists():
        return skill_id
    return "general"


def route_skill(state: AgentState) -> dict:
    """Pick a skill from the latest user message."""
    if state.get("skill"):
        return {"status": "planning"}

    messages = state.get("messages") or []
    if not messages:
        return {"skill": "general", "status": "planning"}

    last = messages[-1]
    content = getattr(last, "content", str(last)).lower()

    for skill_id, keywords in SKILL_KEYWORDS.items():
        if any(kw in content for kw in keywords):
            return {"skill": _load_skill_name(skill_id), "status": "planning"}

    return {"skill": "general", "status": "planning"}
