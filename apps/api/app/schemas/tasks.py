"""Pydantic schemas for task API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class TaskCreateRequest(BaseModel):
    skill: Literal[
        "douyin-keyword-research",
        "temu-product-listing",
        "social-media-publish",
    ] = "douyin-keyword-research"
    seed: str | None = Field(default=None, max_length=20)
    include_video: bool = True
    include_product: bool = True
    date_range_days: Literal[7, 30, 90] = 30
    shop_id: str | None = None
    excel_path: str | None = None
    agent_id: str | None = None
    platform: str = "temu"
    media_path: str | None = None
    platform_type: int | None = None
    account_list: list[str] | None = None
    title: str | None = None
    tags: list[str] | None = None
    # Explicit session pin; omit/null = catalog. Black-box skills strip before run.
    model_id: str | None = None

    @model_validator(mode="after")
    def _check_by_skill(self) -> TaskCreateRequest:
        from agent.constants import ALLOWED_MODEL_IDS, is_blackbox_skill, normalize_model_id

        mid = normalize_model_id(self.model_id)
        if is_blackbox_skill(self.skill):
            # Black-box: strip any model_id (invalid ids also ignored, no 400).
            self.model_id = None
        else:
            if mid is not None and mid not in ALLOWED_MODEL_IDS:
                raise ValueError(f"model_id not in allowlist: {mid}")
            self.model_id = mid

        if self.skill == "douyin-keyword-research":
            if not self.seed or not (1 <= len(self.seed.strip()) <= 20):
                raise ValueError("douyin-keyword-research 需要 1~20 字的 seed")
            self.seed = self.seed.strip()
        if self.skill == "temu-product-listing":
            if not self.shop_id or not self.shop_id.strip():
                raise ValueError("temu-product-listing 需要 shop_id")
            if not self.excel_path or not self.excel_path.strip():
                raise ValueError("temu-product-listing 需要 excel_path（先上传文件）")
            self.shop_id = self.shop_id.strip()
            self.excel_path = self.excel_path.strip()
            self.platform = (self.platform or "temu").strip() or "temu"
        if self.skill == "social-media-publish":
            if not self.media_path or not self.media_path.strip():
                raise ValueError("social-media-publish 需要 media_path（先上传素材）")
            if self.platform_type not in (1, 2, 3, 4, 5):
                raise ValueError("social-media-publish 需要 platform_type ∈ 1–5")
            if not self.account_list:
                raise ValueError("social-media-publish 需要 account_list")
            if not self.title or not self.title.strip():
                raise ValueError("social-media-publish 需要 title")
            self.media_path = self.media_path.strip()
            self.title = self.title.strip()
            self.account_list = [str(a).strip() for a in self.account_list if str(a).strip()]
            if not self.account_list:
                raise ValueError("social-media-publish 需要非空 account_list")
            self.tags = [str(t).strip() for t in (self.tags or []) if str(t).strip()]
        return self


class TaskProgress(BaseModel):
    step: int
    total_steps: int = 4
    step_name: str
    percent: int
    micro_attempt: int = 0
    micro_budget: int = 3
    replan_used: int = 0


class MetricItem(BaseModel):
    label: str
    value: str


class KeywordCard(BaseModel):
    keyword: str
    priority: Literal["P0", "P1", "P2"]
    trend: Literal["up", "flat", "down"]
    reason: str
    metrics: list[MetricItem]
    evidence: list[str]
    action: str


class AlertItem(BaseModel):
    type: Literal["info", "warn"]
    text: str


class DataSourceMeta(BaseModel):
    source: Literal["mcp", "stub", "stub_fallback"]
    tool: str | None = None
    resolved_tool: str | None = None
    mcp_error: str | None = None


class ReportSummary(BaseModel):
    keyword_count: int
    video_sample_count: int
    product_sku_count: int
    p0_count: int


class ReportCategories(BaseModel):
    video_hot: list[KeywordCard]
    video_potential: list[KeywordCard]
    product_hot: list[KeywordCard]
    product_potential: list[KeywordCard]


class DouyinTaskReport(BaseModel):
    kind: Literal["douyin_keyword"] = "douyin_keyword"
    summary: ReportSummary
    tags: list[str]
    alerts: list[AlertItem]
    categories: ReportCategories
    data_source: DataSourceMeta | None = None


class TemuListingReport(BaseModel):
    kind: Literal["temu_listing"] = "temu_listing"
    ok: bool
    status: Literal["processing", "success", "failed", "cancelled", "unknown"]
    message: str
    shop_id: str | None = None
    agent_id: str | None = None
    task_id: str | None = None
    data_source: DataSourceMeta | None = None


class SocialPublishReport(BaseModel):
    kind: Literal["social_publish"] = "social_publish"
    ok: bool
    status: Literal["pending", "running", "success", "failed", "unknown"]
    message: str
    job_id: str | None = None
    platform_type: int | None = None
    publish_runtime: str | None = None
    title: str | None = None
    account_list: list[str] = Field(default_factory=list)
    data_source: DataSourceMeta | None = None


TaskReport = DouyinTaskReport | TemuListingReport | SocialPublishReport


class TaskListItem(BaseModel):
    id: str
    seed: str | None = None
    skill: str = "douyin-keyword-research"
    title: str = ""
    status: Literal["pending", "running", "completed", "failed"]
    created_at: datetime
    completed_at: datetime | None = None


class TaskDetail(BaseModel):
    id: str
    skill: str = "douyin-keyword-research"
    seed: str | None = None
    status: Literal["pending", "running", "completed", "failed"]
    include_video: bool = True
    include_product: bool = True
    date_range_days: int = 30
    shop_id: str | None = None
    excel_path: str | None = None
    agent_id: str | None = None
    platform: str | None = None
    media_path: str | None = None
    platform_type: int | None = None
    account_list: list[str] | None = None
    title: str | None = None
    tags: list[str] | None = None
    model_id: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    progress: TaskProgress | None = None
    error_message: str | None = None
    report: DouyinTaskReport | TemuListingReport | SocialPublishReport | None = None
    debug: dict[str, Any] | None = None


class TaskListResponse(BaseModel):
    items: list[TaskListItem]
    total: int
