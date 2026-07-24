"""Validate report kinds."""

from agent.nodes.validate import _report_valid


def test_douyin_report_valid():
    report = {
        "kind": "douyin_keyword",
        "summary": {
            "keyword_count": 1,
            "video_sample_count": 1,
            "product_sku_count": 1,
            "p0_count": 1,
        },
        "tags": [],
        "alerts": [],
        "categories": {
            "video_hot": [],
            "video_potential": [],
            "product_hot": [],
            "product_potential": [],
        },
    }
    assert _report_valid(report)


def test_pipeline_kind_rejected():
    report = {
        "kind": "keyword_cards_pipeline",
        "summary": {"slug_count": 2, "ok": True, "deployed": False},
        "tags": [],
        "alerts": [],
        "pipeline": {"urls": {"feide": "https://x"}, "generated_paths": {}},
    }
    assert not _report_valid(report)
