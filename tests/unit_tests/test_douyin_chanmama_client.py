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
def test_bridge_seeds_do_not_implicitly_expand_niche_terms():
    assert client.bridge_seeds("欧鲤钓") == []
    assert client.bridge_seeds("反底钓") == []
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
def _session_with_api(api_get):
    session = object.__new__(client.ChanmamaSession)
    session.check_login = lambda: {"logged_in": True}
    session.api_get = api_get
    return session
def test_collect_no_data_returns_safe_relation_diagnostic():
    calls: list[tuple[str, dict]] = []
    def api_get(path: str, params: dict):
        calls.append((path, params))
        return {"errCode": 0, "data": {"aweme_keyword_relation_resp_list": []}}
    result = _session_with_api(api_get).collect_hot_keywords("\u5927\u7269\u7aff", include_product=False)
    assert result["ok"] is False
    assert result["status"] == "no_data"
    assert result["diagnostics"][0]["queried_term"] == "\u5927\u7269\u7aff"
    assert result["diagnostics"][0]["err_code"] == 0
    assert result["diagnostics"][0]["raw_item_count"] == 0
    assert result["diagnostics"][0]["parsed_item_count"] == 0
    assert calls == [("/v1/hot_search_analysis/relationWord", {"keyword": "\u5927\u7269\u7aff", "keyword_type": 1, "sort": "search_index", "orderBy": 1})]
def test_collect_explicit_query_plan_keeps_query_lineage():
    seen_terms: list[str] = []
    def api_get(path: str, params: dict):
        if path == "/v1/hot_search_analysis/relationWord":
            term = params["keyword"]
            seen_terms.append(term)
            return {"errCode": 0, "data": {"aweme_keyword_relation_resp_list": [{"keyword": f"{term}\u5173\u8054\u8bcd", "hot_value": 100}]}}
        return {"errCode": 0, "data": {"aweme_keyword_relation_resp_list": []}}
    result = _session_with_api(api_get).collect_hot_keywords("\u5927\u7269\u7aff", include_product=False, query_plan=[{"term": "\u5de8\u7269\u7aff", "source": "operator_expansion"}])
    assert seen_terms == ["\u5927\u7269\u7aff", "\u5de8\u7269\u7aff"]
    assert result["status"] == "ok"
    assert {(item["queried_term"], item["query_level"], item["query_source"]) for item in result["keywords"]} == {("\u5927\u7269\u7aff", "seed", "seed"), ("\u5de8\u7269\u7aff", "explicit_expansion", "operator_expansion")}
def test_collect_known_empty_relation_code_is_no_data_with_diagnostic():
    def api_get(_path: str, _params: dict):
        return {"errCode": 55006, "errMsg": "\u65e0\u76f8\u5173\u5173\u8054\u8bcd\uff01", "data": {}}
    result = _session_with_api(api_get).collect_hot_keywords("\u5927\u7269\u7aff", include_product=False)
    assert result["ok"] is False
    assert result["status"] == "no_data"
    assert result["diagnostics"][0]["queried_term"] == "\u5927\u7269\u7aff"
    assert result["diagnostics"][0]["err_code"] == 55006
    assert result["diagnostics"][0]["raw_item_count"] == 0
    assert result["diagnostics"][0]["parsed_item_count"] == 0
    assert result["diagnostics"][0]["error"] == "\u65e0\u76f8\u5173\u5173\u8054\u8bcd\uff01"
def test_collect_unexpected_relation_error_is_upstream_error():
    def api_get(_path: str, _params: dict):
        return {"errCode": 50001, "errMsg": "service unavailable", "data": {}}
    result = _session_with_api(api_get).collect_hot_keywords("\u5927\u7269\u7aff", include_product=False)
    assert result["status"] == "upstream_error"
