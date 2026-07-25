import sys
from pathlib import Path


SERVERS_DIR = Path(__file__).resolve().parents[2] / "mcp" / "servers"
sys.path.insert(0, str(SERVERS_DIR))

from douyin_chanmama_client import ChanmamaSession, bridge_seeds


def test_niche_seed_has_no_implicit_parent_bridge():
    assert bridge_seeds("大物竿") == []


def test_empty_exact_query_reports_coverage_gap_without_parent_queries(monkeypatch):
    calls = []

    monkeypatch.setattr(
        ChanmamaSession,
        "check_login",
        lambda self: {"logged_in": True, "nickname": "test"},
    )

    def fake_api_get(self, path, params):
        calls.append((path, dict(params)))
        return {"errCode": 0, "data": {"aweme_keyword_relation_resp_list": []}}

    monkeypatch.setattr(ChanmamaSession, "api_get", fake_api_get)

    result = ChanmamaSession().collect_hot_keywords(
        "大物竿", include_video=True, include_product=False
    )

    assert result["ok"] is False
    assert result["coverage_state"] == "coverage_gap"
    assert result["fallback_used"] is False
    assert result["attempts"] == [
        {
            "term": "大物竿",
                "level": "seed",
            "route": "relation_word",
            "result_count": 0,
        }
    ]
    assert [params["keyword"] for _path, params in calls] == ["大物竿"]


def test_exact_candidates_keep_query_lineage_and_competition(monkeypatch):
    monkeypatch.setattr(
        ChanmamaSession,
        "check_login",
        lambda self: {"logged_in": True, "nickname": "test"},
    )

    def fake_api_get(self, path, params):
        if path.endswith("relationWord"):
            return {
                "errCode": 0,
                "data": {
                    "aweme_keyword_relation_resp_list": [
                        {
                            "keyword": "青鱼竿",
                            "search_index": 1200,
                            "competitive_index": 1.2,
                        }
                    ]
                },
            }
        return {"errCode": 0, "data": {"aweme_keyword_relation_resp_list": []}}

    monkeypatch.setattr(ChanmamaSession, "api_get", fake_api_get)

    result = ChanmamaSession().collect_hot_keywords(
        "大物竿", include_video=True, include_product=False
    )

    assert result["coverage_state"] == "exact_hit"
    candidate = result["keywords"][0]
    assert candidate["compete_index"] == 1.2
    assert candidate["queried_term"] == "大物竿"
    assert candidate["query_level"] == "seed"
    assert candidate["relation_to_seed"] == "exact_query_relation"
    assert candidate["source_route"] == "relation_word"
