"""Resumes router — CRUD + personalization."""

from __future__ import annotations

import uuid

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from models.job import JDSchema
from models.resume import ResumeCreateRequest, ResumeResponse, ResumeSchema, TailoredResumeSchema
from services.resume_parser import ResumeParserService
from services.resume_personalizer import ResumePersonalizer

router = APIRouter()


@router.post("/parse", response_model=ResumeSchema)
async def parse_resume_upload(file: UploadFile = File(...)) -> ResumeSchema:
    """
    Parse an uploaded PDF/DOCX/TXT resume into structured ResumeSchema.
    User can edit the result before saving as their base resume.
    """
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 10MB)")

    suffix = Path(file.filename or "resume.pdf").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        parser = ResumeParserService()
        return await parser.parse_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


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
