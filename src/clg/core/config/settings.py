"""Application settings, loaded from ``CLG_``-prefixed env vars.

The domain core stays framework-agnostic: settings are plain Pydantic and the
data directory (``~/.clg`` by default) is created with owner-only permissions so
the SQLite database and the encrypted key files are never world-readable.
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

    # --- derived paths ----------------------------------------------------
    @property
    def db_path(self) -> Path:
        return self.data_dir / "clg.db"

    @property
    def master_key_path(self) -> Path:
        return self.data_dir / "master.key"

    @property
    def keys_path(self) -> Path:
        return self.data_dir / "keys.bin"

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
