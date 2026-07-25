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


def test_bridge_seeds_for_niche():
    bridges = client.bridge_seeds("欧鲤钓")
    assert "鲤鱼" in bridges or "钓鱼" in bridges
    bridges2 = client.bridge_seeds("反底钓")
    assert "线组" in bridges2 or "钓鱼" in bridges2


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
