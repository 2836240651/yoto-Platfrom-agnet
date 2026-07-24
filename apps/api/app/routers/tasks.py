import app.bootstrap  # noqa: F401

import re
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile

from agent.config.settings import settings
from app.schemas.tasks import TaskCreateRequest, TaskDetail, TaskListResponse
from app.services.langgraph_runner import create_task_record, merge_live_detail, run_task_async
from app.store.task_store import task_store

router = APIRouter(prefix="/tasks", tags=["tasks"])

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._\u4e00-\u9fff-]+")


def _upload_root() -> Path:
    """Shared with platform-mcp (same absolute path in API + gateway containers)."""
    root = Path(settings.upload_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_filename(name: str) -> str:
    base = Path(name or "upload.xlsx").name
    cleaned = _SAFE_NAME.sub("_", base).strip("._") or "upload.xlsx"
    if not cleaned.lower().endswith((".xlsx", ".xls")):
        cleaned = f"{cleaned}.xlsx"
    return cleaned[:180]


@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)) -> dict:
    """Store Excel under UPLOAD_ROOT for MCP gateway (same host path) to read."""
    raw_name = file.filename or "listing.xlsx"
    if not raw_name.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx / .xls")
    batch = uuid.uuid4().hex[:12]
    dest_dir = _upload_root() / batch
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / _safe_filename(raw_name)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    dest.write_bytes(content)
    # Keep absolute path identical for gateway container mount.
    excel_path = str(dest.resolve())
    return {
        "ok": True,
        "excel_path": excel_path,
        "filename": dest.name,
        "bytes": len(content),
        "upload_root": str(_upload_root().resolve()),
    }


@router.post("", response_model=TaskDetail, status_code=201)
async def create_task(body: TaskCreateRequest, background_tasks: BackgroundTasks) -> TaskDetail:
    record = create_task_record(
        skill=body.skill,
        seed=body.seed,
        include_video=body.include_video,
        include_product=body.include_product,
        date_range_days=body.date_range_days,
        shop_id=body.shop_id,
        excel_path=body.excel_path,
        agent_id=body.agent_id,
        platform=body.platform,
        model_id=body.model_id,
    )
    background_tasks.add_task(
        run_task_async,
        record.id,
        skill=record.skill,
        seed=record.seed,
        include_video=record.include_video,
        include_product=record.include_product,
        date_range_days=record.date_range_days,
        shop_id=getattr(record, "shop_id", None),
        excel_path=getattr(record, "excel_path", None),
        agent_id=getattr(record, "agent_id", None),
        platform=getattr(record, "platform", None),
        model_id=getattr(record, "model_id", None),
    )
    return task_store.to_detail(record)


@router.post("/temu-listing", response_model=TaskDetail, status_code=201)
async def create_temu_listing_task(
    background_tasks: BackgroundTasks,
    shop_id: str = Form(...),
    file: UploadFile = File(...),
    agent_id: str = Form(""),
    platform: str = Form("temu"),
    model_id: str = Form(""),
) -> TaskDetail:
    """One-shot: upload Excel + create temu-product-listing task.

    ``model_id`` accepted for API symmetry but stripped (black-box skill).
    """
    uploaded = await upload_excel(file)
    body = TaskCreateRequest(
        skill="temu-product-listing",
        shop_id=shop_id,
        excel_path=uploaded["excel_path"],
        agent_id=agent_id or None,
        platform=platform or "temu",
        model_id=model_id or None,
    )
    return await create_task(body, background_tasks)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> TaskListResponse:
    items, total = task_store.list_items(limit=limit, offset=offset)
    return TaskListResponse(items=items, total=total)


@router.get("/{task_id}", response_model=TaskDetail)
def get_task(task_id: str) -> TaskDetail:
    record = task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="任务不存在")
    return merge_live_detail(record)
