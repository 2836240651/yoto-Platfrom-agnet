"""Outbound Douyin meat-machine worker (dev CLI).

Prefer packaged EXE for ops hosts:
  apps/meat-worker → scripts/build-meat-worker.bat → dist/meat-worker/

Env (or AppData config.json):
  DOUYIN_WORKER_URL / TOKEN / ID / POLL_S / HEADED / CHROME_USER_DATA_DIR
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MW = ROOT / "apps" / "meat-worker"
if str(MW) not in sys.path:
    sys.path.insert(0, str(MW))

from worker_core import run_headless  # noqa: E402


def main() -> int:
    return run_headless()


if __name__ == "__main__":
    raise SystemExit(main())
