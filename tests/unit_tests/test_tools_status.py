"""Unit smoke for tools status schema (mocked; no live MCP/Commander)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.tools_status import ToolsStatusResponse, get_tools_status


@patch("app.services.tools_status.settings")
@patch("app.services.tools_status.mcp_runtime")
@patch("app.services.tools_status.httpx.Client")
@patch("app.services.tools_status._commander_token", return_value="test-token")
@patch("app.services.tools_status._default_agent", return_value="肉机")
def test_tools_status_shape(
    _mock_agent: MagicMock,
    _mock_token: MagicMock,
    mock_client_cls: MagicMock,
    mock_mcp: MagicMock,
    mock_settings: MagicMock,
) -> None:
    mock_settings.mcp_runtime_enabled = True
    mock_mcp.status.return_value = {"ok": True, "tool_count": 3, "error": ""}
    mock_mcp.available_tools.return_value = ["temu_listing_submit", "other"]

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "code": 0,
        "data": [{"name": "肉机", "status": True}],
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.post.return_value = mock_resp
    mock_client_cls.return_value = mock_client

    data = get_tools_status()
    assert isinstance(data, ToolsStatusResponse)
    assert len(data.probes) >= 2
    ids = {p.id for p in data.probes}
    assert "mcp_runtime" in ids
    assert "commander_agent" in ids
    assert "API Key" in data.note or "密钥" in data.note
    assert data.ok is True
    meat = next(p for p in data.probes if p.id == "commander_agent")
    assert meat.online is True
    mock_client.post.assert_called_once()
