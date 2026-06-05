"""API boundary DTOs.

These Pydantic models define the request/response contract exposed to the UI.
ORM rows (SQLModel entities) are never returned directly — routers map entities
to these DTOs so the storage model can evolve independently of the API.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from clg.core.persistence.models import ProfileSource, VersionOrigin

_FROM_ORM = ConfigDict(from_attributes=True)

# --- profiles ------------------------------------------------------------- #


class ContactModel(BaseModel):
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    location: str = ""
    website: str = ""


class ExperienceEntry(BaseModel):
    role: str = ""
    company: str = ""
    period: str = ""
    location: str = ""
    highlights: list[str] = []


class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    tech: list[str] = []
    highlights: list[str] = []
    link: str = ""


class EducationEntry(BaseModel):
    degree: str = ""
    institution: str = ""
    period: str = ""
    details: str = ""


class CertificationEntry(BaseModel):
    name: str = ""
    issuer: str = ""
    year: str = ""  # string, not int — CV dates are messy ("expected 2025")


class LanguageEntry(BaseModel):
    language: str = ""
    proficiency: str = ""


class SectionsModel(BaseModel):
    contact: ContactModel = ContactModel()
    summary: str = ""
    key_skills: list[str] = []
    skills: list[str] = []
    experiences: list[ExperienceEntry] = []
    projects: list[ProjectEntry] = []
    education: list[EducationEntry] = []
    certifications: list[CertificationEntry] = []
    languages: list[LanguageEntry] = []


class ProfileCreate(BaseModel):
    name: str
    # When ``sections`` is given, the server composes background_text from it and
    # ignores this field; kept for the legacy unstructured path.
    background_text: str = ""
    source: ProfileSource = ProfileSource.manual
    sections: SectionsModel | None = None


class ProfileUpdate(BaseModel):
    name: str
    background_text: str = ""
    source: ProfileSource = ProfileSource.manual
    sections: SectionsModel | None = None


class ProfileRead(BaseModel):
    model_config = _FROM_ORM

    id: int
    name: str
    background_text: str
    source: ProfileSource
    sections: SectionsModel | None = None
    created_at: datetime


# --- jobs ----------------------------------------------------------------- #


class JobCreate(BaseModel):
    title: str
    company: str | None = None
    description: str


class JobRead(BaseModel):
    model_config = _FROM_ORM

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
    model_config = _FROM_ORM

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
    available_providers: list[str] = []
    providers_with_keys: list[str] = []


class SettingsUpdate(BaseModel):
    ai_provider: str | None = None
    default_language: str | None = None
