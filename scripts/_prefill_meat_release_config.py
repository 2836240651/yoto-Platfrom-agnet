"""Write release/config.json with DOUYIN_WORKER_TOKEN from repo .env."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from load_env_keys import load  # noqa: E402

REL = ROOT / "apps" / "meat-worker" / "release"
CFG_PATH = REL / "config.json"
EXAMPLE = ROOT / "apps" / "meat-worker" / "config.example.json"


def main() -> int:
    env = load()
    token = (env.get("DOUYIN_WORKER_TOKEN") or "").strip()
    if not token:
        print("WARN: DOUYIN_WORKER_TOKEN empty — writing blank config")
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["worker_token"] = token
    data["worker_url"] = (
        env.get("DOUYIN_WORKER_URL") or data.get("worker_url") or "https://www.yoto.work/platform-mcp"
    ).rstrip("/")
    data["worker_id"] = env.get("DOUYIN_WORKER_ID") or data.get("worker_id") or "闲置机-1"
    # Prefer existing Chanmama profile under repo .local (same as scripts/chanmama_login.py).
    profile = (env.get("DOUYIN_CHROME_USER_DATA_DIR") or "").strip()
    if not profile:
        profile = str(ROOT / ".local" / "chanmama-chrome")
    data["chrome_user_data_dir"] = profile
    CFG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", CFG_PATH, "token_set=", bool(token), "profile=", profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
