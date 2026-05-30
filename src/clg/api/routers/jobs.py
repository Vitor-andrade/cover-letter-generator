"""Job endpoints — create, read, list."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from clg.api.deps import get_session
from clg.api.schemas import JobCreate, JobRead
from clg.core.persistence.models import Job
from clg.core.persistence.repositories import SqlJobRepository

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobRead)
def create_job(payload: JobCreate, session: Session = Depends(get_session)) -> JobRead:
    job = SqlJobRepository(session).add(
        Job(title=payload.title, company=payload.company, description=payload.description)
    )
    return JobRead.model_validate(job)


@router.get("", response_model=list[JobRead])
def list_jobs(session: Session = Depends(get_session)) -> list[JobRead]:
    return [JobRead.model_validate(j) for j in SqlJobRepository(session).list_all()]


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, session: Session = Depends(get_session)) -> JobRead:
    job = SqlJobRepository(session).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRead.model_validate(job)
