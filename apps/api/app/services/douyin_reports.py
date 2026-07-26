"""Read-only Douyin BOSS reporting service."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

from agent.config.settings import settings
from app.schemas.boss import (
    DouyinBossReport,
    DouyinProductRankItem,
    DouyinStoreMetrics,
    DouyinVideoRankItem,
)


class ReportNotAvailable(RuntimeError):
    """Raised when the reporting database cannot be read."""


class DouyinReportReader(Protocol):
    """Small read model boundary for BOSS report queries."""

    def latest_report_date(self) -> str | None: ...

    def report_date_bounds(self) -> tuple[str | None, str | None]: ...

    def count_store_days(self, start_date: str, end_date: str) -> int: ...

    def store_summary(self, start_date: str, end_date: str) -> dict[str, Any] | None: ...

    def top_products(
        self, start_date: str, end_date: str, limit: int
    ) -> list[dict[str, Any]]: ...

    def top_videos(self, statistics_period: str, limit: int) -> list[dict[str, Any]]: ...


_RANGE_DAYS = {"day": 1, "7d": 7, "30d": 30}
_LEGACY_RANGE_IDS = {"daily": "day", "weekly": "7d", "monthly": "30d"}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _integer(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _rate(numerator: Any, denominator: Any) -> str | None:
    if numerator is None or denominator is None:
        return None
    try:
        divisor = Decimal(str(denominator))
        if not divisor:
            return None
        return f"{Decimal(str(numerator)) / divisor:.10f}"
    except (InvalidOperation, ValueError):
        return None


def _parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y%m%d")
    except ValueError as exc:
        raise ValueError("end_date must use YYYYMMDD") from exc


class PyMySQLDouyinReportReader:
    """Parameterized read-only MySQL queries for the existing reporting tables."""

    def _connection(self):
        try:
            import pymysql
        except ImportError as exc:  # pragma: no cover - deployment dependency guard
            raise ReportNotAvailable("抖音运营数据驱动未安装") from exc

        if not all(
            (
                settings.boss_reports_db_host,
                settings.boss_reports_db_user,
                settings.boss_reports_db_password,
            )
        ):
            raise ReportNotAvailable("抖音运营数据连接尚未配置")

        return pymysql.connect(
            host=settings.boss_reports_db_host,
            port=settings.boss_reports_db_port,
            user=settings.boss_reports_db_user,
            password=settings.boss_reports_db_password,
            database=settings.boss_reports_db_name,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=settings.boss_reports_db_connect_timeout_s,
            read_timeout=settings.boss_reports_db_connect_timeout_s,
            write_timeout=settings.boss_reports_db_connect_timeout_s,
            autocommit=True,
        )

    def _fetch_one(self, sql: str, parameters: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, parameters)
                return cursor.fetchone()

    def latest_report_date(self) -> str | None:
        row = self._fetch_one("SELECT MAX(report_date) AS report_date FROM store_daily")
        return _text(row.get("report_date")) if row else None

    def report_date_bounds(self) -> tuple[str | None, str | None]:
        row = self._fetch_one(
            "SELECT MIN(report_date) AS start_date, MAX(report_date) AS end_date FROM store_daily"
        )
        if not row:
            return None, None
        return _text(row.get("start_date")), _text(row.get("end_date"))

    def count_store_days(self, start_date: str, end_date: str) -> int:
        row = self._fetch_one(
            """
            SELECT COUNT(DISTINCT report_date) AS day_count
            FROM store_daily
            WHERE report_date BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )
        return _integer(row.get("day_count")) if row else 0

    def store_summary(self, start_date: str, end_date: str) -> dict[str, Any] | None:
        return self._fetch_one(
            """
            SELECT SUM(user_payment_amount) AS user_payment_amount,
                   SUM(transaction_order_count) AS transaction_order_count,
                   SUM(transaction_user_count) AS transaction_user_count,
                   SUM(transaction_item_count) AS transaction_item_count,
                   SUM(product_impression_count) AS product_impression_count,
                   SUM(product_click_count) AS product_click_count,
                   SUM(refund_amount) AS refund_amount,
                   SUM(refund_order_count) AS refund_order_count,
                   MAX(imported_at) AS imported_at
            FROM store_daily
            WHERE report_date BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )

    def top_products(
        self, start_date: str, end_date: str, limit: int
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT product_id,
                   MAX(product_name) AS product_name,
                   SUM(user_payment_amount) AS user_payment_amount,
                   SUM(transaction_order_count) AS transaction_order_count,
                   CASE
                     WHEN SUM(product_click_count) > 0
                     THEN SUM(transaction_item_count) / SUM(product_click_count)
                     ELSE NULL
                   END AS product_click_conversion_rate
            FROM product_transaction_daily
            WHERE report_date BETWEEN %s AND %s
            GROUP BY product_id
            ORDER BY user_payment_amount DESC, product_id ASC
            LIMIT %s
        """
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (start_date, end_date, limit))
                return list(cursor.fetchall())

    def top_videos(self, statistics_period: str, limit: int) -> list[dict[str, Any]]:
        sql = """
            SELECT video_id, video_title, video_user_payment_amount,
                   transaction_order_count, view_count, completion_rate
            FROM video_daily
            WHERE statistics_period = %s
            ORDER BY video_user_payment_amount DESC, id ASC
            LIMIT %s
        """
        with self._connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (statistics_period, limit))
                return list(cursor.fetchall())


