"""Credential-safe contracts shared by all cross-border sync adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


READ_SCOPES = {
    "temu": frozenset({"operational", "sales", "activity_data"}),
    "aliexpress": frozenset({"operational", "orders", "violations"}),
}
SENSITIVE_KEY_PARTS = ("token", "cookie", "oauth", "authorization", "password", "secret")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]"
            if any(part in str(key).lower() for part in SENSITIVE_KEY_PARTS)
            else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


@dataclass(frozen=True)
class SyncRequest:
    platform: str
    account_ref: str
    scope: str
    date_start: str
    date_end: str
    force: bool

    @classmethod
    def from_args(
        cls, platform: str, account_ref: str, scope: str, args: dict[str, Any]
    ) -> "SyncRequest":
        normalized_platform = (platform or "").strip().lower()
        normalized_scope = (scope or "").strip().lower()
        if normalized_platform not in READ_SCOPES:
            raise ValueError(f"unsupported platform: {normalized_platform or 'empty'}")
        if normalized_scope not in READ_SCOPES[normalized_platform]:
            raise ValueError(f"unsupported scope for {normalized_platform}: {normalized_scope or 'empty'}")
        normalized_account_ref = (account_ref or "").strip()
        if not normalized_account_ref:
            raise ValueError("account_ref is required")
        return cls(
            platform=normalized_platform,
            account_ref=normalized_account_ref,
            scope=normalized_scope,
            date_start=str(args.get("date_start") or "").strip(),
            date_end=str(args.get("date_end") or "").strip(),
            force=bool(args.get("force")),
        )


def normalize_result(
    *, platform: str, account_ref: str, scope: str, payload: dict[str, Any]
) -> dict[str, Any]:
    safe = redact(payload)
    return {
        "ok": safe.get("ok", True) is not False,
        "platform": platform,
        "account_ref": account_ref,
        "scope": scope,
        "summary": safe.get("summary") if isinstance(safe.get("summary"), dict) else {},
        "diagnostics": safe.get("diagnostics") if isinstance(safe.get("diagnostics"), (dict, list)) else {},
        "need_login": bool(safe.get("need_login")),
        "error": safe.get("error"),
    }
