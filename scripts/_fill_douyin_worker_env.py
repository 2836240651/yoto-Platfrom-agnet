"""Upsert Douyin worker + deploy helper keys into local .env (never prints secrets)."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"

# Fixed non-secret defaults for this machine as meat-worker
DEFAULTS = {
    "DOUYIN_WORKER_URL": "https://www.yoto.work/platform-mcp",
    "DOUYIN_WORKER_ID": "肉机",
    "DOUYIN_WORKER_POLL_S": "3",
    "DEPLOY_HOST": "124.223.27.98",
    "DEPLOY_USER": "root",
}
TOKEN_TTL_DAYS = 30


def parse_env(text: str) -> list[tuple[str, str | None, str]]:
    """Return list of (kind, key, raw_line). kind in key|comment|blank|other."""
    rows: list[tuple[str, str | None, str]] = []
    for line in text.splitlines():
        raw = line
        s = line.strip()
        if not s:
            rows.append(("blank", None, raw))
            continue
        if s.startswith("#"):
            rows.append(("comment", None, raw))
            continue
        if "=" in s and not s.startswith("export "):
            k = s.split("=", 1)[0].strip()
            rows.append(("key", k, raw))
            continue
        rows.append(("other", None, raw))
    return rows


def get_value(text: str, key: str) -> str | None:
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        if k.strip() == key:
            return v.strip()
    return None


def upsert(text: str, updates: dict[str, str], comments_before: dict[str, str] | None = None) -> str:
    comments_before = comments_before or {}
    rows = parse_env(text)
    present = {k for kind, k, _ in rows if kind == "key" and k}
    out_lines: list[str] = []
    written: set[str] = set()

    for kind, key, raw in rows:
        if kind == "key" and key in updates:
            out_lines.append(f"{key}={updates[key]}")
            written.add(key)
        else:
            out_lines.append(raw)

    # append missing keys at end with optional section comment
    missing = [k for k in updates if k not in written]
    if missing:
        if out_lines and out_lines[-1].strip():
            out_lines.append("")
        out_lines.append("# --- Douyin meat worker / platform-mcp deploy (local secrets) ---")
        for k in missing:
            if k in comments_before:
                out_lines.append(comments_before[k])
            out_lines.append(f"{k}={updates[k]}")
    return "\n".join(out_lines).rstrip() + "\n"


def main() -> None:
    text = ENV.read_text(encoding="utf-8") if ENV.exists() else ""
    updates = dict(DEFAULTS)

    existing_token = get_value(text, "DOUYIN_WORKER_TOKEN")
    if existing_token:
        updates["DOUYIN_WORKER_TOKEN"] = existing_token
        token_action = "kept"
    else:
        updates["DOUYIN_WORKER_TOKEN"] = secrets.token_urlsafe(32)
        token_action = "generated"

    existing_expiry = get_value(text, "DOUYIN_WORKER_TOKEN_EXPIRES_AT")
    try:
        parsed_expiry = (
            datetime.fromisoformat((existing_expiry or "").replace("Z", "+00:00"))
            if existing_expiry
            else None
        )
        if parsed_expiry and parsed_expiry.tzinfo is None:
            parsed_expiry = parsed_expiry.replace(tzinfo=timezone.utc)
    except ValueError:
        parsed_expiry = None
    if parsed_expiry and parsed_expiry > datetime.now(timezone.utc):
        updates["DOUYIN_WORKER_TOKEN_EXPIRES_AT"] = parsed_expiry.astimezone(
            timezone.utc
        ).isoformat().replace("+00:00", "Z")
        expiry_action = "kept"
    else:
        updates["DOUYIN_WORKER_TOKEN_EXPIRES_AT"] = (
            datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        expiry_action = f"set_{TOKEN_TTL_DAYS}d"

    # Leave DEPLOY_PASS alone if set; otherwise add empty placeholder for user to fill
    deploy_pass = get_value(text, "DEPLOY_PASS")
    if deploy_pass is None:
        updates["DEPLOY_PASS"] = ""
        pass_action = "placeholder_empty"
    elif deploy_pass:
        pass_action = "kept"
    else:
        pass_action = "still_empty"

    comments = {
        "DOUYIN_WORKER_TOKEN": "# shared by meat worker + server platform-mcp (do not commit)",
        "DOUYIN_WORKER_TOKEN_EXPIRES_AT": "# UTC expiry enforced by platform-mcp; refresh before it expires",
        "DEPLOY_PASS": "# SSH password for DEPLOY_USER@DEPLOY_HOST (same as $env:P); do not commit",
    }
    new_text = upsert(text, updates, comments)
    ENV.write_text(new_text, encoding="utf-8")

    # redact report
    tok = updates["DOUYIN_WORKER_TOKEN"]
    print("updated", ENV)
    print("DOUYIN_WORKER_URL", updates["DOUYIN_WORKER_URL"])
    print("DOUYIN_WORKER_ID", updates["DOUYIN_WORKER_ID"])
    print("DOUYIN_WORKER_TOKEN", f"{token_action} len={len(tok)} prefix={tok[:4]}…")
    print("DOUYIN_WORKER_TOKEN_EXPIRES_AT", expiry_action)
    print("DEPLOY_HOST", updates["DEPLOY_HOST"])
    print("DEPLOY_USER", updates["DEPLOY_USER"])
    print("DEPLOY_PASS", pass_action)
    print("COMMANDER_ACCESS_TOKEN", "set" if get_value(new_text, "COMMANDER_ACCESS_TOKEN") else "missing")


if __name__ == "__main__":
    main()
