"""Unit tests for social automedia MCP client (mocked HTTP)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SERVERS = Path(__file__).resolve().parents[2] / "mcp" / "servers"
if str(_SERVERS) not in sys.path:
    sys.path.insert(0, str(_SERVERS))

from social_automedia_client import (  # noqa: E402
    social_list_accounts,
    social_publish_status,
    social_publish_submit,
)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("SOCIAL_UPLOAD_API_BASE", "https://automedia.test")
    monkeypatch.setenv("SOCIAL_UPLOAD_TOKEN", "test-token")


def test_missing_token(monkeypatch):
    monkeypatch.delenv("SOCIAL_UPLOAD_TOKEN", raising=False)
    out = social_publish_submit(
        file_list=["a.mp4"],
        account_list=["acc.json"],
        platform_type=3,
        title="t",
    )
    assert out["ok"] is False
    assert "TOKEN" in out["error"]


def test_agent_required_response():
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.content = b"{}"
    mock_resp.json.return_value = {
        "code": 400,
        "msg": "TikTok 发布必须连接本机助手",
        "data": {"publish_runtime": "agent_required", "job_id": "j1"},
    }
    with patch("social_automedia_client.httpx.Client") as client_cls:
        client = MagicMock()
        client_cls.return_value.__enter__.return_value = client
        client.post.return_value = mock_resp
        out = social_publish_submit(
            file_list=["a.mp4"],
            account_list=["acc.json"],
            platform_type=5,
            title="tk",
        )
    assert out["ok"] is False
    assert out["publish_runtime"] == "agent_required"
    assert out["job_id"] == "j1"


def test_submit_and_status_success():
    submit_resp = MagicMock()
    submit_resp.status_code = 200
    submit_resp.content = b"{}"
    submit_resp.raise_for_status = MagicMock()
    submit_resp.json.return_value = {
        "code": 200,
        "msg": "ok",
        "data": {"publish_runtime": "local_queued", "job_id": "job-abc"},
    }
    status_resp = MagicMock()
    status_resp.status_code = 200
    status_resp.raise_for_status = MagicMock()
    status_resp.json.return_value = {
        "code": 200,
        "msg": "ok",
        "data": {
            "job_id": "job-abc",
            "status": "success",
            "runtime": "local_profile",
            "error": None,
            "platform_type": 3,
            "detail": {},
        },
    }
    with patch("social_automedia_client.httpx.Client") as client_cls:
        client = MagicMock()
        client_cls.return_value.__enter__.return_value = client
        client.post.return_value = submit_resp
        client.get.return_value = status_resp
        submitted = social_publish_submit(
            file_list=["a.mp4"],
            account_list=["acc.json"],
            platform_type=3,
            title="hello",
        )
        status = social_publish_status(job_id="job-abc")
    assert submitted["ok"] is True
    assert submitted["job_id"] == "job-abc"
    assert status["ok"] is True
    assert status["status"] == "success"


def test_list_accounts_ok():
    acc_resp = MagicMock()
    acc_resp.raise_for_status = MagicMock()
    acc_resp.json.return_value = {"code": 200, "data": [{"id": 1, "userName": "a"}]}
    agent_resp = MagicMock()
    agent_resp.raise_for_status = MagicMock()
    agent_resp.json.return_value = {"code": 200, "data": {"online": True, "agent_id": "x"}}
    with patch("social_automedia_client.httpx.Client") as client_cls:
        client = MagicMock()
        client_cls.return_value.__enter__.return_value = client
        client.get.side_effect = [acc_resp, agent_resp]
        out = social_list_accounts()
    assert out["ok"] is True
    assert out["agent_online"] is True
