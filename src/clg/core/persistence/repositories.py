"""Repository interfaces (Protocols) and their SQLModel implementations.

The domain depends on the Protocols, not the concrete SQLite-backed classes, so
the storage engine can later be swapped (e.g. Postgres in Phase C) without
touching generation/ingestion/export logic.
"""

from __future__ import annotations

from typing import Protocol

from sqlmodel import Session, col, select

from clg.core.persistence.models import (
    CoverLetter,
    Job,
    LetterVersion,
    Profile,
    Setting,
)

# --------------------------------------------------------------------------- #
# Protocols
# --------------------------------------------------------------------------- #


class ProfileRepository(Protocol):
    def add(self, profile: Profile) -> Profile: ...
    def get(self, profile_id: int) -> Profile | None: ...
    def list_all(self) -> list[Profile]: ...


class JobRepository(Protocol):
    def add(self, job: Job) -> Job: ...
    def get(self, job_id: int) -> Job | None: ...
    def list_all(self) -> list[Job]: ...


class LetterRepository(Protocol):
    def add(self, letter: CoverLetter) -> CoverLetter: ...
    def get(self, letter_id: int) -> CoverLetter | None: ...
    def list_all(self) -> list[CoverLetter]: ...
    def add_version(self, version: LetterVersion) -> LetterVersion: ...
    def versions(self, letter_id: int) -> list[LetterVersion]: ...
    def next_version_no(self, letter_id: int) -> int: ...


class SettingsRepository(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...
    def all(self) -> dict[str, str]: ...


# --------------------------------------------------------------------------- #
# SQLModel implementations
# --------------------------------------------------------------------------- #


class SqlProfileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, profile: Profile) -> Profile:
        self._session.add(profile)
        self._session.flush()
        self._session.refresh(profile)
        return profile

    def get(self, profile_id: int) -> Profile | None:
        return self._session.get(Profile, profile_id)

    def list_all(self) -> list[Profile]:
        return list(self._session.exec(select(Profile)).all())


class SqlJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, job: Job) -> Job:
        self._session.add(job)
        self._session.flush()
        self._session.refresh(job)
        return job

    def get(self, job_id: int) -> Job | None:
        return self._session.get(Job, job_id)

    def list_all(self) -> list[Job]:
        return list(self._session.exec(select(Job)).all())


class SqlLetterRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, letter: CoverLetter) -> CoverLetter:
        self._session.add(letter)
        self._session.flush()
        self._session.refresh(letter)
        return letter

    def get(self, letter_id: int) -> CoverLetter | None:
        return self._session.get(CoverLetter, letter_id)

    def list_all(self) -> list[CoverLetter]:
        return list(self._session.exec(select(CoverLetter)).all())

    def add_version(self, version: LetterVersion) -> LetterVersion:
        self._session.add(version)
        self._session.flush()
        self._session.refresh(version)
        return version

    def versions(self, letter_id: int) -> list[LetterVersion]:
        stmt = (
            select(LetterVersion)
            .where(col(LetterVersion.cover_letter_id) == letter_id)
            .order_by(col(LetterVersion.version_no))
        )
        return list(self._session.exec(stmt).all())

    def next_version_no(self, letter_id: int) -> int:
        existing = self.versions(letter_id)
        return (existing[-1].version_no + 1) if existing else 1


class SqlSettingsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, key: str) -> str | None:
        row = self._session.get(Setting, key)
        return row.value if row else None

    def set(self, key: str, value: str) -> None:
        row = self._session.get(Setting, key)
        if row is None:
            self._session.add(Setting(key=key, value=value))
        else:
            row.value = value
            self._session.add(row)

    def all(self) -> dict[str, str]:
        return {s.key: s.value for s in self._session.exec(select(Setting)).all()}
