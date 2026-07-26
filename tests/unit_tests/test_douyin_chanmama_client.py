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


def test_normal_member_rows_drop_unrelated_search_results():
    product_rows = client.ChanmamaSession._product_rows(
        [
            {"title": "【试吃两枚】特大号无铅松花蛋70-80g大号海鸭蛋"},
            {"title": "海南琼珍酥皮月饼蛋黄豆蓉老字号"},
            {"title": "久岩升级版金海夕成品子线双钩"},
        ],
        term="海夕钩",
        level="explicit_expansion",
        source="fishing_gear_kb",
    )
    video_rows = client.ChanmamaSession._video_rows(
        [
            {
                "aweme_info": {"desc": "婚宴散场时我的高跟鞋里像灌了铅"},
                "product_info": {"title": "桥筏套装筏钓轮冬微铅缓降"},
            },
            {
                "aweme_info": {"desc": "筏钓轮微铅缓降实战演示"},
                "product_info": {"title": "桥筏套装"},
            },
        ],
        term="筏钓轮微铅",
        level="explicit_expansion",
        source="fishing_gear_kb",
    )

    assert [row["word"] for row in product_rows] == ["久岩升级版金海夕成品子线双钩"]
    assert [row["word"] for row in video_rows] == ["筏钓轮微铅缓降实战演示"]
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


def _session_with_ui(ui_search):
    session = _session_with_api(lambda _path, _params: {"errCode": 0, "data": {}})
    session._ui_search = ui_search
    return session


def test_collect_no_data_returns_safe_video_search_diagnostic():
    calls: list[tuple[str, str]] = []

    def ui_search(*, chain: str, term: str):
        calls.append((chain, term))
        return {"route": "aweme_search", "request": {"keyword": term}, "http_status": 200, "payload": {"errCode": 0, "data": {"list": []}}}

    result = _session_with_ui(ui_search).collect_hot_keywords("\u5927\u7269\u7aff", include_product=False)
    assert result["ok"] is False
    assert result["status"] == "no_data"
    assert result["diagnostics"][0]["queried_term"] == "\u5927\u7269\u7aff"
    assert result["diagnostics"][0]["err_code"] == 0
    assert result["diagnostics"][0]["raw_item_count"] == 0
    assert result["diagnostics"][0]["parsed_item_count"] == 0
    assert result["diagnostics"][0]["route"] == "aweme_search"
    assert calls == [("video", "\u5927\u7269\u7aff")]
def test_collect_explicit_query_plan_keeps_query_lineage_and_dimension():
    seen_terms: list[str] = []

    def ui_search(*, chain: str, term: str):
        seen_terms.append(term)
        return {"route": "aweme_search", "request": {"keyword": term}, "http_status": 200, "payload": {"errCode": 0, "data": {"list": [{"aweme_info": {"desc": f"{term}\u89c6\u9891", "digg_count": 100}}]}}}

    result = _session_with_ui(ui_search).collect_hot_keywords("\u5927\u7269\u7aff", include_product=False, query_plan=[{"term": "\u5de8\u7269\u7aff", "source": "operator_expansion", "query_dimension": "rod"}])
    assert seen_terms == ["\u5927\u7269\u7aff", "\u5de8\u7269\u7aff"]
    assert result["status"] == "ok"
    assert {(item["queried_term"], item["query_level"], item["query_source"]) for item in result["keywords"]} == {("\u5927\u7269\u7aff", "seed", "seed"), ("\u5de8\u7269\u7aff", "explicit_expansion", "operator_expansion")}
    expansion = next(item for item in result["keywords"] if item["queried_term"] == "\u5de8\u7269\u7aff")
    assert expansion["query_dimension"] == "rod"
    diagnostic = next(item for item in result["diagnostics"] if item["queried_term"] == "\u5de8\u7269\u7aff")
    assert diagnostic["query_dimension"] == "rod"
