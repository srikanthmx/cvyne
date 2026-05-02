"""Resumes router — CRUD + personalization."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from models.job import JDSchema
from models.resume import ResumeCreateRequest, ResumeResponse, TailoredResumeSchema
from services.resume_personalizer import ResumePersonalizer

router = APIRouter()


@router.post("/", response_model=ResumeResponse, status_code=201)
async def create_resume(body: ResumeCreateRequest) -> ResumeResponse:
    """Save a base resume."""
    resume_id = uuid.uuid4()
    # TODO (Kiro): persist to DB
    return ResumeResponse(id=resume_id, name=body.name, data=body.data, is_base=body.is_base)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: uuid.UUID) -> ResumeResponse:
    # TODO (Kiro): query DB
    raise HTTPException(status_code=404, detail="Resume not found")


@router.post("/{resume_id}/personalize", response_model=TailoredResumeSchema)
async def personalize_resume(resume_id: uuid.UUID, jd: JDSchema) -> TailoredResumeSchema:
    """Personalize a saved resume for a given JD. Synchronous — use for preview."""
    # TODO (Kiro): load resume from DB
    raise HTTPException(status_code=404, detail="Resume not found")
