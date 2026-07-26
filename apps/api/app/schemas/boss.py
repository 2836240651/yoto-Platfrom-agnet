"""BOSS platform reporting response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class DouyinStoreMetrics(BaseModel):
    user_payment_amount: str | None = None
    transaction_order_count: int | None = None
    transaction_user_count: int | None = None
    transaction_item_count: int | None = None
    product_impression_count: int | None = None
    product_click_count: int | None = None
    product_impression_click_rate: str | None = None
    product_click_conversion_rate: str | None = None
    refund_amount: str | None = None
    refund_order_count: int | None = None


class DouyinProductRankItem(BaseModel):
    product_id: str
    product_name: str | None = None
    user_payment_amount: str | None = None
    transaction_order_count: int | None = None
    product_click_conversion_rate: str | None = None


class DouyinVideoRankItem(BaseModel):
    video_id: str
    video_title: str | None = None
    video_user_payment_amount: str | None = None
    transaction_order_count: int | None = None
    view_count: int | None = None
    completion_rate: str | None = None


class DouyinBossReport(BaseModel):
    platform: str = "douyin"
    available: bool = True
    empty_message: str | None = None
    range: str = "day"
    period: str | None = None
    data_as_of: str
    start_date: str | None = None
    statistics_period: str = ""
    video_statistics_period: str | None = None
    available_start_date: str | None = None
    available_end_date: str | None = None
    imported_at: str | None = None
    metrics: DouyinStoreMetrics | None = None
    products: list[DouyinProductRankItem]
    videos: list[DouyinVideoRankItem]
