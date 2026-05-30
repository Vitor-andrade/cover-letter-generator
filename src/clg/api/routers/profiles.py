"""Profile endpoints — create (manual or CV upload), read, list, update."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from clg.api.deps import get_session
from clg.api.schemas import ProfileCreate, ProfileRead
from clg.core.ingestion.parse import MAX_INPUT_BYTES, IngestionError, extract_upload
from clg.core.persistence.models import Profile
from clg.core.persistence.repositories import SqlProfileRepository

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("", response_model=ProfileRead)
def create_profile(payload: ProfileCreate, session: Session = Depends(get_session)) -> ProfileRead:
    profile = SqlProfileRepository(session).add(
        Profile(
            name=payload.name,
            background_text=payload.background_text,
            source=payload.source,
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
    profile = SqlProfileRepository(session).add(
        Profile(name=name, background_text=extracted.text, source=extracted.source)
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
    profile_id: int, payload: ProfileCreate, session: Session = Depends(get_session)
) -> ProfileRead:
    repo = SqlProfileRepository(session)
    profile = repo.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.name = payload.name
    profile.background_text = payload.background_text
    repo.add(profile)
    return ProfileRead.model_validate(profile)
