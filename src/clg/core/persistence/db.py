"""SQLite engine, schema creation, and session management.

A single local SQLite file at ``~/.clg/clg.db`` (configurable). The database file
is created with owner-only permissions to match the privacy posture of the data
directory.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, text
from sqlmodel import Session, SQLModel, create_engine

from clg.core.config import get_settings

# Importing models registers them on SQLModel.metadata for create_all().
from clg.core.persistence import models as _models  # noqa: F401


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    settings.ensure_data_dir()
    db_path = settings.db_path
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    return engine


def _ensure_profile_sections_column(engine: Engine) -> None:
    """Add ``profile.sections`` to a pre-existing DB.

    ``create_all`` only creates missing tables — it never alters an existing one,
    so databases created before the structured-sections feature lack the column.
    Idempotent: guarded by ``PRAGMA table_info`` so it is a no-op once present.
    """
    with engine.begin() as conn:
        columns = {row[1] for row in conn.execute(text("PRAGMA table_info(profile)"))}
        if "sections" not in columns:
            conn.execute(text("ALTER TABLE profile ADD COLUMN sections JSON"))


def init_db() -> None:
    """Create tables if missing, apply lightweight migrations, and lock the DB file."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    _ensure_profile_sections_column(engine)
    db_path = get_settings().db_path
    if db_path.exists():
        os.chmod(db_path, 0o600)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional session, committing on success and rolling back on error."""
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
