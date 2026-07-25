"""LangGraph-backed task runner for M1.3."""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import app.bootstrap  # noqa: F401 — sys.path bootstrap

from agent.graph import build_graph
from app.schemas.tasks import TaskDetail
from app.services.report_adapter import (
    graph_status_to_api,
    state_to_debug,
    state_to_progress,
    state_to_task_report,
)
from app.store.task_store import TaskRecord, task_store

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph(with_checkpointer=True)
    return _graph


def _thread_config(task_id: str) -> dict:
    return {"configurable": {"thread_id": task_id}}


def _apply_state(task_id: str, state: dict[str, Any]) -> None:
    api_status = graph_status_to_api(state.get("status"))
    progress = state_to_progress(state)
    updates: dict[str, Any] = {
        "status": api_status,
        "progress": progress,
        "debug": state_to_debug(state),
    }

    if api_status == "failed":
        updates["error_message"] = state.get("user_error_message") or "分析未能完成，请稍后重试"

    if api_status == "completed":
        report = state_to_task_report(state)
        if report:
            updates["report"] = report
            updates["completed_at"] = datetime.now(timezone.utc)
            updates["progress"] = state_to_progress({**state, "status": "done"})

    task_store.update(task_id, **updates)


def merge_live_detail(record: TaskRecord) -> TaskDetail:
    """Merge in-memory record with live LangGraph checkpoint when still running."""
    if record.status not in ("pending", "running"):
        return task_store.to_detail(record)

    graph = get_graph()
    try:
        snap = graph.get_state(_thread_config(record.id))
        if snap and snap.values:
            state = dict(snap.values)
            detail = task_store.to_detail(record)
            api_status = graph_status_to_api(state.get("status"))
            return detail.model_copy(
                update={
                    "status": api_status,  # type: ignore[arg-type]
                    "progress": state_to_progress(state),
                    "error_message": state.get("user_error_message")
                    if api_status == "failed"
                    else None,
                    "report": state_to_task_report(state)
                    if api_status == "completed"
                    else detail.report,
                    "debug": state_to_debug(state),
                }
            )
    except Exception:
        pass
    return task_store.to_detail(record)


async def run_task_async(
    task_id: str,
    *,
    skill: str,
    seed: str | None,
    include_video: bool,
    include_product: bool,
    date_range_days: int,
    shop_id: str | None = None,
    excel_path: str | None = None,
    agent_id: str | None = None,
    platform: str | None = None,
    model_id: str | None = None,
    media_path: str | None = None,
    platform_type: int | None = None,
    account_list: list[str] | None = None,
    title: str | None = None,
    tags: list[str] | None = None,
) -> None:
    graph = get_graph()
    config = _thread_config(task_id)
    initial: dict[str, Any] = {
        "task_id": task_id,
        "skill": skill,
        "seed": seed or "",
        "include_video": include_video,
        "include_product": include_product,
        "date_range_days": date_range_days,
        "excel_path": excel_path or "",
        "shop_id": shop_id or "",
        "agent_id": agent_id or "",
        "platform": platform or "temu",
        "model_id": model_id,
        "media_path": media_path or "",
        "platform_type": int(platform_type or 0) or 3,
        "account_list": list(account_list or []),
        "title": title or "",
        "tags": list(tags or []),
        "skip_transient_sim": os.getenv("SIMULATE_TRANSIENT") != "1",
    }

    try:
        task_store.update(task_id, status="running")

        def _run() -> dict[str, Any]:
            last: dict[str, Any] = initial
            for chunk in graph.stream(initial, config, stream_mode="values"):
                last = chunk
                _apply_state(task_id, chunk)
            snap = graph.get_state(config)
            if snap and snap.values:
                return dict(snap.values)
            return last

        final = await asyncio.to_thread(_run)
        _apply_state(task_id, final)
    except Exception:
        task_store.update(
            task_id,
            status="failed",
            error_message="分析服务异常，请稍后重试",
        )


def create_task_record(
    *,
    skill: str = "douyin-keyword-research",
    seed: str | None = None,
    include_video: bool = True,
    include_product: bool = True,
    date_range_days: int = 30,
    shop_id: str | None = None,
    excel_path: str | None = None,
    agent_id: str | None = None,
    platform: str | None = None,
    model_id: str | None = None,
    media_path: str | None = None,
    platform_type: int | None = None,
    account_list: list[str] | None = None,
    title: str | None = None,
    tags: list[str] | None = None,
) -> TaskRecord:
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    record = TaskRecord(
        id=task_id,
        skill=skill,
        seed=seed,
        include_video=include_video,
        include_product=include_product,
        date_range_days=date_range_days,
        shop_id=shop_id,
        excel_path=excel_path,
        agent_id=agent_id,
        platform=platform,
        model_id=model_id,
        media_path=media_path,
        platform_type=platform_type,
        account_list=account_list,
        title=title,
        tags=tags,
        status="pending",
    )
    task_store.create(record)
    return record
