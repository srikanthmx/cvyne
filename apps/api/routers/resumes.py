"""Resumes router — CRUD + personalization."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from db.models import Resume
from models.job import JDSchema
from models.resume import ResumeCreateRequest, ResumeResponse, ResumeSchema, TailoredResumeSchema
from services.resume_parser import ResumeParserService
from services.resume_personalizer import ResumePersonalizer

router = APIRouter()

# Placeholder user_id until Clerk auth is wired
_PLACEHOLDER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


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
async def create_resume(
    body: ResumeCreateRequest,
    db: AsyncSession = Depends(get_session),
) -> ResumeResponse:
    """Save a base resume."""
    resume_id = uuid.uuid4()
    row = Resume(
        id=resume_id,
        user_id=_PLACEHOLDER_USER_ID,
        name=body.name,
        data=body.data.model_dump(mode="json"),
        is_base=body.is_base,
    )
    db.add(row)
    await db.flush()
    return ResumeResponse(id=resume_id, name=body.name, data=body.data, is_base=body.is_base)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> ResumeResponse:
    row = await db.get(Resume, resume_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeResponse(
        id=row.id,
        name=row.name,
        data=ResumeSchema.model_validate(row.data),
        is_base=row.is_base,
    )


@router.post("/{resume_id}/personalize", response_model=TailoredResumeSchema)
async def personalize_resume(
    resume_id: uuid.UUID,
    jd: JDSchema,
    db: AsyncSession = Depends(get_session),
) -> TailoredResumeSchema:
    """Personalize a saved resume for a given JD. Synchronous — use for preview."""
    row = await db.get(Resume, resume_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume = ResumeSchema.model_validate(row.data)
    personalizer = ResumePersonalizer()
    return await personalizer.personalize(resume, jd)
