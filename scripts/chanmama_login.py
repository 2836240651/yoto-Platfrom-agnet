#!/usr/bin/env python3
"""Open headed Chromium with Chanmama profile for QR/password login.

Usage:
  python scripts/chanmama_login.py

Env:
  DOUYIN_CHROME_USER_DATA_DIR  (optional; default .local/chanmama-chrome)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp" / "servers"))

from douyin_chanmama_client import interactive_login, profile_dir  # noqa: E402


def main() -> int:
    print("蝉妈妈登录窗口即将打开…")
    print(f"Profile: {profile_dir()}")
    print("请在浏览器中完成扫码/密码登录；登录成功后本脚本会自动退出。")
    result = interactive_login(timeout_sec=420)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("logged_in") else 1


if __name__ == "__main__":
    raise SystemExit(main())
