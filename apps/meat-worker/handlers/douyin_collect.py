"""Douyin Chanmama collect handler (Playwright)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from config import MeatConfig


def _ensure_chanmama_path() -> None:
    # Dev: repo mcp/servers. Frozen: bundled next to package or _MEIPASS.
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", ""))
        candidates.append(meipass)
        candidates.append(meipass / "mcp" / "servers")
        candidates.append(Path(sys.executable).resolve().parent)
    here = Path(__file__).resolve()
    # apps/meat-worker/handlers -> repo root
    repo = here.parents[3] if len(here.parents) > 3 else here.parents[-1]
    candidates.append(repo / "mcp" / "servers")
    candidates.append(here.parents[1] / "vendor")
    for c in candidates:
        if c.is_dir() and (c / "douyin_chanmama_client.py").is_file():
            s = str(c)
            if s not in sys.path:
                sys.path.insert(0, s)
            return
    # last resort: already importable
    return


def _client():
    _ensure_chanmama_path()
    if getattr(sys, "frozen", False):
        try:
            from playwright_bootstrap import prepare_playwright_driver

            prepare_playwright_driver()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Playwright 驱动初始化失败: {exc}") from exc
    import douyin_chanmama_client as client  # noqa: WPS433

    return client


def check_login_status(*, headed: bool = False) -> dict[str, Any]:
    return _client().check_login(headed=headed)


def run_interactive_login(*, timeout_sec: int = 420) -> dict[str, Any]:
    return _client().interactive_login(timeout_sec=timeout_sec)


def handle_douyin_collect(job: dict[str, Any], cfg: "MeatConfig") -> dict[str, Any]:
    args = job.get("args") if isinstance(job.get("args"), dict) else {}
    seed = str(args.get("seed") or "").strip()
    if not seed:
        return {"ok": False, "error": "missing seed"}
    cfg.apply_env()
    result = _client().collect_hot_keywords(
        seed,
        date_range_days=int(args.get("date_range_days") or 30),
        include_video=bool(args.get("include_video", True)),
        include_product=bool(args.get("include_product", True)),
        headed=bool(cfg.headed),
    )
    if isinstance(result, dict):
        ds = result.setdefault("data_source", {})
        if isinstance(ds, dict):
            ds.setdefault("source", "mcp")
            ds.setdefault("tool", "douyin_collect_hot_keywords")
            ds.setdefault("provider", "chanmama")
            ds["worker_id"] = cfg.worker_id
    return result if isinstance(result, dict) else {"ok": False, "error": "non-dict result"}