def test_collect_empty_product_search_is_no_data_with_diagnostic():
    def ui_search(*, chain: str, term: str):
        assert chain == "product"
        return {"route": "spu_search", "request": {"keyword": term}, "http_status": 200, "payload": {"errCode": 0, "data": {"list": []}}}

    result = _session_with_ui(ui_search).collect_hot_keywords("\u5927\u7269\u7aff", include_video=False)
    assert result["ok"] is False
    assert result["status"] == "no_data"
    assert result["diagnostics"][0]["queried_term"] == "\u5927\u7269\u7aff"
    assert result["diagnostics"][0]["route"] == "spu_search"
    assert result["diagnostics"][0]["err_code"] == 0
    assert result["diagnostics"][0]["raw_item_count"] == 0
    assert result["diagnostics"][0]["parsed_item_count"] == 0
    assert result["diagnostics"][0]["error"] is None
def test_collect_unexpected_video_search_error_is_upstream_error():
    def ui_search(*, chain: str, term: str):
        assert chain == "video"
        return {"route": "aweme_search", "request": {"keyword": term}, "http_status": 200, "payload": {"errCode": 50001, "errMsg": "service unavailable", "data": {}}}

    result = _session_with_ui(ui_search).collect_hot_keywords("\u5927\u7269\u7aff", include_product=False)
    assert result["status"] == "upstream_error"


def test_collect_uses_normal_member_product_and_video_ui_chains():
    session = _session_with_api(lambda _path, _params: {"errCode": 0, "data": {}})
    calls: list[tuple[str, str]] = []

    def ui_search(*, chain: str, term: str):
        calls.append((chain, term))
        if chain == "product":
            return {
                "route": "spu_search",
                "request": {"keyword": term, "page": "1", "sort": "duration_volume"},
                "http_status": 200,
                "payload": {
                    "errCode": 52000,
                    "data": {
                        "list": [
                            {
                                "title": "\u5927\u7269\u7aff\u4e3b\u529b\u6b3e",
                                "duration_volume": 1200,
                                "duration_author_count": 8,
                            }
                        ]
                    },
                },
            }
        return {
            "route": "aweme_search",
            "request": {"keyword": term, "page": "1", "sort": "auto"},
            "http_status": 200,
            "payload": {
                "errCode": 0,
                "data": {
                    "list": [
                        {
                            "aweme_info": {"aweme_title": "\u5927\u7269\u7aff\u5b9e\u6218", "digg_count": 88},
                            "product_info": {"title": "\u5927\u7269\u7aff"},
                        }
                    ]
                },
            },
        }

    session._ui_search = ui_search

    result = session.collect_hot_keywords("\u5927\u7269\u7aff")

    assert calls == [("video", "\u5927\u7269\u7aff"), ("product", "\u5927\u7269\u7aff")]
    assert result["status"] == "ok"
    assert {item["source_route"] for item in result["keywords"]} == {"aweme_search", "spu_search"}
    assert next(item for item in result["keywords"] if item["side"] == "video")["word"] == "\u5927\u7269\u7aff\u5b9e\u6218"
    product_diagnostic = next(item for item in result["diagnostics"] if item["route"] == "spu_search")
    assert product_diagnostic["err_code"] == 52000
    assert product_diagnostic["raw_item_count"] == 1
    assert product_diagnostic["parsed_item_count"] == 1
    assert product_diagnostic["error"] is None


def test_ui_response_match_requires_the_exact_keyword():
    url = "https://api-service.chanmama.com/v5/home/aweme/search?page=1&keyword=%E5%A4%A7%E7%89%A9%E7%AB%BF&sort=auto"

    assert client._matches_keyword_response(url, "/v5/home/aweme/search", "\u5927\u7269\u7aff")
    assert not client._matches_keyword_response(
        "https://api-service.chanmama.com/v5/home/aweme/search?page=1&keyword=&sort=digg_count",
        "/v5/home/aweme/search",
        "\u5927\u7269\u7aff",
    )
