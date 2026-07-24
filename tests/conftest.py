import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_API = _ROOT / "apps" / "api"
_SRC = _ROOT / "src"
for p in (_SRC, _API):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def disable_mcp_runtime_in_tests():
    """Keep graph/API tests fast and deterministic (use stub tools)."""
    from agent.config.settings import settings

    prev_enabled = settings.mcp_runtime_enabled
    settings.mcp_runtime_enabled = False
    yield
    settings.mcp_runtime_enabled = prev_enabled
