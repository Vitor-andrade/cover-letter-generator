"""Application settings, loaded from ``CLG_``-prefixed env vars.

The domain core stays framework-agnostic: settings are plain Pydantic and the
data directory (``~/.clg`` by default) is created with owner-only permissions so
the SQLite database is never world-readable. Provider API keys are supplied via
``CLG_<PROVIDER>_API_KEY`` env vars (e.g. in a git-ignored ``.env``).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    return Path.home() / ".clg"


class Settings(BaseSettings):
    """Runtime configuration.

    Every field can be overridden via an environment variable using the
    ``CLG_`` prefix (e.g. ``CLG_HOST``, ``CLG_AI_PROVIDER``).
    """

    model_config = SettingsConfigDict(env_prefix="CLG_", env_file=".env", extra="ignore")

    # --- server -----------------------------------------------------------
    host: str = "127.0.0.1"
    port: int = 0  # 0 => pick a free port at launch
    open_browser: bool = True

    # --- storage ----------------------------------------------------------
    data_dir: Path = Field(default_factory=_default_data_dir)

    # --- AI providers -----------------------------------------------------
    ai_provider: str = "ollama"
    default_language: str = "en"

    # --- provider API keys (bring-your-own, configured via env/.env) ------
    # Cloud providers read their key from these vars (e.g. CLG_ANTHROPIC_API_KEY).
    # An empty value means the provider is not configured and cannot be used.
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # --- derived paths ----------------------------------------------------
    @property
    def db_path(self) -> Path:
        return self.data_dir / "clg.db"

    def provider_api_key(self, name: str) -> str | None:
        """Return the configured API key for a cloud provider, or ``None``."""
        key = {
            "gemini": self.gemini_api_key,
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
        }.get(name.lower(), "")
        return key or None

    def ensure_data_dir(self) -> Path:
        """Create the data directory (owner-only, 0700) if it does not exist."""
        self.data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        # Tighten perms even if the directory pre-existed with looser bits.
        os.chmod(self.data_dir, 0o700)
        return self.data_dir


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
