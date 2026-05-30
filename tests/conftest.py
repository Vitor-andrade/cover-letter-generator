"""Shared fixtures — isolate each test run in a temp data dir, no network."""

from __future__ import annotations

from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch) -> Iterator[None]:
    """Point CLG at a throwaway data dir and the fake provider; reset caches."""
    monkeypatch.setenv("CLG_DATA_DIR", str(tmp_path / ".clg"))
    monkeypatch.setenv("CLG_AI_PROVIDER", "fake")

    # Settings and engine are cached singletons; clear them per test.
    from clg.core.config import get_settings
    from clg.core.persistence import db

    get_settings.cache_clear()
    db.get_engine.cache_clear()
    yield
    get_settings.cache_clear()
    db.get_engine.cache_clear()
