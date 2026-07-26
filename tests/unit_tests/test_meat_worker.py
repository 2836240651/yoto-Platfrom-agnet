"""Unit tests for meat-worker config + handler registry (no live network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

MW = Path(__file__).resolve().parents[2] / "apps" / "meat-worker"
sys.path.insert(0, str(MW))

from config import MeatConfig, config_path, save_config  # noqa: E402
from worker_core import MeatWorker, default_handlers  # noqa: E402


def test_default_handlers_include_douyin() -> None:
    h = default_handlers()
    assert "douyin_collect_hot_keywords" in h


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


def test_config_path_handles_unset_worker_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MEAT_WORKER_DIR", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))

    assert config_path() == tmp_path / "appdata" / "agent-platform-meat" / "config.json"
