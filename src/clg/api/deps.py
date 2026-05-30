"""FastAPI dependencies — request-scoped DB session and repository wiring."""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session

from clg.core.persistence.db import get_engine


def get_session() -> Iterator[Session]:
    """Yield a request-scoped session, committing on success, rolling back on error."""
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
