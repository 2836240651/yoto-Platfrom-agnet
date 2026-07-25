"""Unit tests for Douyin meat-machine job queue."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def job_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("DOUYIN_JOB_DIR", str(tmp_path / "jobs"))
    monkeypatch.setenv("DOUYIN_WORKER_TOKEN", "test-token")
    monkeypatch.delenv("DOUYIN_WORKER_ALLOW_EMPTY_TOKEN", raising=False)
    import importlib
    import sys

    servers = Path(__file__).resolve().parents[2] / "mcp" / "servers"
    if str(servers) not in sys.path:
        sys.path.insert(0, str(servers))
    import douyin_job_queue as djq

    importlib.reload(djq)
    return tmp_path / "jobs"


def test_worker_token_auth(job_dir: Path) -> None:
    import douyin_job_queue as djq

    assert djq.worker_token_ok("Bearer test-token") is True
    assert djq.worker_token_ok("test-token") is True
    assert djq.worker_token_ok("Bearer wrong") is False
    assert djq.worker_token_ok(None) is False


def test_enqueue_claim_complete(job_dir: Path) -> None:
    import douyin_job_queue as djq

    job = djq.enqueue_collect(seed="渔具", date_range_days=7)
    assert job["status"] == "pending"
    claimed = djq.claim_job(worker_id="肉机")
    assert claimed is not None
    assert claimed["id"] == job["id"]
    assert claimed["status"] == "running"
    assert djq.claim_job(worker_id="肉机") is None

    result = {
        "ok": True,
        "seed": "渔具",
        "keywords": [{"word": "钓鱼", "hot_level": 1}],
        "count": 1,
    }
    out = djq.complete_job(
        job_id=job["id"], worker_id="肉机", ok=True, result=result
    )
    assert out["ok"] is True
    done = djq.get_job(job["id"])
    assert done is not None
    assert done["status"] == "done"
    assert done["result"]["seed"] == "渔具"


def test_auth_status_offline(job_dir: Path) -> None:
    import douyin_job_queue as djq

    status = djq.auth_status_summary()
    assert status["ok"] is False
    assert status["need_login"] is True


def test_auth_status_online_logged_in(job_dir: Path) -> None:
    import douyin_job_queue as djq

    djq.record_heartbeat(worker_id="肉机", logged_in=True, nickname="tester")
    status = djq.auth_status_summary()
    assert status["ok"] is True
    assert status["logged_in"] is True
    assert status["nickname"] == "tester"


def test_wait_job_timeout(job_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import douyin_job_queue as djq

    job = djq.enqueue_collect(seed="渔具")
    out = djq.wait_job(job["id"], timeout_s=0.2, poll_s=0.05)
    assert out["ok"] is False
    assert "超时" in (out.get("error") or "")
