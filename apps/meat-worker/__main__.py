"""Entry: tray UI by default; --headless for console loop."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Bump when shipping a fixed release — appears in meat-worker.log for “which EXE”.
MEAT_WORKER_BUILD = "2026-07-25c-pw-tray"

# Ensure apps/meat-worker is on path (dev + frozen)
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

if getattr(sys, "frozen", False):
    os.environ.setdefault("MEAT_WORKER_DIR", str(Path(sys.executable).resolve().parent))
else:
    os.environ.setdefault("MEAT_WORKER_DIR", str(_HERE))


def _boot_log() -> None:
    """Log which binary/profile/driver is live (diagnose Downloads vs repo release)."""
    from worker_core import setup_logging

    setup_logging()
    log = logging.getLogger("meat_worker")
    exe = Path(sys.executable).resolve() if getattr(sys, "frozen", False) else Path(__file__).resolve()
    log.info("boot build=%s frozen=%s exe=%s", MEAT_WORKER_BUILD, getattr(sys, "frozen", False), exe)
    if getattr(sys, "frozen", False):
        try:
            from playwright_bootstrap import prepare_playwright_driver

            driver = prepare_playwright_driver()
            log.info("playwright driver ready: %s", driver)
        except Exception as exc:  # noqa: BLE001
            log.exception("playwright driver NOT ready: %s", exc)


def main() -> int:
    _boot_log()
    if "--headless" in sys.argv or os.environ.get("MEAT_WORKER_HEADLESS") == "1":
        from worker_core import run_headless

        return run_headless()
    from ui.tray_app import main as tray_main

    return tray_main()


if __name__ == "__main__":
    raise SystemExit(main())
