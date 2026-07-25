"""Unit smoke for tools status schema (mocked; no live MCP/Commander)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.tools_status import ToolsStatusResponse, get_tools_status


@patch("app.services.tools_status.settings")
@patch("app.services.tools_status.mcp_runtime")
@patch("app.services.tools_status.httpx.Client")
@patch("app.services.tools_status._douyin_worker_token", return_value="dy-token")
@patch("app.services.tools_status._commander_token", return_value="test-token")
@patch("app.services.tools_status._default_agent", return_value="肉机")
def test_tools_status_shape(
    _mock_agent: MagicMock,
    _mock_token: MagicMock,
    _mock_dy_token: MagicMock,
    mock_client_cls: MagicMock,
    mock_mcp: MagicMock,
    mock_settings: MagicMock,
) -> None:
    mock_settings.mcp_runtime_enabled = True
    mock_settings.douyin_worker_url = "https://www.yoto.work/platform-mcp"
    mock_mcp.status.return_value = {"ok": True, "tool_count": 3, "error": ""}
    mock_mcp.available_tools.return_value = ["temu_listing_submit", "other"]

    mock_post = MagicMock()
    mock_post.raise_for_status = MagicMock()
    mock_post.json.return_value = {
        "code": 0,
        "data": [{"name": "肉机", "status": True}],
    }
    mock_get = MagicMock()
    mock_get.raise_for_status = MagicMock()
    mock_get.json.return_value = {
        "ok": True,
        "logged_in": True,
        "nickname": "test",
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.post.return_value = mock_post
    mock_client.get.return_value = mock_get
    mock_client_cls.return_value = mock_client

    data = get_tools_status()
    assert isinstance(data, ToolsStatusResponse)
    assert len(data.probes) >= 3
    ids = {p.id for p in data.probes}
    assert "mcp_runtime" in ids
    assert "commander_agent" in ids
    assert "douyin_meat_worker" in ids
    assert "API Key" in data.note or "密钥" in data.note
    assert data.ok is True
    meat = next(p for p in data.probes if p.id == "commander_agent")
    assert meat.online is True
    dy = next(p for p in data.probes if p.id == "douyin_meat_worker")
    assert dy.online is True
    mock_client.post.assert_called_once()
    mock_client.get.assert_called_once()


@patch("app.services.tools_status.settings")
@patch("app.services.tools_status.mcp_runtime")
@patch("app.services.tools_status.httpx.Client")
@patch("app.services.tools_status._douyin_worker_token", return_value="dy-token")
@patch("app.services.tools_status._commander_token", return_value="bad-token")
@patch("app.services.tools_status._default_agent", return_value="肉机")
def test_tools_status_ok_when_commander_down_douyin_up(
    _mock_agent: MagicMock,
    _mock_token: MagicMock,
    _mock_dy_token: MagicMock,
    mock_client_cls: MagicMock,
    mock_mcp: MagicMock,
    mock_settings: MagicMock,
) -> None:
    """Temu Agent is advisory; Douyin hand + MCP gate overall ok."""
    mock_settings.mcp_runtime_enabled = True
    mock_settings.douyin_worker_url = "https://www.yoto.work/platform-mcp"
    mock_mcp.status.return_value = {"ok": True, "tool_count": 3, "error": ""}
    mock_mcp.available_tools.return_value = ["temu_listing_submit"]

    mock_post = MagicMock()
    mock_post.raise_for_status.side_effect = Exception("401")
    mock_get = MagicMock()
    mock_get.raise_for_status = MagicMock()
    mock_get.json.return_value = {"ok": True, "logged_in": True, "nickname": "x"}
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.post.return_value = mock_post
    mock_client.get.return_value = mock_get
    mock_client_cls.return_value = mock_client

    data = get_tools_status()
    assert data.ok is True
    assert next(p for p in data.probes if p.id == "commander_agent").ok is False
    assert next(p for p in data.probes if p.id == "douyin_meat_worker").ok is True
