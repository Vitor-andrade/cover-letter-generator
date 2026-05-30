"""Export endpoints — render a letter's latest version to a downloadable file."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel import Session

from clg.api.deps import get_session
from clg.core.export.base import ExportError, ExportFormat, LetterDocument, get_renderer
from clg.core.persistence.repositories import (
    SqlJobRepository,
    SqlLetterRepository,
    SqlProfileRepository,
)

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/{letter_id}/{fmt}")
def export_letter(
    letter_id: int, fmt: ExportFormat, session: Session = Depends(get_session)
) -> Response:
    letters = SqlLetterRepository(session)
    letter = letters.get(letter_id)
    if letter is None:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    versions = letters.versions(letter_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Cover letter has no content")

    profile = SqlProfileRepository(session).get(letter.profile_id)
    job = SqlJobRepository(session).get(letter.job_id)
    title = f"Cover Letter — {job.title}" if job else "Cover Letter"

    doc = LetterDocument(
        content=versions[-1].content,
        title=title,
        candidate_name=profile.name if profile else "",
        language=letter.language,
    )
    renderer = get_renderer(fmt)
    try:
        body = renderer.render(doc)
    except ExportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    filename = f"cover-letter-{letter_id}.{renderer.extension}"
    return Response(
        content=body,
        media_type=renderer.media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
