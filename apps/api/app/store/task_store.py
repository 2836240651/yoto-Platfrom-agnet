"""In-memory task store."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.schemas.tasks import TaskDetail, TaskListItem, TaskProgress


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TaskRecord:
    id: str
    skill: str = "douyin-keyword-research"
    seed: str | None = None
    include_video: bool = True
    include_product: bool = True
    date_range_days: int = 30
    shop_id: str | None = None
    excel_path: str | None = None
    agent_id: str | None = None
    platform: str | None = None
    model_id: str | None = None
    status: str = "pending"
    created_at: datetime = field(default_factory=_utcnow)
    completed_at: datetime | None = None
    progress: TaskProgress | None = None
    error_message: str | None = None
    report: Any = None
    debug: dict[str, Any] | None = None

    @property
    def title(self) -> str:
        if self.skill == "temu-product-listing":
            return f"Temu {self.shop_id or '上架'}"
        return self.seed or "未命名"


class TaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}

    def create(self, record: TaskRecord) -> TaskRecord:
        self._tasks[record.id] = record
        return record

    def get(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def update(self, task_id: str, **kwargs) -> TaskRecord | None:
        record = self._tasks.get(task_id)
        if not record:
            return None
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record

    def list_items(self, *, limit: int = 20, offset: int = 0) -> tuple[list[TaskListItem], int]:
        records = sorted(self._tasks.values(), key=lambda r: r.created_at, reverse=True)
        total = len(records)
        page = records[offset : offset + limit]
        items = [
            TaskListItem(
                id=r.id,
                seed=r.seed,
                skill=r.skill,
                title=r.title,
                status=r.status,  # type: ignore[arg-type]
                created_at=r.created_at,
                completed_at=r.completed_at,
            )
            for r in page
        ]
        return items, total

    def to_detail(self, record: TaskRecord) -> TaskDetail:
        return TaskDetail(
            id=record.id,
            skill=record.skill,
            seed=record.seed,
            status=record.status,  # type: ignore[arg-type]
            include_video=record.include_video,
            include_product=record.include_product,
            date_range_days=record.date_range_days,
            shop_id=record.shop_id,
            excel_path=record.excel_path,
            agent_id=record.agent_id,
            platform=record.platform,
            model_id=record.model_id,
            created_at=record.created_at,
            completed_at=record.completed_at,
            progress=record.progress,
            error_message=record.error_message,
            report=record.report,
            debug=record.debug,
        )


task_store = TaskStore()
