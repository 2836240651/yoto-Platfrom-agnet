"""Unit tests for meat-worker config + handler registry (no live network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

MW = Path(__file__).resolve().parents[2] / "apps" / "meat-worker"
sys.path.insert(0, str(MW))

from config import MeatConfig, save_config  # noqa: E402
from worker_core import MeatWorker, default_handlers  # noqa: E402


def test_default_handlers_include_douyin() -> None:
    h = default_handlers()
    assert "douyin_collect_hot_keywords" in h
    assert "crossborder_sync" in h


def test_crossborder_handler_rejects_unsupported_platform() -> None:
    from handlers.crossborder_sync import handle_crossborder_sync

    result = handle_crossborder_sync(
        {"args": {"platform": "shopee", "account_ref": "store-1", "scope": "orders"}},
        MeatConfig(worker_token="t"),
    )

    assert result == {
        "ok": False,
        "need_login": False,
        "error": "unsupported platform: shopee",
    }


def test_claim_sends_supported_job_types(monkeypatch: pytest.MonkeyPatch) -> None:
    worker = MeatWorker(MeatConfig(worker_token="t"), handlers=default_handlers())
    calls: list[dict] = []

    def fake_request(method: str, path: str, body: dict | None = None):  # type: ignore[no-untyped-def]
        calls.append(body or {})
        return {"ok": True, "job": None}

    monkeypatch.setattr(worker, "_request", fake_request)
    worker.claim()

    assert calls == [{"worker_id": worker.cfg.worker_id, "job_types": ["crossborder_sync"]}]


def test_unknown_job_type_completes_false(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = MeatConfig(worker_token="t", worker_url="http://127.0.0.1:9", worker_id="t1")
    calls: list[dict] = []

    w = MeatWorker(cfg, handlers={})

    def fake_complete(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        return {"ok": True}

    monkeypatch.setattr(w, "complete", fake_complete)
    w.run_job({"id": "j1", "type": "nope", "args": {}})
    assert calls and calls[0]["ok"] is False
    assert "unknown" in (calls[0].get("error") or "")


def test_save_load_config_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "config.json"
    cfg = MeatConfig(worker_token="abc", worker_id="机-1", worker_url="https://example.test")
    save_config(cfg, path=path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["worker_token"] == "abc"
    assert data["worker_id"] == "机-1"


def test_idle_login_probe_stays_headless_when_task_browser_is_headed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import handlers.douyin_collect as douyin_collect

    seen: list[bool] = []
    monkeypatch.setattr(
        douyin_collect,
        "check_login_status",
        lambda *, headed: seen.append(headed) or {"logged_in": True},
    )
    worker = MeatWorker(MeatConfig(worker_token="t", headed=True))

    worker.refresh_login()

    assert seen == [False]
