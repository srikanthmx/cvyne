"""Applications router — submit and stream application status."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from core.config import settings
from core.db import get_session
from db.models import Application
from models.job import ApplicationCreateRequest, ApplicationResponse, ApplicationStatus
from workers.tasks import process_application_task

router = APIRouter()

_TERMINAL_STATUSES = {"submitted", "failed", "requires_human"}


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
