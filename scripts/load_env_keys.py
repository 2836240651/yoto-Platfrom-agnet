"""Print KEY=value lines from repo .env for selected keys (for bat/for /f).

Usage:
  python scripts/load_env_keys.py DOUYIN_WORKER_TOKEN DOUYIN_WORKER_URL
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"


def load() -> dict[str, str]:
    out: dict[str, str] = {}
    if not ENV.is_file():
        return out
    for line in ENV.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> int:
    keys = [k for k in sys.argv[1:] if k]
    if not keys:
        print("usage: load_env_keys.py KEY [KEY...]", file=sys.stderr)
        return 2
    data = load()
    for k in keys:
        v = data.get(k, "")
        # bat-safe: no newlines
        v = v.replace("\r", "").replace("\n", "")
        print(f"{k}={v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
