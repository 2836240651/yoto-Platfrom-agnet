from __future__ import annotations

import pytest

from app.services.douyin_reports import DouyinReportService, ReportNotAvailable


class FakeReader:
    def latest_report_date(self) -> str | None:
        return "20260722"

    def report_date_bounds(self) -> tuple[str | None, str | None]:
        return "20260622", "20260722"

    def count_store_days(self, start_date: str, end_date: str) -> int:
        assert (start_date, end_date) == ("20260722", "20260722")
        return 1

    def store_summary(self, start_date: str, end_date: str) -> dict[str, object] | None:
        assert (start_date, end_date) == ("20260722", "20260722")
        return {
            "imported_at": "2026-07-25 17:00:00",
            "user_payment_amount": "12888.50",
            "transaction_order_count": 86,
            "transaction_user_count": 73,
            "transaction_item_count": 94,
            "product_impression_count": 10000,
            "product_click_count": 500,
            "product_impression_click_rate": "0.05",
            "product_click_conversion_rate": "0.172",
            "refund_amount": "18.00",
            "refund_order_count": 1,
        }

    def top_products(self, start_date: str, end_date: str, limit: int) -> list[dict[str, object]]:
        assert (start_date, end_date) == ("20260722", "20260722")
        assert limit == 10
        return [
            {
                "product_id": "p-1",
                "product_name": "反底钓线组",
                "user_payment_amount": "100.50",
                "transaction_order_count": 3,
                "product_click_conversion_rate": "0.1",
            }
        ]

    def top_videos(self, statistics_period: str, limit: int) -> list[dict[str, object]]:
        assert statistics_period == "20260722-20260722"
        assert limit == 10
        return [
            {
                "video_id": "same-video",
                "video_title": "视频 A",
                "video_user_payment_amount": "50.00",
                "transaction_order_count": 2,
                "view_count": 1000,
                "completion_rate": "0.3",
            },
            {
                "video_id": "same-video",
                "video_title": "视频 B",
                "video_user_payment_amount": "40.00",
                "transaction_order_count": 1,
                "view_count": 900,
                "completion_rate": "0.2",
            },
        ]


class EmptyReader:
    def latest_report_date(self) -> None:
        return None

    def report_date_bounds(self) -> tuple[None, None]:
        return None, None


class RangeReader:
    def latest_report_date(self) -> str | None:
        return "20260722"

    def report_date_bounds(self) -> tuple[str | None, str | None]:
        return "20260622", "20260722"

    def count_store_days(self, start_date: str, end_date: str) -> int:
        assert (start_date, end_date) == ("20260716", "20260722")
        return 7

    def store_summary(self, start_date: str, end_date: str) -> dict[str, object] | None:
        assert (start_date, end_date) == ("20260716", "20260722")
        return {
            "user_payment_amount": "700.00",
            "transaction_order_count": 70,
            "transaction_user_count": 60,
            "transaction_item_count": 80,
            "product_impression_count": 1000,
            "product_click_count": 100,
            "refund_amount": "7.00",
            "refund_order_count": 2,
            "imported_at": "2026-07-25 17:00:00",
        }

    def top_products(self, start_date: str, end_date: str, limit: int) -> list[dict[str, object]]:
        assert (start_date, end_date, limit) == ("20260716", "20260722", 10)
        return [
            {
                "product_id": "p-7d",
                "product_name": "seven-day product",
                "user_payment_amount": "300.00",
                "transaction_order_count": 30,
                "product_click_conversion_rate": "0.3",
            }
        ]

    def top_videos(self, statistics_period: str, limit: int) -> list[dict[str, object]]:
        assert statistics_period == "20260716-20260722"
        assert limit == 10
        return []


class IncompleteRangeReader(RangeReader):
    def count_store_days(self, start_date: str, end_date: str) -> int:
        return 1


def test_dashboard_maps_real_report_fields_and_keeps_duplicate_video_ids() -> None:
    report = DouyinReportService(FakeReader()).get_dashboard("daily")

    assert report.available is True
    assert report.range == "day"
    assert report.data_as_of == "20260722"
    assert report.statistics_period == "20260722-20260722"
    assert report.video_statistics_period == "20260722-20260722"
    assert report.metrics.user_payment_amount == "12888.50"
    assert report.metrics.product_impression_click_rate == "0.0500000000"
    assert report.products[0].product_id == "p-1"
    assert [video.video_id for video in report.videos] == ["same-video", "same-video"]
    assert report.videos[0].completion_rate == "0.3"


def test_dashboard_returns_empty_state_when_no_daily_reports_exist() -> None:
    report = DouyinReportService(EmptyReader()).get_dashboard("day")

    assert report.available is False
    assert report.metrics is None
    assert report.empty_message == "暂无可用的抖音日报数据。"


def test_dashboard_aggregates_a_complete_seven_day_window() -> None:
    report = DouyinReportService(RangeReader()).get_dashboard("7d", end_date="20260722")

    assert report.available is True
    assert report.range == "7d"
    assert report.start_date == "20260716"
    assert report.data_as_of == "20260722"
    assert report.metrics is not None
    assert report.metrics.user_payment_amount == "700.00"
    assert report.metrics.product_impression_click_rate == "0.1000000000"
    assert report.metrics.product_click_conversion_rate == "0.8000000000"
    assert report.products[0].product_id == "p-7d"
    assert report.videos == []


def test_dashboard_returns_empty_state_when_a_range_is_incomplete() -> None:
    report = DouyinReportService(IncompleteRangeReader()).get_dashboard("7d", end_date="20260722")

    assert report.available is False
    assert report.metrics is None
    assert report.products == []
    assert report.videos == []
