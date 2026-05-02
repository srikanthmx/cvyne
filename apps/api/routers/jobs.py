"""Jobs router — extract and manage job postings."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from models.job import JobCreateRequest, JobResponse, JobStatus
from services.jd_extractor import JDExtractorService

router = APIRouter()


@router.post("/extract", response_model=JobResponse, status_code=202)
async def extract_job(body: JobCreateRequest, background_tasks: BackgroundTasks) -> JobResponse:
    """
    Submit a job URL for extraction.
    Returns a job record immediately; extraction runs in background.
    """
    job_id = uuid.uuid4()
    # TODO (Kiro): persist job record to DB with status=pending

    background_tasks.add_task(_run_extraction, job_id, body.url)

    return JobResponse(id=job_id, url=body.url, status=JobStatus.PENDING)


async def _run_extraction(job_id: uuid.UUID, url: str) -> None:
    extractor = JDExtractorService()
    try:
        jd = await extractor.extract(url)
        # TODO (Kiro): update DB record with jd + status=extracted
    except Exception as e:
        # TODO (Kiro): update DB record with status=failed, error message
        pass


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID) -> JobResponse:
    """Get job extraction result."""
    # TODO (Kiro): query DB
    raise HTTPException(status_code=404, detail="Job not found")
