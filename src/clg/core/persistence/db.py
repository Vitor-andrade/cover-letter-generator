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

from sqlalchemy import Engine
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


def init_db() -> None:
    """Create tables if missing and tighten the DB file permissions to 0600."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
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
