"""SQLModel entities — the persisted domain model.

Mirrors the ER diagram in ``docs/clg-architecture-plan.md``. Secrets are NOT
modelled here: API keys live in the encrypted key file (ADR-005), never the DB.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ProfileSource(StrEnum):
    upload = "upload"
    manual = "manual"


class VersionOrigin(StrEnum):
    ai = "ai"
    manual = "manual"


class Profile(SQLModel, table=True):
    """A user's background (experience, education, projects, achievements)."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    # ``background_text`` is DERIVED from ``sections`` (composed server-side) for
    # structured profiles; it stays the single source the generation/export
    # pipeline reads. ``sections`` is the structured editable source; ``None``
    # marks a legacy (pre-sections) profile.
    background_text: str
    sections: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    source: ProfileSource = ProfileSource.manual
    created_at: datetime = Field(default_factory=_utcnow)


class Job(SQLModel, table=True):
    """A target job posting."""

    id: int | None = Field(default=None, primary_key=True)
    title: str
    company: str | None = None
    description: str
    created_at: datetime = Field(default_factory=_utcnow)


class CoverLetter(SQLModel, table=True):
    """A generated cover letter, linking a profile to a job.

    The letter content lives in :class:`LetterVersion` rows so that AI drafts and
    manual edits are both retained as history.
    """

    id: int | None = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profile.id")
    job_id: int = Field(foreign_key="job.id")
    language: str = "en"
    provider: str = "ollama"
    model: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class LetterVersion(SQLModel, table=True):
    """One revision of a cover letter's text."""

    id: int | None = Field(default=None, primary_key=True)
    cover_letter_id: int = Field(foreign_key="coverletter.id")
    version_no: int
    content: str
    origin: VersionOrigin = VersionOrigin.ai
    created_at: datetime = Field(default_factory=_utcnow)


class Setting(SQLModel, table=True):
    """A single key/value application setting (non-secret)."""

    key: str = Field(primary_key=True)
    value: str
