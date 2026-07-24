"""Background task runner — mock progress, later LangGraph."""

from __future__ import annotations

import asyncio
import uuid

from app.schemas.tasks import TaskProgress
from app.services.mock_report import build_mock_report
from app.store.task_store import TaskRecord, task_store

STEPS = [
    "采集数据",
    "扩展联想词",
    "打分分类",
    "生成报告",
]


async def run_task_async(
    task_id: str,
    *,
    seed: str,
    include_video: bool,
    include_product: bool,
    date_range_days: int,
) -> None:
    """Simulate agent pipeline with staged progress."""
    try:
        task_store.update(task_id, status="running")
        for i, step_name in enumerate(STEPS, start=1):
            percent = int(i / len(STEPS) * 100)
            task_store.update(
                task_id,
                progress=TaskProgress(
                    step=i,
                    total_steps=len(STEPS),
                    step_name=step_name,
                    percent=percent,
                ),
            )
            await asyncio.sleep(2)

        report = build_mock_report(
            seed,
            include_video=include_video,
            include_product=include_product,
        )
        from datetime import datetime, timezone

        task_store.update(
            task_id,
            status="completed",
            report=report,
            progress=TaskProgress(step=4, total_steps=4, step_name="完成", percent=100),
            completed_at=datetime.now(timezone.utc),
        )
    except Exception as exc:  # noqa: BLE001
        task_store.update(task_id, status="failed", error_message=str(exc))


def create_task_record(
    *,
    seed: str,
    include_video: bool,
    include_product: bool,
    date_range_days: int,
) -> TaskRecord:
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    record = TaskRecord(
        id=task_id,
        seed=seed,
        include_video=include_video,
        include_product=include_product,
        date_range_days=date_range_days,
        status="pending",
    )
    task_store.create(record)
    return record
