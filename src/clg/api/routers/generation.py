"""Generation endpoints — generate a letter and regenerate/revise it."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from clg.api.deps import get_session
from clg.api.schemas import (
    GenerateRequest,
    LetterRead,
    LetterVersionRead,
    RegenerateSectionRequest,
)
from clg.core.generation.service import GenerationError, GenerationService
from clg.core.persistence.models import CoverLetter, LetterVersion
from clg.core.persistence.repositories import (
    SqlJobRepository,
    SqlLetterRepository,
    SqlProfileRepository,
)
from clg.core.providers.base import ProviderError

router = APIRouter(prefix="/api/generation", tags=["generation"])


def _service(session: Session) -> GenerationService:
    return GenerationService(
        profiles=SqlProfileRepository(session),
        jobs=SqlJobRepository(session),
        letters=SqlLetterRepository(session),
    )


def _to_letter_read(letter: CoverLetter, version: LetterVersion) -> LetterRead:
    return LetterRead(
        id=letter.id or 0,
        profile_id=letter.profile_id,
        job_id=letter.job_id,
        language=letter.language,
        provider=letter.provider,
        model=letter.model,
        created_at=letter.created_at,
        latest_version=LetterVersionRead.model_validate(version),
    )


@router.post("", response_model=LetterRead)
def generate(payload: GenerateRequest, session: Session = Depends(get_session)) -> LetterRead:
    try:
        result = _service(session).generate(
            profile_id=payload.profile_id,
            job_id=payload.job_id,
            language=payload.language,
            provider=payload.provider,
            model=payload.model,
        )
    except GenerationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return _to_letter_read(result.letter, result.version)


@router.post("/regenerate", response_model=LetterVersionRead)
def regenerate(
    payload: RegenerateSectionRequest, session: Session = Depends(get_session)
) -> LetterVersionRead:
    try:
        version = _service(session).regenerate_section(
            letter_id=payload.letter_id,
            instruction=payload.instruction,
            language=payload.language,
        )
    except GenerationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return LetterVersionRead.model_validate(version)
