"""API boundary DTOs.

These Pydantic models define the request/response contract exposed to the UI.
ORM rows (SQLModel entities) are never returned directly — routers map entities
to these DTOs so the storage model can evolve independently of the API.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from clg.core.persistence.models import ProfileSource, VersionOrigin

# --- profiles ------------------------------------------------------------- #


class ProfileCreate(BaseModel):
    name: str
    background_text: str
    source: ProfileSource = ProfileSource.manual


class ProfileRead(BaseModel):
    id: int
    name: str
    background_text: str
    source: ProfileSource
    created_at: datetime


# --- jobs ----------------------------------------------------------------- #


class JobCreate(BaseModel):
    title: str
    company: str | None = None
    description: str


class JobRead(BaseModel):
    id: int
    title: str
    company: str | None
    description: str
    created_at: datetime


# --- generation ----------------------------------------------------------- #


class GenerateRequest(BaseModel):
    profile_id: int
    job_id: int
    language: str = "en"
    provider: str | None = None  # None => use configured default
    model: str | None = None


class RegenerateSectionRequest(BaseModel):
    letter_id: int
    instruction: str
    language: str | None = None


class LetterVersionRead(BaseModel):
    id: int
    version_no: int
    content: str
    origin: VersionOrigin
    created_at: datetime


class LetterRead(BaseModel):
    id: int
    profile_id: int
    job_id: int
    language: str
    provider: str
    model: str | None
    created_at: datetime
    latest_version: LetterVersionRead | None = None


# --- settings ------------------------------------------------------------- #


class SettingsRead(BaseModel):
    ai_provider: str
    default_language: str
    values: dict[str, str] = {}


class SettingsUpdate(BaseModel):
    ai_provider: str | None = None
    default_language: str | None = None


class ProviderKeyUpdate(BaseModel):
    provider: str
    api_key: str
