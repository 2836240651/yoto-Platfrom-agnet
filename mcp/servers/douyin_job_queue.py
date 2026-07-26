"""File-backed Douyin meat-machine job queue (server-side).

Jobs live under DOUYIN_JOB_DIR (default ./data/douyin-jobs).
Worker auth: DOUYIN_WORKER_TOKEN Bearer.
Never store Chanmama cookies here.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _job_dir() -> Path:
    raw = (os.environ.get("DOUYIN_JOB_DIR") or "").strip()
    path = Path(raw) if raw else Path(__file__).resolve().parent / "data" / "douyin-jobs"
    path.mkdir(parents=True, exist_ok=True)
    (path / "pending").mkdir(exist_ok=True)
    (path / "running").mkdir(exist_ok=True)
    (path / "done").mkdir(exist_ok=True)
    (path / "workers").mkdir(exist_ok=True)
    return path


_LOCK = threading.Lock()


def _worker_token_expired() -> bool:
    """Return whether the optional Worker token expiry has passed (fail closed)."""
    raw = (os.environ.get("DOUYIN_WORKER_TOKEN_EXPIRES_AT") or "").strip()
    if not raw:
        return False
    try:
        expires_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    return datetime.now(timezone.utc) >= expires_at.astimezone(timezone.utc)


def worker_token_ok(authorization: str | None) -> bool:
    expected = (os.environ.get("DOUYIN_WORKER_TOKEN") or "").strip()
    if not expected:
        # Fail closed in production; allow empty only if explicitly opted in
        if (os.environ.get("DOUYIN_WORKER_ALLOW_EMPTY_TOKEN") or "").strip() in {
            "1",
            "true",
            "yes",
        }:
            return True
        return False
    if _worker_token_expired():
        return False
    if not authorization:
        return False
    auth = authorization.strip()
    if auth.lower().startswith("bearer "):
        auth = auth[7:].strip()
    return auth == expected


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def record_heartbeat(
    *,
    worker_id: str,
    logged_in: bool | None = None,
    nickname: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wid = (worker_id or "肉机").strip() or "肉机"
    path = _job_dir() / "workers" / f"{wid}.json"
    payload = {
        "worker_id": wid,
        "ts": time.time(),
        "logged_in": logged_in,
        "nickname": (nickname or "")[:40] or None,
        "detail": detail or {},
    }
    with _LOCK:
        _write_json(path, payload)
    return {"ok": True, **payload}


def list_workers(*, max_age_s: float = 90.0) -> list[dict[str, Any]]:
    now = time.time()
    out: list[dict[str, Any]] = []
    workers = _job_dir() / "workers"
    for path in workers.glob("*.json"):
        data = _read_json(path)
        if not data:
            continue
        age = now - float(data.get("ts") or 0)
        data = dict(data)
        data["age_s"] = round(age, 1)
        data["online"] = age <= max_age_s
        out.append(data)
    out.sort(key=lambda x: (-float(x.get("ts") or 0), str(x.get("worker_id") or "")))
    return out


def auth_status_summary() -> dict[str, Any]:
    workers = list_workers()
    online = [w for w in workers if w.get("online")]
    logged = [w for w in online if w.get("logged_in") is True]
    if not online:
        return {
            "ok": False,
            "logged_in": False,
            "need_login": True,
            "error": "无在线肉机 Worker（请在本机启动 scripts/start-douyin-meat-worker.bat）",
            "workers": workers,
        }
    if not logged:
        return {
            "ok": False,
            "logged_in": False,
            "need_login": True,
            "error": "肉机在线但蝉妈妈未登录（请 python scripts/chanmama_login.py）",
            "workers": workers,
            "worker_id": online[0].get("worker_id"),
        }
    w = logged[0]
    return {
        "ok": True,
        "logged_in": True,
        "nickname": w.get("nickname"),
        "worker_id": w.get("worker_id"),
        "workers": workers,
    }


def enqueue_collect(
    *,
    seed: str,
    date_range_days: int = 30,
    include_video: bool = True,
    include_product: bool = True,
) -> dict[str, Any]:
    job_id = uuid.uuid4().hex[:16]
    now = time.time()
    job = {
        "id": job_id,
        "type": "douyin_collect_hot_keywords",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "args": {
            "seed": seed,
            "date_range_days": int(date_range_days),
            "include_video": bool(include_video),
            "include_product": bool(include_product),
        },
        "worker_id": None,
        "result": None,
        "error": None,
    }
    path = _job_dir() / "pending" / f"{job_id}.json"
    with _LOCK:
        _write_json(path, job)
    return job


def claim_job(*, worker_id: str) -> dict[str, Any] | None:
    wid = (worker_id or "肉机").strip() or "肉机"
    root = _job_dir()
    with _LOCK:
        pending = sorted((root / "pending").glob("*.json"), key=lambda p: p.stat().st_mtime)
        if not pending:
            return None
        src = pending[0]
        job = _read_json(src)
        if not job:
            src.unlink(missing_ok=True)
            return None
        job["status"] = "running"
        job["worker_id"] = wid
        job["updated_at"] = time.time()
        dest = root / "running" / src.name
        _write_json(dest, job)
        src.unlink(missing_ok=True)
        return job


def complete_job(
    *,
    job_id: str,
    worker_id: str,
    ok: bool,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    wid = (worker_id or "肉机").strip() or "肉机"
    root = _job_dir()
    with _LOCK:
        running = root / "running" / f"{job_id}.json"
        pending = root / "pending" / f"{job_id}.json"
        src = running if running.is_file() else pending if pending.is_file() else None
        if src is None:
            return {"ok": False, "error": f"job not found: {job_id}"}
        job = _read_json(src) or {"id": job_id}
        if job.get("worker_id") and job.get("worker_id") != wid:
            return {"ok": False, "error": "worker_id mismatch"}
        job["status"] = "done" if ok else "failed"
        job["updated_at"] = time.time()
        job["worker_id"] = wid
        job["result"] = result if ok else None
        job["error"] = None if ok else (error or "worker failed")
        dest = root / "done" / f"{job_id}.json"
        _write_json(dest, job)
        src.unlink(missing_ok=True)
        return {"ok": True, "job": job}


def get_job(job_id: str) -> dict[str, Any] | None:
    root = _job_dir()
    for folder in ("done", "running", "pending"):
        path = root / folder / f"{job_id}.json"
        data = _read_json(path)
        if data:
            return data
    return None


def wait_job(
    job_id: str,
    *,
    timeout_s: float = 240.0,
    poll_s: float = 1.0,
) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        job = get_job(job_id)
        if not job:
            return {"ok": False, "error": f"job disappeared: {job_id}"}
        status = job.get("status")
        if status == "done":
            result = job.get("result")
            if isinstance(result, dict):
                out = dict(result)
                out.setdefault("ok", True)
                out.setdefault("job_id", job_id)
                out.setdefault(
                    "data_source",
                    {
                        "source": "mcp",
                        "tool": "douyin_collect_hot_keywords",
                        "provider": "chanmama",
                        "worker_id": job.get("worker_id"),
                    },
                )
                return out
            return {"ok": True, "job_id": job_id, "result": result}
        if status == "failed":
            return {
                "ok": False,
                "error": job.get("error") or "肉机采集失败",
                "job_id": job_id,
                "need_login": False,
            }
        time.sleep(poll_s)
    return {
        "ok": False,
        "error": f"等待肉机超时（{int(timeout_s)}s），请确认 Worker 在线",
        "job_id": job_id,
        "need_worker": True,
    }


def collect_via_worker(
    seed: str,
    *,
    date_range_days: int = 30,
    include_video: bool = True,
    include_product: bool = True,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Enqueue + wait (MCP tool entry)."""
    auth = auth_status_summary()
    if not auth.get("ok"):
        return {
            "ok": False,
            "need_login": bool(auth.get("need_login")),
            "error": auth.get("error") or "肉机不可用",
            "workers": auth.get("workers") or [],
            "seed": seed,
        }
    timeout = float(
        timeout_s
        if timeout_s is not None
        else (os.environ.get("DOUYIN_JOB_TIMEOUT_S") or "240")
    )
    job = enqueue_collect(
        seed=seed,
        date_range_days=date_range_days,
        include_video=include_video,
        include_product=include_product,
    )
    return wait_job(job["id"], timeout_s=timeout)
