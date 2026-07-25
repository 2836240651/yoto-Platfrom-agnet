"""Probe Temu Commander Agent + Douyin meat worker (dual hands on meat PC).

Reads DOUYIN_WORKER_* / COMMANDER_* from repo .env via load_env_keys when available.
Exit 0 only if Douyin worker is online and logged in (Temu Agent is advisory).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from load_env_keys import load
except ImportError:  # pragma: no cover
    def load() -> dict[str, str]:
        return {}


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _ensure_env() -> None:
    for k, v in load().items():
        if v and not os.environ.get(k):
            os.environ[k] = v


def _get_json(url: str, *, headers: dict[str, str], method: str = "GET", body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def probe_douyin() -> dict:
    base = _env("DOUYIN_WORKER_URL", "https://www.yoto.work/platform-mcp").rstrip("/")
    token = _env("DOUYIN_WORKER_TOKEN")
    if not token:
        return {"id": "douyin_meat_worker", "ok": False, "detail": "DOUYIN_WORKER_TOKEN missing"}
    try:
        st = _get_json(
            f"{base}/worker/status",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        ok = bool(st.get("ok")) and bool(st.get("logged_in"))
        detail = (
            f"online logged_in={st.get('logged_in')} nick={st.get('nickname') or '-'}"
            if ok
            else (st.get("error") or st.get("message") or "need_worker/need_login")
        )
        return {"id": "douyin_meat_worker", "ok": ok, "detail": detail, "raw": st}
    except Exception as exc:  # noqa: BLE001
        return {"id": "douyin_meat_worker", "ok": False, "detail": f"{type(exc).__name__}: {exc}"}


def probe_commander() -> dict:
    base = _env("COMMANDER_API_BASE", "https://www.yoto.work/api/v1").rstrip("/")
    token = _env("COMMANDER_ACCESS_TOKEN")
    agent = _env("COMMANDER_DEFAULT_AGENT_ID", "肉机") or "肉机"
    if not token:
        return {
            "id": "commander_agent",
            "ok": False,
            "detail": "COMMANDER_ACCESS_TOKEN missing (Temu hand optional for Douyin)",
        }
    try:
        payload = _get_json(
            f"{base}/agent/list",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
            body={},
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        items = data if isinstance(data, list) else list((data or {}).get("list") or [])
        match = next(
            (
                a
                for a in items
                if isinstance(a, dict)
                and str(a.get("name") or a.get("agentId") or a.get("id") or "") == agent
            ),
            None,
        )
        if match is None:
            return {"id": "commander_agent", "ok": False, "detail": f"agent {agent!r} not in list"}
        st = match.get("status")
        online = st is True or str(st).lower() in ("true", "1", "online", "on")
        return {
            "id": "commander_agent",
            "ok": online,
            "detail": f"{agent} {'online' if online else 'offline'}",
        }
    except Exception as exc:  # noqa: BLE001
        return {"id": "commander_agent", "ok": False, "detail": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    _ensure_env()
    probes = [probe_douyin(), probe_commander()]
    for p in probes:
        flag = "OK " if p.get("ok") else "FAIL"
        print(f"[{flag}] {p.get('id')}: {p.get('detail')}")
    # Douyin hand is required for keyword ops; Temu is advisory here.
    return 0 if probes[0].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
