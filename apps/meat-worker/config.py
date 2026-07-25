"""Meat worker AppData config (Token never baked into EXE)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


APP_NAME = "agent-platform-meat"
DEFAULT_WORKER_URL = "https://www.yoto.work/platform-mcp"
DEFAULT_WORKER_ID = "肉机"


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_profile_dir() -> Path:
    path = app_data_dir() / "chanmama-chrome"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    # Prefer sidecar next to EXE for easy copy; fall back to AppData.
    sidecar = Path.cwd() / "config.json"
    if sidecar.is_file():
        return sidecar
    exe_dir = Path(os.environ.get("MEAT_WORKER_DIR") or "").strip()
    if exe_dir:
        p = Path(exe_dir) / "config.json"
        if p.is_file():
            return p
    return app_data_dir() / "config.json"


@dataclass
class MeatConfig:
    worker_url: str = DEFAULT_WORKER_URL
    worker_token: str = ""
    worker_id: str = DEFAULT_WORKER_ID
    poll_s: float = 3.0
    headed: bool = False
    chrome_user_data_dir: str = ""
    use_system_chrome: bool = True
    claim_enabled: bool = True

    def profile_dir(self) -> Path:
        raw = (self.chrome_user_data_dir or "").strip()
        if raw:
            path = Path(raw)
        else:
            path = default_profile_dir()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def apply_env(self) -> None:
        """Export settings so douyin_chanmama_client / worker see them."""
        os.environ["DOUYIN_WORKER_URL"] = (self.worker_url or DEFAULT_WORKER_URL).rstrip("/")
        os.environ["DOUYIN_WORKER_TOKEN"] = self.worker_token or ""
        os.environ["DOUYIN_WORKER_ID"] = self.worker_id or DEFAULT_WORKER_ID
        os.environ["DOUYIN_WORKER_POLL_S"] = str(self.poll_s)
        os.environ["DOUYIN_WORKER_HEADED"] = "1" if self.headed else "0"
        os.environ["DOUYIN_CHROME_USER_DATA_DIR"] = str(self.profile_dir())
        if self.use_system_chrome:
            os.environ.setdefault("DOUYIN_PW_CHANNEL", "chrome")
        elif "DOUYIN_PW_CHANNEL" in os.environ and not os.environ.get("DOUYIN_PW_CHANNEL"):
            os.environ.pop("DOUYIN_PW_CHANNEL", None)


def _from_mapping(data: dict[str, Any]) -> MeatConfig:
    return MeatConfig(
        worker_url=str(data.get("worker_url") or DEFAULT_WORKER_URL).rstrip("/"),
        worker_token=str(data.get("worker_token") or ""),
        worker_id=str(data.get("worker_id") or DEFAULT_WORKER_ID) or DEFAULT_WORKER_ID,
        poll_s=float(data.get("poll_s") or 3.0),
        headed=bool(data.get("headed", False)),
        chrome_user_data_dir=str(data.get("chrome_user_data_dir") or ""),
        use_system_chrome=bool(data.get("use_system_chrome", True)),
        claim_enabled=bool(data.get("claim_enabled", True)),
    )


def load_config() -> MeatConfig:
    # Env overrides for dev scripts
    cfg = MeatConfig(
        worker_url=(os.environ.get("DOUYIN_WORKER_URL") or DEFAULT_WORKER_URL).rstrip("/"),
        worker_token=os.environ.get("DOUYIN_WORKER_TOKEN") or "",
        worker_id=os.environ.get("DOUYIN_WORKER_ID") or DEFAULT_WORKER_ID,
        poll_s=float(os.environ.get("DOUYIN_WORKER_POLL_S") or 3),
        headed=(os.environ.get("DOUYIN_WORKER_HEADED") or "0").lower() in {"1", "true", "yes"},
        chrome_user_data_dir=os.environ.get("DOUYIN_CHROME_USER_DATA_DIR") or "",
        use_system_chrome=(os.environ.get("DOUYIN_PW_CHANNEL") or "chrome").lower()
        in {"chrome", "msedge", "1", "true", "yes", ""},
    )
    path = config_path()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                file_cfg = _from_mapping(data)
                # File wins for empty env token
                if not cfg.worker_token:
                    cfg.worker_token = file_cfg.worker_token
                if not os.environ.get("DOUYIN_WORKER_URL"):
                    cfg.worker_url = file_cfg.worker_url
                if not os.environ.get("DOUYIN_WORKER_ID"):
                    cfg.worker_id = file_cfg.worker_id
                if not os.environ.get("DOUYIN_WORKER_POLL_S"):
                    cfg.poll_s = file_cfg.poll_s
                if not os.environ.get("DOUYIN_WORKER_HEADED"):
                    cfg.headed = file_cfg.headed
                if not os.environ.get("DOUYIN_CHROME_USER_DATA_DIR"):
                    cfg.chrome_user_data_dir = file_cfg.chrome_user_data_dir
                cfg.use_system_chrome = file_cfg.use_system_chrome
                cfg.claim_enabled = file_cfg.claim_enabled
        except (OSError, json.JSONDecodeError):
            pass
    return cfg


def save_config(cfg: MeatConfig, *, path: Path | None = None) -> Path:
    target = path or config_path()
    # Prefer writing next to EXE when MEAT_WORKER_DIR set; else AppData.
    if path is None and not target.is_file():
        exe_dir = (os.environ.get("MEAT_WORKER_DIR") or "").strip()
        target = Path(exe_dir) / "config.json" if exe_dir else app_data_dir() / "config.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(cfg)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def ensure_sample_config() -> Path:
    path = app_data_dir() / "config.json"
    if not path.is_file():
        save_config(MeatConfig(), path=path)
    return path
