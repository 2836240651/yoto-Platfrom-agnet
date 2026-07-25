"""Entry: tray UI by default; --headless for console loop."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure apps/meat-worker is on path (dev + frozen)
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

if getattr(sys, "frozen", False):
    os.environ.setdefault("MEAT_WORKER_DIR", str(Path(sys.executable).resolve().parent))
else:
    os.environ.setdefault("MEAT_WORKER_DIR", str(_HERE))


def main() -> int:
    if "--headless" in sys.argv or os.environ.get("MEAT_WORKER_HEADLESS") == "1":
        from worker_core import run_headless

        return run_headless()
    from ui.tray_app import main as tray_main

    return tray_main()


if __name__ == "__main__":
    raise SystemExit(main())
