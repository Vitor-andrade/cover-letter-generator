"""Profile endpoints — create (manual or CV upload), read, list, update."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from clg.api.deps import get_session
from clg.api.schemas import ProfileCreate, ProfileRead, ProfileUpdate
from clg.core.ingestion.parse import MAX_INPUT_BYTES, IngestionError, extract_upload
from clg.core.ingestion.sectionize import sectionize
from clg.core.persistence.models import Profile
from clg.core.persistence.repositories import SqlProfileRepository
from clg.core.profile.compose import compose_background_text

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


def _resolve_background(
    payload: ProfileCreate | ProfileUpdate,
) -> tuple[str, dict[str, Any] | None]:
    """Compose background_text from structured sections when present.

    Returns ``(background_text, sections)``. With sections, background_text is
    derived (composed); without, the literal field is used and sections stays
    ``None`` (legacy unstructured profile).
    """
    if payload.sections is not None:
        sections = payload.sections.model_dump()
        return compose_background_text(sections), sections
    return payload.background_text, None


@router.post("", response_model=ProfileRead)
def create_profile(payload: ProfileCreate, session: Session = Depends(get_session)) -> ProfileRead:
    background_text, sections = _resolve_background(payload)
    profile = SqlProfileRepository(session).add(
        Profile(
            name=payload.name,
            background_text=background_text,
            source=payload.source,
            sections=sections,
        )
    )
    return ProfileRead.model_validate(profile)


@router.post("/upload", response_model=ProfileRead)
async def upload_profile(
    name: str = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ProfileRead:
    data = await file.read()
    if len(data) > MAX_INPUT_BYTES:
        raise HTTPException(status_code=413, detail="File too large")
    try:
        extracted = extract_upload(file.filename or "", data)
    except IngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # Locally split the extracted text into structured sections (no LLM, ADR-004),
    # then derive background_text from them — the user refines in the editor.
    sections, _ = sectionize(extracted.text)
    profile = SqlProfileRepository(session).add(
        Profile(
            name=name,
            background_text=compose_background_text(sections),
            source=extracted.source,
            sections=sections,
        )
    )
    return ProfileRead.model_validate(profile)


@router.get("", response_model=list[ProfileRead])
def list_profiles(session: Session = Depends(get_session)) -> list[ProfileRead]:
    return [ProfileRead.model_validate(p) for p in SqlProfileRepository(session).list_all()]


@router.get("/{profile_id}", response_model=ProfileRead)
def get_profile(profile_id: int, session: Session = Depends(get_session)) -> ProfileRead:
    profile = SqlProfileRepository(session).get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileRead.model_validate(profile)


@router.patch("/{profile_id}", response_model=ProfileRead)
def update_background(
    profile_id: int, payload: ProfileUpdate, session: Session = Depends(get_session)
) -> ProfileRead:
    repo = SqlProfileRepository(session)
    profile = repo.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.name = payload.name
    background_text, sections = _resolve_background(payload)
    profile.background_text = background_text
    # Reassign sections as a WHOLE object — SQLAlchemy's JSON column is not
    # mutation-tracked, so an in-place dict edit would silently not be flushed.
    profile.sections = sections
    repo.add(profile)
    return ProfileRead.model_validate(profile)
