"""Persistence: the one-time sections-column migration is safe and idempotent."""

from __future__ import annotations

from sqlalchemy import create_engine, text

from clg.core.persistence.db import _ensure_profile_sections_column


def _old_shape_engine(tmp_path):
    """An engine whose ``profile`` table predates the ``sections`` column."""
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE profile (id INTEGER PRIMARY KEY, name TEXT, "
                "background_text TEXT, source TEXT, created_at TEXT)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO profile (name, background_text, source, created_at) "
                "VALUES ('Ada', 'bg', 'manual', 'now')"
            )
        )
    return engine


def test_migration_adds_sections_column(tmp_path):
    engine = _old_shape_engine(tmp_path)
    _ensure_profile_sections_column(engine)
    with engine.begin() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(profile)"))}
        assert "sections" in cols
        # Existing rows are stranded at NULL — the legacy sentinel, no backfill.
        value = conn.execute(text("SELECT sections FROM profile WHERE name='Ada'")).scalar()
        assert value is None


def test_migration_is_idempotent(tmp_path):
    engine = _old_shape_engine(tmp_path)
    _ensure_profile_sections_column(engine)
    # Running again on an already-migrated DB must not raise.
    _ensure_profile_sections_column(engine)
    with engine.begin() as conn:
        names = [row[1] for row in conn.execute(text("PRAGMA table_info(profile)"))]
        assert names.count("sections") == 1
