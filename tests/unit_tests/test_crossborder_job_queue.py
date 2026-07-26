"""Contracts for cross-border read-only worker jobs."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SERVERS = Path(__file__).resolve().parents[2] / "mcp" / "servers"
if str(SERVERS) not in sys.path:
    sys.path.insert(0, str(SERVERS))

import douyin_job_queue as queue  # noqa: E402


@pytest.fixture(autouse=True)
def job_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DOUYIN_JOB_DIR", str(tmp_path / "jobs"))


def test_crossborder_job_persists_only_safe_request_fields() -> None:
    job = queue.enqueue_crossborder_sync(
        platform="temu",
        account_ref="temu-main",
        scope="operational",
        date_start="2026-07-01",
        date_end="2026-07-26",
    )

    assert job["type"] == "crossborder_sync"
    assert job["args"] == {
        "platform": "temu",
        "account_ref": "temu-main",
        "scope": "operational",
        "date_start": "2026-07-01",
        "date_end": "2026-07-26",
        "force": False,
    }


def test_crossborder_rejects_unknown_platform() -> None:
    with pytest.raises(ValueError, match="unsupported platform"):
        queue.enqueue_crossborder_sync(
            platform="shopee",
            account_ref="store-1",
            scope="orders",
        )


def test_crossborder_status_redacts_sensitive_result_fields() -> None:
    job = queue.enqueue_crossborder_sync(
        platform="aliexpress", account_ref="ali-main", scope="operational"
    )
    assert queue.claim_job(worker_id="肉机")
    queue.complete_job(
        job_id=job["id"],
        worker_id="肉机",
        ok=True,
        result={
            "ok": True,
            "summary": {"rows": 12},
            "diagnostics": {"access_token": "secret", "cookie": "session"},
        },
    )

    status = queue.get_crossborder_sync(job["id"])

    assert status["ok"] is True
    assert status["result"]["summary"] == {"rows": 12}
    assert status["result"]["diagnostics"] == {"access_token": "[REDACTED]", "cookie": "[REDACTED]"}