class DouyinReportService:
    """Maps selected daily reporting windows to the BOSS dashboard read model."""

    def __init__(self, reader: DouyinReportReader | None = None) -> None:
        self._reader = reader or PyMySQLDouyinReportReader()

    def get_dashboard(self, range_id: str = "day", end_date: str | None = None) -> DouyinBossReport:
        range_id = _LEGACY_RANGE_IDS.get(range_id, range_id)
        if range_id not in _RANGE_DAYS:
            raise ValueError(f"Unsupported report range: {range_id}")

        available_start_date, available_end_date = self._reader.report_date_bounds()
        latest_report_date = self._reader.latest_report_date()
        selected_end_date = end_date or latest_report_date
        if not selected_end_date:
            return self._empty_report(
                range_id,
                "暂无可用的抖音日报数据。",
                available_start_date,
                available_end_date,
            )

        end = _parse_date(selected_end_date)
        start = end - timedelta(days=_RANGE_DAYS[range_id] - 1)
        start_date = start.strftime("%Y%m%d")
        statistics_period = f"{start_date}-{selected_end_date}"
        if self._reader.count_store_days(start_date, selected_end_date) != _RANGE_DAYS[range_id]:
            return self._empty_report(
                range_id,
                "所选日期范围没有完整日报数据。",
                available_start_date,
                available_end_date,
                start_date,
                selected_end_date,
            )

        store = self._reader.store_summary(start_date, selected_end_date)
        if not store or store.get("user_payment_amount") is None:
            return self._empty_report(
                range_id,
                "所选日期范围暂无店铺运营数据。",
                available_start_date,
                available_end_date,
                start_date,
                selected_end_date,
            )

        metrics = DouyinStoreMetrics(
            user_payment_amount=_text(store.get("user_payment_amount")),
            transaction_order_count=_integer(store.get("transaction_order_count")),
            transaction_user_count=_integer(store.get("transaction_user_count")),
            transaction_item_count=_integer(store.get("transaction_item_count")),
            product_impression_count=_integer(store.get("product_impression_count")),
            product_click_count=_integer(store.get("product_click_count")),
            product_impression_click_rate=_rate(
                store.get("product_click_count"), store.get("product_impression_count")
            ),
            product_click_conversion_rate=_rate(
                store.get("transaction_item_count"), store.get("product_click_count")
            ),
            refund_amount=_text(store.get("refund_amount")),
            refund_order_count=_integer(store.get("refund_order_count")),
        )
        products = [
            DouyinProductRankItem(
                product_id=str(row["product_id"]),
                product_name=_text(row.get("product_name")),
                user_payment_amount=_text(row.get("user_payment_amount")),
                transaction_order_count=_integer(row.get("transaction_order_count")),
                product_click_conversion_rate=_text(row.get("product_click_conversion_rate")),
            )
            for row in self._reader.top_products(start_date, selected_end_date, limit=10)
        ]
        videos = [
            DouyinVideoRankItem(
                video_id=str(row["video_id"]),
                video_title=_text(row.get("video_title")),
                video_user_payment_amount=_text(row.get("video_user_payment_amount")),
                transaction_order_count=_integer(row.get("transaction_order_count")),
                view_count=_integer(row.get("view_count")),
                completion_rate=_text(row.get("completion_rate")),
            )
            for row in self._reader.top_videos(statistics_period, limit=10)
        ]
        return DouyinBossReport(
            available=True,
            range=range_id,
            data_as_of=selected_end_date,
            start_date=start_date,
            statistics_period=statistics_period,
            video_statistics_period=statistics_period if videos else None,
            available_start_date=available_start_date,
            available_end_date=available_end_date,
            imported_at=_text(store.get("imported_at")),
            metrics=metrics,
            products=products,
            videos=videos,
        )

    @staticmethod
    def _empty_report(
        range_id: str,
        message: str,
        available_start_date: str | None,
        available_end_date: str | None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> DouyinBossReport:
        return DouyinBossReport(
            available=False,
            empty_message=message,
            range=range_id,
            data_as_of=end_date or "",
            start_date=start_date,
            statistics_period=(f"{start_date}-{end_date}" if start_date and end_date else ""),
            available_start_date=available_start_date,
            available_end_date=available_end_date,
            metrics=None,
            products=[],
            videos=[],
        )
