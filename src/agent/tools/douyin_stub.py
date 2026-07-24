"""Stub Douyin data tools for M1 loop testing."""

from __future__ import annotations

import random
from typing import Any


def collect_hot_keywords(seed: str, *, date_range_days: int = 30) -> dict[str, Any]:
    words = [
        f"{seed}装备",
        f"专业{seed}",
        f"{seed}推荐",
        f"入门{seed}",
        f"碳素{seed}",
    ]
    return {
        "ok": True,
        "seed": seed,
        "date_range_days": date_range_days,
        "keywords": [{"word": w, "hot_level": random.randint(50_000, 500_000)} for w in words],
        "count": len(words),
    }


def expand_suggest_words(seed: str, *, depth: int = 2) -> dict[str, Any]:
    base = [f"碳素{seed}", f"轻量化{seed}", f"{seed}套装", f"远投{seed}", f"入门{seed}推荐"]
    extra = [f"{seed}避坑", f"{seed}测评", f"平价{seed}"]
    words = (base + extra)[: 5 + depth]
    return {
        "ok": True,
        "seed": seed,
        "depth": depth,
        "suggest_words": words,
        "count": len(words),
    }


def score_keywords(
    seed: str,
    *,
    raw_keywords: list[str],
    include_video: bool,
    include_product: bool,
) -> dict[str, Any]:
    """Rule-based scoring for M1 (no LLM required)."""
    categories: dict[str, list[dict]] = {
        "video_hot": [],
        "video_potential": [],
        "product_hot": [],
        "product_potential": [],
    }

    for i, kw in enumerate(raw_keywords[:12]):
        card = {
            "keyword": kw,
            "priority": "P0" if i < 2 else "P1" if i < 5 else "P2",
            "trend": "up" if i % 3 != 1 else "flat",
            "reason": f"与「{seed}」相关，样本热度排名第 {i + 1}",
            "metrics": [
                {"label": "关联视频", "value": str(40 + i * 8)},
                {"label": "30天销量", "value": f"{1.0 + i * 0.3:.1f}万"},
                {"label": "增速", "value": f"+{20 + i * 5}%"},
            ],
            "evidence": ["stub 数据源", f"周期近30天"],
            "action": f"建议测试 #{kw} 话题内容",
        }
        if include_video and i % 2 == 0:
            bucket = "video_hot" if i < 4 else "video_potential"
            categories[bucket].append(card)
        if include_product and i % 2 == 1:
            bucket = "product_hot" if i < 4 else "product_potential"
            categories[bucket].append(card)

    if include_video and not categories["video_hot"]:
        categories["video_hot"].append(_fallback_card(seed, "P0"))
    if include_product and not categories["product_hot"]:
        categories["product_hot"].append(_fallback_card(f"{seed}套装", "P1"))

    all_cards = sum(categories.values(), [])
    p0 = sum(1 for c in all_cards if c["priority"] == "P0")
    return {
        "ok": True,
        "categories": categories,
        "summary": {
            "keyword_count": len(all_cards),
            "video_sample_count": 66 if include_video else 0,
            "product_sku_count": 44 if include_product else 0,
            "p0_count": max(p0, 1),
        },
        "tags": [f"种子词：{seed}", "周期：近30天", "数据源：stub"],
        "alerts": [
            {
                "type": "info",
                "text": f"「{seed}」为主赛道种子词，差异化请优先关注潜力词卡片。",
            },
            {
                "type": "warn",
                "text": "当前为 M1 stub 数据，接入真实 MCP 后结论将更准确。",
            },
        ],
    }


def _fallback_card(keyword: str, priority: str) -> dict:
    return {
        "keyword": keyword,
        "priority": priority,
        "trend": "up",
        "reason": "默认补充词",
        "metrics": [
            {"label": "关联视频", "value": "50"},
            {"label": "30天销量", "value": "1.0万"},
            {"label": "增速", "value": "+25%"},
        ],
        "evidence": ["stub"],
        "action": f"建议关注 #{keyword}",
    }
