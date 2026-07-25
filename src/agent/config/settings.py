"""Application settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = ROOT


class Settings(BaseSettings):
    """Environment-backed settings."""

    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    # NewAPI / OpenAI-compatible gateway (shared default base).
    openai_api_base: str = "https://api.hyhacct.com/v1"
    # Legacy aliases → heavy tier (backward compatible).
    llm_model: str = "gpt-5.6-luna"
    # Heavy: complex ops analysis / plan writing.
    llm_heavy_api_key: str = ""
    llm_heavy_api_base: str = ""
    llm_heavy_model: str = "gpt-5.6-luna"
    # Light: summary / extract / intent / memory compress / format.
    llm_light_api_key: str = ""
    llm_light_api_base: str = ""
    llm_light_model: str = "agnes-2.0-flash"
    mcp_config_path: Path = ROOT / "config" / "mcp.json"
    tool_registry_path: Path = ROOT / "config" / "tool_registry.json"
    skills_dir: Path = ROOT / "skills"
    knowledge_dir: Path = ROOT / "knowledge"
    chroma_persist_dir: Path = ROOT / "knowledge" / "index" / "chroma"
    # Excel uploads for Temu MCP: must be the same absolute path the gateway can read.
    # Prod (API + platform-mcp同机): /data/platform-mcp/uploads
    upload_root: Path = ROOT / "uploads"

    max_loops: int = 15
    max_retries: int = 3

    agent_env: Literal["dev", "staging", "prod"] = "dev"
    mcp_runtime_enabled: bool = True
    mcp_allow_stub_fallback: bool | None = None
    mcp_write_token: str = ""
    douyin_chrome_user_data_dir: str = Field(
        default_factory=lambda: os.environ.get("DOUYIN_CHROME_USER_DATA_DIR", "")
    )
    # Commander (Temu black-box Job / agent online probe). Prefer .env via settings.
    commander_api_base: str = "https://www.yoto.work/api/v1"
    commander_access_token: str = ""
    commander_default_agent_id: str = "肉机"
    commander_default_platform: str = "temu"
    # Douyin meat worker probe (platform_mcp /worker/status). Same token as Worker.
    douyin_worker_url: str = "https://www.yoto.work/platform-mcp"
    douyin_worker_token: str = ""
    douyin_worker_id: str = "肉机"

    @model_validator(mode="after")
    def _derive_fallback(self) -> Settings:
        if self.mcp_allow_stub_fallback is None:
            # dev allows fallback; staging/prod forbid silent stub success on MCP failure
            object.__setattr__(
                self,
                "mcp_allow_stub_fallback",
                self.agent_env == "dev",
            )
        return self

    @property
    def allow_stub_fallback(self) -> bool:
        return bool(self.mcp_allow_stub_fallback)


settings = Settings()
