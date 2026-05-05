"""Applications router — submit and stream application status."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from core.config import settings
from core.db import get_session
from db.models import Application, Job, Resume
from models.job import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationStatus,
    CVTheme,
    JDSchema,
)
from models.resume import ResumeSchema, TailoredResumeSchema
from workers.tasks import process_application_task

router = APIRouter()

_PLACEHOLDER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_TERMINAL_STATUSES = {"submitted", "failed", "requires_human", "cancelled"}


class ApplicationListItem(BaseModel):
    """Enriched application row for the dashboard list view."""

    id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID
    status: ApplicationStatus
    job_title: str | None = None
    company: str | None = None
    job_url: str | None = None
    cv_url: str | None = None
    error: str | None = None
    attempts: int = 0
    created_at: str | None = None
    submitted_at: str | None = None


class PreviewRequest(BaseModel):
    job_id: uuid.UUID
    resume_id: uuid.UUID
    theme: CVTheme = CVTheme.ATS
    generate_cover_letter: bool = False


class PreviewResponse(BaseModel):
    """The 'magic moment' payload — gives the UI everything it needs to render the preview."""

    job: JDSchema
    base_resume: ResumeSchema
    tailored_resume: TailoredResumeSchema
    cv_preview_url: str
    cover_letter: str | None = None


@router.get("/", response_model=list[ApplicationListItem])
async def list_applications(
    db: AsyncSession = Depends(get_session),
    limit: int = 100,
) -> list[ApplicationListItem]:
    """List the current user's applications, joined with job metadata for display."""
    stmt = (
        select(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .where(Application.user_id == _PLACEHOLDER_USER_ID)
        .order_by(desc(Application.created_at))
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    out: list[ApplicationListItem] = []
    for app, job in rows:
        jd = job.raw_jd or {}
        out.append(
            ApplicationListItem(
                id=app.id,
                job_id=app.job_id,
                resume_id=app.resume_id,
                status=ApplicationStatus(app.status),
                job_title=jd.get("title"),
                company=jd.get("company"),
                job_url=job.url,
                cv_url=f"/api/v1/applications/{app.id}/cv" if app.cv_file_key else None,
                error=app.error,
                attempts=app.attempts or 0,
                created_at=app.created_at.isoformat() if app.created_at else None,
                submitted_at=app.submitted_at.isoformat() if app.submitted_at else None,
            )
        )
    return out


@router.post("/preview", response_model=PreviewResponse)
async def preview_application(
    body: PreviewRequest,
    db: AsyncSession = Depends(get_session),
) -> PreviewResponse:
    """
    THE killer endpoint — synchronously personalizes the resume and generates the CV
    so the UI can show the user *before* they commit to submitting.

    Flow:
      1. Load job + resume from DB
      2. Run ResumePersonalizer + ATSOptimizer (LLM)
      3. Run DesignAgent.generate_cv → uploads PDF to S3 → returns presigned URL
      4. (Optional) Generate cover letter
    Returns everything the UI needs to render a side-by-side diff + CV preview.
    """
    from agents.design_agent import DesignAgent
    from services.ats_optimizer import ATSOptimizer
    from services.cover_letter import CoverLetterService
    from services.resume_personalizer import ResumePersonalizer

    job = await db.get(Job, body.job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    if not job.raw_jd:
        raise HTTPException(400, "Job has not been extracted yet")

    resume_row = await db.get(Resume, body.resume_id)
    if resume_row is None:
        raise HTTPException(404, "Resume not found")

    base_resume = ResumeSchema.model_validate(resume_row.data)
    jd = JDSchema.model_validate(job.raw_jd)

    # 1. Personalize
    personalizer = ResumePersonalizer()
    tailored = await personalizer.personalize(base_resume, jd)

    # 2. ATS-optimize
    ats = ATSOptimizer()
    tailored = await ats.optimize(tailored, jd)
    tailored.tailored_for_job_id = body.job_id

    # 3. Generate CV → bytes cached in Redis (1h TTL) for inline preview
    import redis.asyncio as aioredis
    preview_id = uuid.uuid4()
    design = DesignAgent()
    cv_ref = await design.generate_cv(
        resume=tailored,
        theme=body.theme,
        application_id=str(preview_id),
        user_id=str(_PLACEHOLDER_USER_ID),
    )
    if cv_ref.pdf_bytes:
        r = aioredis.from_url(settings.redis_url)
        try:
            await r.setex(f"cv-preview:{preview_id}", 3600, cv_ref.pdf_bytes)
        finally:
            await r.aclose()

    # 4. Optional cover letter
    cover = None
    if body.generate_cover_letter:
        cl = CoverLetterService()
        cover = await cl.generate(tailored, jd)

    return PreviewResponse(
        job=jd,
        base_resume=base_resume,
        tailored_resume=tailored,
        cv_preview_url=f"/api/v1/applications/preview-cv/{preview_id}",
        cover_letter=cover,
    )


@router.get("/preview-cv/{preview_id}")
async def get_preview_cv(preview_id: uuid.UUID) -> StreamingResponse:
    """Serve an inline preview PDF (cached in Redis for 1 hour)."""
    import redis.asyncio as aioredis

    r = aioredis.from_url(settings.redis_url)
    try:
        data: bytes | None = await r.get(f"cv-preview:{preview_id}")
    finally:
        await r.aclose()

    if not data:
        raise HTTPException(404, "Preview expired or not found")

    async def streamer():
        yield data

    return StreamingResponse(
        streamer(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="preview-{preview_id}.pdf"'},
    )


@router.get("/{application_id}/cv")
async def get_cv_file(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Stream the application's generated CV PDF."""
    app = await db.get(Application, application_id)
    if app is None or not app.cv_file_key:
        raise HTTPException(404, "CV file not found")

    try:
        from core.storage import stream_object  # implemented by Kiro
        body_iter, content_type = await stream_object(app.cv_file_key)
    except (ImportError, Exception) as exc:  # noqa: BLE001
        raise HTTPException(503, f"Object storage unavailable: {exc}")

    return StreamingResponse(
        body_iter,
        media_type=content_type or "application/pdf",
        headers={"Content-Disposition": f'inline; filename="cv-{application_id}.pdf"'},
    )


@router.post("/", response_model=ApplicationResponse, status_code=202)
async def submit_application(
    body: ApplicationCreateRequest,
    db: AsyncSession = Depends(get_session),
) -> ApplicationResponse:
    """Queue a job application. Returns immediately; use /stream to follow progress."""
    application_id = uuid.uuid4()

    # Persist application record before enqueuing so the task can load it
    app = Application(
        id=application_id,
        user_id=body.job_id,  # placeholder — real auth wires user_id from JWT
        job_id=body.job_id,
        resume_id=body.resume_id,
        theme=body.theme.value,
        status="queued",
        attempts=0,
    )
    db.add(app)
    await db.flush()

    process_application_task.delay(
        application_id=str(application_id),
        job_id=str(body.job_id),
        resume_id=str(body.resume_id),
        theme=body.theme.value,
        generate_cover_letter=body.generate_cover_letter,
    )

    return ApplicationResponse(
        id=application_id,
        job_id=body.job_id,
        resume_id=body.resume_id,
        status=ApplicationStatus.QUEUED,
        attempts=0,
    )


@router.get("/{application_id}/stream")
async def stream_status(application_id: uuid.UUID) -> EventSourceResponse:
    """
    SSE stream of ApplicationStatusEvent objects for real-time status updates.

    Subscribes to Redis pub/sub channel app:{application_id}.
    Terminates when status enters a terminal state.
    """

    async def event_generator():
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        pubsub = r.pubsub()
        channel = f"app:{application_id}"
        await pubsub.subscribe(channel)

        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                raw = message["data"]
                if isinstance(raw, bytes):
                    raw = raw.decode()

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                # Sentinel message — close the stream
                if data.get("terminal"):
                    yield {"event": "done", "data": json.dumps({"status": data.get("status")})}
                    break

                yield {"event": "status_update", "data": raw}

                # Also close on terminal status in the event payload itself
                if data.get("status") in _TERMINAL_STATUSES:
                    break
        finally:
            await pubsub.unsubscribe(channel)
            await r.aclose()

    return EventSourceResponse(event_generator())


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> ApplicationResponse:
    """Get current application state."""
    app = await db.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationResponse.model_validate(app)


@router.post("/{application_id}/cancel", response_model=ApplicationResponse)
async def cancel_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> ApplicationResponse:
    """Cancel a running or queued application. No-op if already terminal."""
    app = await db.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.status in _TERMINAL_STATUSES:
        return ApplicationResponse.model_validate(app)

    app.status = "cancelled"
    await db.commit()

    # Publish cancellation event so SSE stream closes
    import json
    import redis.asyncio as aioredis
    r = aioredis.from_url(settings.redis_url)
    try:
        cancel_event = {
            "application_id": str(application_id),
            "status": "cancelled",
            "step": "cancelled",
            "progress": 0,
            "message": "Cancelled by user",
        }
        await r.publish(f"app:{application_id}", json.dumps(cancel_event))
        await r.publish(f"app:{application_id}", json.dumps({"terminal": True, "status": "cancelled"}))
    finally:
        await r.aclose()

    return ApplicationResponse.model_validate(app)


@router.post("/{application_id}/retry", response_model=ApplicationResponse)
async def retry_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> ApplicationResponse:
    """Manually retry a failed or cancelled application."""
    app = await db.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.status not in {"failed", "cancelled"}:
        raise HTTPException(status_code=400, detail=f"Cannot retry application in status: {app.status}")

    app.status = "queued"
    await db.commit()

    process_application_task.delay(
        application_id=str(application_id),
        job_id=str(app.job_id),
        resume_id=str(app.resume_id),
        theme=app.theme or "ats",
        user_id=str(app.user_id),
    )

    return ApplicationResponse.model_validate(app)
