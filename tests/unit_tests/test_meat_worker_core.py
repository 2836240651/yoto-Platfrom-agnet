from __future__ import annotations

import sys
from pathlib import Path


MEAT_WORKER_DIR = Path(__file__).resolve().parents[2] / "apps" / "meat-worker"
if str(MEAT_WORKER_DIR) not in sys.path:
    sys.path.insert(0, str(MEAT_WORKER_DIR))

import worker_core
from config import MeatConfig


def test_complete_retries_transient_gateway_timeout(monkeypatch):
    worker = worker_core.MeatWorker(MeatConfig(worker_token="test-token"))
    calls: list[tuple[str, str, dict | None]] = []
    outcomes = [RuntimeError("timeout 20s /worker/complete"), {"ok": True}]

    def fake_request(method: str, path: str, body: dict | None = None):
        calls.append((method, path, body))
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    sleeps: list[float] = []
    monkeypatch.setattr(worker, "_request", fake_request)
    monkeypatch.setattr(worker_core.time, "sleep", sleeps.append)

    assert worker.complete(job_id="job-1", ok=True, result={"ok": True}) == {"ok": True}
    assert [(method, path) for method, path, _ in calls] == [
        ("POST", "/worker/complete"),
        ("POST", "/worker/complete"),
    ]
    assert sleeps == [1.0]
