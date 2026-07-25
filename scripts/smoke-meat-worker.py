"""Smoke: start meat worker headless briefly; require heartbeat OK (claim off)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "meat-worker"))
sys.path.insert(0, str(ROOT / "scripts"))

from load_env_keys import load  # noqa: E402
from config import MeatConfig  # noqa: E402
from worker_core import MeatWorker, default_handlers, setup_logging  # noqa: E402


def main() -> int:
    setup_logging()
    env = load()
    token = (env.get("DOUYIN_WORKER_TOKEN") or "").strip()
    url = (env.get("DOUYIN_WORKER_URL") or "https://www.yoto.work/platform-mcp").rstrip("/")
    if not token:
        print("SKIP: no DOUYIN_WORKER_TOKEN")
        return 0
    cfg = MeatConfig(
        worker_url=url,
        worker_token=token,
        worker_id="smoke-pack",
        poll_s=2,
        claim_enabled=False,
        use_system_chrome=True,
    )
    w = MeatWorker(cfg, handlers=default_handlers())
    w.set_claim_enabled(False)
    w.start()
    deadline = time.time() + 45
    ok = False
    while time.time() < deadline:
        if w.state.last_heartbeat_ok:
            ok = True
            break
        time.sleep(1)
    w.stop()
    print(
        "heartbeat_ok",
        ok,
        "login",
        w.state.login.get("logged_in"),
        "err",
        (w.state.last_error or "")[:120],
    )
    # Heartbeat to server is enough for pack smoke; login may fail headless without profile.
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
