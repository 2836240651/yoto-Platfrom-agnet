"""Regression tests for lineage retained in LLM analysis input."""

from agent.tools.douyin_analyze import _compact_collect


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
