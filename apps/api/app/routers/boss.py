"""Business-safe BOSS reporting endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.schemas.boss import DouyinBossReport
from app.services.douyin_reports import DouyinReportService, ReportNotAvailable

router = APIRouter(prefix="/boss", tags=["boss"])


@router.get("/douyin", response_model=DouyinBossReport)
def douyin_report(
    range: Literal["day", "7d", "30d"] = "day",
    end_date: str | None = Query(default=None, pattern=r"^\d{8}$"),
) -> DouyinBossReport:
    """Return a selected daily, seven-day, or thirty-day Douyin BOSS report."""
    try:
        return DouyinReportService().get_dashboard(range, end_date=end_date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="日期参数无效，请使用 YYYYMMDD") from exc
    except ReportNotAvailable as exc:
        raise HTTPException(
            status_code=503,
            detail="抖音运营数据暂不可用，请稍后重试",
        ) from exc
