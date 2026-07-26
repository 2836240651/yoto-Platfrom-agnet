from __future__ import annotations

import sys
from pathlib import Path

import pytest

WORKER = Path(__file__).resolve().parents[2] / "apps" / "meat-worker"
if str(WORKER) not in sys.path:
    sys.path.insert(0, str(WORKER))

from crossborder.contract import SyncRequest, normalize_result  # noqa: E402


def test_request_rejects_write_scope() -> None:
    with pytest.raises(ValueError, match="unsupported scope"):
        SyncRequest.from_args("temu", "temu-main", "write_inventory", {})


def test_result_redacts_nested_platform_secrets() -> None:
    result = normalize_result(
        platform="temu",
        account_ref="temu-main",
        scope="operational",
        payload={"summary": {"rows": 3}, "diagnostics": {"browser_oauth": "secret"}},
    )

    assert result["ok"] is True
    assert result["diagnostics"] == {"browser_oauth": "[REDACTED]"}
