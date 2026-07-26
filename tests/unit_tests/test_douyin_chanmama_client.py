"""Unit tests for Chanmama collect helpers (no live browser)."""

import sys
from pathlib import Path

_SERVERS = Path(__file__).resolve().parents[2] / "mcp" / "servers"
sys.path.insert(0, str(_SERVERS))

import douyin_chanmama_client as client  # noqa: E402


def test_seed_related():
    assert client._seed_related("渔具装备", "渔具")
    assert client._seed_related("路亚竿", "路亚")
    assert not client._seed_related("手机壳", "渔具")


def test_bridge_seeds_are_disabled_for_niche_terms():
    assert client.bridge_seeds("欧鲤钓") == []
    assert client.bridge_seeds("反底钓") == []


def test_normal_member_rows_drop_unrelated_search_results():
    product_rows = client.ChanmamaSession._product_rows(
        [
            {"title": "南美白虾1.65KG", "duration_volume": 500},
            {"title": "金海夕成品子线双钩", "duration_volume": 120},
        ],
        term="海夕钩",
        level="explicit_expansion",
        source="fishing_gear_kb",
    )
    video_rows = client.ChanmamaSession._video_rows(
        [
            {
                "aweme_info": {"aweme_title": "野钓鲤鱼实战", "digg_count": 88},
                "product_info": {"title": "金海夕成品子线双钩"},
            },
            {
                "aweme_info": {"aweme_title": "白虾做法", "digg_count": 99},
                "product_info": {"title": "南美白虾"},
            },
        ],
        term="海夕钩",
        level="explicit_expansion",
        source="fishing_gear_kb",
    )

    assert [row["word"] for row in product_rows] == ["金海夕成品子线双钩"]
    assert [row["word"] for row in video_rows] == ["野钓鲤鱼实战"]


def test_extract_and_dedupe():
    payload = {
        "list": [
            {"keyword": "渔具套装", "hot_value": 100},
            {"keyword": "渔具套装", "hot_value": 90},
            {"word": "碳素竿", "score": 50},
        ]
    }
    out: list = []
    client._extract_words_from_obj(payload, out, side="product", bucket="hot")
    deduped = client._dedupe(out)
    words = [x["word"] for x in deduped]
    assert "渔具套装" in words
    assert words.count("渔具套装") == 1
