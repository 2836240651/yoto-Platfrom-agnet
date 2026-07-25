"""Unit tests for douyin analyze helpers (no live LLM)."""

from agent.tools.douyin_analyze import _compact_collect, _normalize_categories, format_heat


def test_compact_collect_caps_and_sorts():
    collect = {
        "keywords": [
            {"word": "a", "hot_level": 1, "side": "video"},
            {"word": "b", "hot_level": 100, "side": "video"},
            {"word": "c", "hot_level": 50, "side": "video"},
        ]
    }
    rows = _compact_collect(collect, limit=2)
    assert [r["word"] for r in rows] == ["b", "c"]


def test_normalize_categories_from_llm_shape():
    rows = [
        {"word": "鱼竿", "hot_level": 90000, "side": "video", "bucket": "hot"},
        {"word": "野钓", "hot_level": 30000, "side": "video", "bucket": "potential"},
    ]
    raw = {
        "video_hot": [{"keyword": "鱼竿", "priority": "P0", "reason": "热", "action": "拍一条测评"}],
        "video_potential": ["野钓"],
        "product_hot": [],
        "product_potential": [],
    }
    cats = _normalize_categories(
        "渔具", raw, rows, include_video=True, include_product=True
    )
    assert cats["video_hot"][0]["keyword"] == "鱼竿"
    metrics = {m["label"]: m["value"] for m in cats["video_hot"][0]["metrics"]}
    assert metrics["蝉妈妈热度"] == format_heat(90000)
    assert metrics["侧别"] == "视频内容"
    assert metrics["分层"] == "热搜"
    assert cats["video_potential"][0]["keyword"] == "野钓"


def test_normalize_drops_cross_side():
    rows = [{"word": "鱼钩", "hot_level": 10, "side": "product", "bucket": "hot"}]
    raw = {
        "video_hot": [{"keyword": "鱼钩", "priority": "P0", "reason": "x", "action": "y"}],
        "video_potential": [],
        "product_hot": [],
        "product_potential": [],
    }
    cats = _normalize_categories(
        "渔具", raw, rows, include_video=True, include_product=True
    )
    assert cats["video_hot"] == []
