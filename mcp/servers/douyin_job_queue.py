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
_CROSSBORDER_PLATFORMS = frozenset({"temu", "aliexpress"})
_SENSITIVE_KEY_PARTS = ("token", "cookie", "oauth", "authorization", "password", "secret")


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
    query_plan: list[dict[str, str]] | None = None,
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
            "query_plan": query_plan or [],
        },
        "worker_id": None,
        "result": None,
        "error": None,
    }
    path = _job_dir() / "pending" / f"{job_id}.json"
    with _LOCK:
        _write_json(path, job)
    return job


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]"
            if any(part in str(key).lower() for part in _SENSITIVE_KEY_PARTS)
            else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def enqueue_crossborder_sync(
    *,
    platform: str,
    account_ref: str,
    scope: str,
    date_start: str = "",
    date_end: str = "",
    force: bool = False,
) -> dict[str, Any]:
    normalized_platform = (platform or "").strip().lower()
    if normalized_platform not in _CROSSBORDER_PLATFORMS:
        raise ValueError(f"unsupported platform: {normalized_platform or 'empty'}")
    normalized_account_ref = (account_ref or "").strip()
    normalized_scope = (scope or "").strip().lower()
    if not normalized_account_ref:
        raise ValueError("account_ref is required")
    if not normalized_scope:
        raise ValueError("scope is required")
    job_id = uuid.uuid4().hex[:16]
    now = time.time()
    job = {
        "id": job_id,
        "type": "crossborder_sync",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "args": {
            "platform": normalized_platform,
            "account_ref": normalized_account_ref,
            "scope": normalized_scope,
            "date_start": (date_start or "").strip(),
            "date_end": (date_end or "").strip(),
            "force": bool(force),
        },
        "worker_id": None,
        "result": None,
        "error": None,
    }
    with _LOCK:
        _write_json(_job_dir() / "pending" / f"{job_id}.json", job)
    return job


def get_crossborder_sync(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        return {"ok": False, "error": f"job not found: {job_id}"}
    if job.get("type") != "crossborder_sync":
        return {"ok": False, "error": f"not a crossborder job: {job_id}"}
    args = job.get("args") if isinstance(job.get("args"), dict) else {}
    status = str(job.get("status") or "")
    return {
        "ok": status != "failed",
        "job_id": job.get("id"),
        "status": status,
        "platform": args.get("platform"),
        "account_ref": args.get("account_ref"),
        "scope": args.get("scope"),
        "result": _redact(job.get("result")),
        "error": job.get("error"),
    }


def crossborder_auth_status(*, platform: str = "", account_ref: str = "") -> dict[str, Any]:
    normalized_platform = (platform or "").strip().lower()
    if normalized_platform and normalized_platform not in _CROSSBORDER_PLATFORMS:
        return {"ok": False, "error": f"unsupported platform: {normalized_platform}"}
    workers = list_workers()
    online = [worker for worker in workers if worker.get("online")]
    states: list[dict[str, Any]] = []
    for worker in online:
        detail = worker.get("detail") if isinstance(worker.get("detail"), dict) else {}
        platforms = detail.get("platforms") if isinstance(detail.get("platforms"), dict) else {}
        if normalized_platform:
            state = platforms.get(normalized_platform)
            if isinstance(state, dict):
                states.append({"worker_id": worker.get("worker_id"), **_redact(state)})
    return {
        "ok": bool(online),
        "platform": normalized_platform or None,
        "account_ref": (account_ref or "").strip() or None,
        "workers": workers,
        "states": states,
        "need_worker": not bool(online),
    }


def claim_job(*, worker_id: str, job_types: list[str] | None = None) -> dict[str, Any] | None:
    wid = (worker_id or "肉机").strip() or "肉机"
    root = _job_dir()
    with _LOCK:
        pending = sorted((root / "pending").glob("*.json"), key=lambda p: p.stat().st_mtime)
        allowed = {str(job_type).strip() for job_type in job_types or [] if str(job_type).strip()}
        src = None
        job = None
        for candidate in pending:
            candidate_job = _read_json(candidate)
            if not candidate_job:
                candidate.unlink(missing_ok=True)
                continue
            if allowed and str(candidate_job.get("type") or "") not in allowed:
                continue
            src = candidate
            job = candidate_job
            break
        if src is None or job is None:
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
        job["result"] = result
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
            result = job.get("result")
            out = dict(result) if isinstance(result, dict) else {}
            out.update({
                "ok": False,
                "error": job.get("error") or out.get("error") or "??????",
                "job_id": job_id,
                "need_login": bool(out.get("need_login")),
            })
            return out
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
    query_plan: list[dict[str, str]] | None = None,
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
        query_plan=query_plan,
    )
    return wait_job(job["id"], timeout_s=timeout)
