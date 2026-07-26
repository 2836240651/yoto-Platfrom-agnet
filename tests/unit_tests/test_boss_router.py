from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routers import boss
from app.schemas.boss import DouyinBossReport, DouyinStoreMetrics
from app.services.douyin_reports import ReportNotAvailable


def test_douyin_boss_route_returns_report() -> None:
    report = DouyinBossReport(
        period="daily",
        data_as_of="20260722",
        statistics_period="20260622-20260722",
        video_statistics_period="20260601-20260722",
        metrics=DouyinStoreMetrics(user_payment_amount="128.00"),
        products=[],
        videos=[],
    )
    service = MagicMock()
    service.get_dashboard.return_value = report

    with patch("app.routers.boss.DouyinReportService", return_value=service):
        assert boss.douyin_report("daily") == report


def test_douyin_boss_route_hides_database_error_details() -> None:
    service = MagicMock()
    service.get_dashboard.side_effect = ReportNotAvailable("password=secret")

    with patch("app.routers.boss.DouyinReportService", return_value=service):
        with pytest.raises(HTTPException) as exc_info:
            boss.douyin_report("daily")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "抖音运营数据暂不可用，请稍后重试"
