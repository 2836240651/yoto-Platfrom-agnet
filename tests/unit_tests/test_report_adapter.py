from app.services.report_adapter import _card


def test_keyword_card_adapter_preserves_query_lineage_dimension():
    card = _card(
        {
            "keyword": "\u6b27\u9ca4\u53cd\u5e95\u9493\u7ec4",
            "priority": "P0",
            "trend": "up",
            "reason": "\u771f\u5b9e\u91c7\u96c6\u7ed3\u679c",
            "metrics": [],
            "evidence": [],
            "action": "\u9a8c\u8bc1",
            "queried_term": "\u6b27\u9ca4\u53cd\u5e95\u9493\u7ec4",
            "query_level": "explicit_expansion",
            "query_source": "fishing_gear_kb",
            "query_dimension": "product",
        }
    )

    assert card.queried_term == "\u6b27\u9ca4\u53cd\u5e95\u9493\u7ec4"
    assert card.query_level == "explicit_expansion"
    assert card.query_source == "fishing_gear_kb"
    assert card.query_dimension == "product"
