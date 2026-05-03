"""Jobs router — extract and manage job postings."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from db.models import Job
from models.job import JobCreateRequest, JobResponse, JobStatus
from services.jd_extractor import JDExtractorService

router = APIRouter()


@router.post("/extract", response_model=JobResponse, status_code=202)
async def extract_job(
    body: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
) -> JobResponse:
    """
    Submit a job URL for extraction.
    Returns a job record immediately; extraction runs in background.
    """
    job_id = uuid.uuid4()

    # Persist job record with status=pending
    # user_id placeholder — real auth wires this from JWT/Clerk
    placeholder_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    job = Job(
        id=job_id,
        user_id=placeholder_user_id,
        url=body.url,
        status="pending",
    )
    db.add(job)
    await db.flush()

    background_tasks.add_task(_run_extraction, job_id, body.url)

    return JobResponse(id=job_id, url=body.url, status=JobStatus.PENDING)


async def _run_extraction(job_id: uuid.UUID, url: str) -> None:
    from core.db import async_session_factory

    extractor = JDExtractorService()
    async with async_session_factory() as db:
        job = await db.get(Job, job_id)
        if job is None:
            return

        job.status = "extracting"
        await db.commit()

        try:
            jd = await extractor.extract(url)
            job.raw_jd = jd.model_dump()
            job.status = "extracted"
        except Exception as exc:
            job.status = "failed"
        finally:
            await db.commit()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> JobResponse:
    """Get job extraction result."""
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        id=job.id,
        url=job.url,
        status=JobStatus(job.status),
        jd=job.raw_jd,
    )
