"""Per-tenant Temu browser profile lock + lightweight session cache."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from app.config import resolve_profile_dir

LOCK_FILENAME = ".crosshub-profile.lock"
CACHE_FILENAME = ".crosshub-session.json"


def _lock_path(tenant_id: int) -> Path:
    return resolve_profile_dir(tenant_id) / LOCK_FILENAME


def _cache_path(tenant_id: int) -> Path:
    return resolve_profile_dir(tenant_id) / CACHE_FILENAME


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def read_profile_lock(tenant_id: int) -> dict[str, Any] | None:
    lock = _read_json(_lock_path(tenant_id))
    if not lock:
        return None
    pid = int(lock.get("pid") or 0)
    if pid > 0 and not _pid_alive(pid):
        clear_profile_lock(tenant_id)
        return None
    return lock


def is_profile_locked(tenant_id: int) -> bool:
    return read_profile_lock(tenant_id) is not None


def write_profile_lock(tenant_id: int, *, pid: int, role: str) -> None:
    _write_json(
        _lock_path(tenant_id),
        {
            "tenant_id": tenant_id,
            "pid": pid,
            "role": role,
            "updated_at": time.time(),
        },
    )


def clear_profile_lock(tenant_id: int) -> None:
    try:
        _lock_path(tenant_id).unlink(missing_ok=True)
    except Exception:
        pass


def write_session_cache(tenant_id: int, payload: dict[str, Any]) -> None:
    body = dict(payload)
    body["tenant_id"] = tenant_id
    body["cached_at"] = time.time()
    _write_json(_cache_path(tenant_id), body)


def read_session_cache(tenant_id: int, *, max_age_seconds: int = 300) -> dict[str, Any] | None:
    cached = _read_json(_cache_path(tenant_id))
    if not cached:
        return None
    cached_at = float(cached.get("cached_at") or 0)
    if cached_at <= 0 or (time.time() - cached_at) > max_age_seconds:
        return None
    return cached


def clear_session_cache(tenant_id: int) -> None:
    try:
        _cache_path(tenant_id).unlink(missing_ok=True)
    except Exception:
        pass


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(handle)
            return bool(ok) and exit_code.value == STILL_ACTIVE
        except Exception:
            return True
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
