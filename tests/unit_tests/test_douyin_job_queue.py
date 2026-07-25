"""Unit tests for persisted Douyin meat-worker job results."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SERVERS = Path(__file__).resolve().parents[2] / "mcp" / "servers"
sys.path.insert(0, str(_SERVERS))

import douyin_job_queue as queue  # noqa: E402


@pytest.fixture(autouse=True)
def job_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("DOUYIN_JOB_DIR", str(tmp_path / "jobs"))


def test_failed_job_persists_and_returns_structured_diagnostics():
    job = queue.enqueue_collect(seed="大物竿")
    claimed = queue.claim_job(worker_id="肉机")
    assert claimed and claimed["id"] == job["id"]
    result = {
        "ok": False,
        "status": "no_data",
        "seed": "大物竿",
        "diagnostics": [{"route": "relation_word", "raw_item_count": 0}],
    }

    completed = queue.complete_job(
        job_id=job["id"], worker_id="肉机", ok=False, result=result, error="no data"
    )

    assert completed["ok"] is True
    stored = queue.get_job(job["id"])
    assert stored and stored["result"] == result
    waited = queue.wait_job(job["id"], timeout_s=0.01)
    assert waited["status"] == "no_data"
    assert waited["diagnostics"] == result["diagnostics"]
