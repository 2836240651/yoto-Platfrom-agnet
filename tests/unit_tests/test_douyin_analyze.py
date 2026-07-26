"""Unit tests for douyin analyze helpers (no live LLM)."""

from agent.tools import douyin_analyze
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


def test_compact_collect_preserves_query_lineage_for_llm_analysis():
    collect = {
        "video_hot": [{"word": "海夕鱼钩实战", "hot_level": 100}],
        "keywords": [
            {
                "word": "海夕鱼钩实战",
                "hot_level": 100,
                "side": "video",
                "bucket": "hot",
                "queried_term": "海夕鱼钩",
                "query_level": "explicit_expansion",
                "query_source": "fishing_gear_kb",
            }
        ],
    }

    rows = _compact_collect(collect)

    assert rows == [
        {
            "word": "海夕鱼钩实战",
            "hot_level": 100,
            "side": "video",
            "bucket": "hot",
            "queried_term": "海夕鱼钩",
            "query_level": "explicit_expansion",
            "query_source": "fishing_gear_kb",
        }
    ]


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


def test_llm_json_uses_ops_analysis_catalog_without_light_tier(monkeypatch):
    captured: dict[str, object] = {}

    class FakeResponse:
        content = '{"video_hot": []}'

    class FakeModel:
        def invoke(self, _messages):
            return FakeResponse()

    def fake_get_chat_model_for_state(state, **kwargs):
        captured["state"] = state
        captured["kwargs"] = kwargs
        return FakeModel()

    import agent.llm

    monkeypatch.setattr(agent.llm, "get_chat_model_for_state", fake_get_chat_model_for_state)

    result = douyin_analyze._llm_json(
        {"skill": "douyin-keyword-research"},
        task="ops_analysis",
        system="system",
        user="user",
    )

    assert result == {"video_hot": []}
    assert captured["kwargs"] == {"task": "ops_analysis"}


def test_llm_failure_preserves_real_mcp_words_without_claiming_completed_analysis(monkeypatch):
    collect = {
        "ok": True,
        "_meta": {"source": "mcp", "tool": "douyin_analyze_keywords"},
        "video_hot": [
            {"word": "video-one", "hot_level": 285000},
            {"word": "video-two", "hot_level": 134000},
        ],
        "product_hot": [{"word": "product-one", "hot_level": 98000}],
    }

    def unavailable_llm(*_args, **_kwargs):
        raise RuntimeError("503 model_not_found")

    monkeypatch.setattr(douyin_analyze, "_llm_json", unavailable_llm)

    result = douyin_analyze.analyze_and_optimize(
        {"seed": "seed", "include_video": True, "include_product": True},
        collect,
    )

    assert result["ok"] is False
    assert result["status"] == "analysis_unavailable"
    assert result["summary"] == {
        "keyword_count": 3,
        "video_sample_count": 2,
        "product_sku_count": 1,
        "p0_count": 2,
    }
    assert [card["keyword"] for card in result["categories"]["video_hot"]] == [
        "video-one",
        "video-two",
    ]
    assert [card["keyword"] for card in result["categories"]["product_hot"]] == ["product-one"]
    assert result["data_source"] == {
        "source": "mcp",
        "tool": "douyin_analyze_keywords",
        "provider": "chanmama",
        "mode": "analysis_unavailable",
    }
    assert "503 model_not_found" in result["error"]
    assert "规则回退" not in str(result)
