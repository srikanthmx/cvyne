"""Applications router — submit and stream application status."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from models.job import ApplicationCreateRequest, ApplicationResponse, ApplicationStatusEvent
from workers.tasks import process_application_task

router = APIRouter()


@router.post("/", response_model=ApplicationResponse, status_code=202)
async def submit_application(body: ApplicationCreateRequest) -> ApplicationResponse:
    """Queue a job application. Returns immediately; use /stream to follow progress."""
    application_id = uuid.uuid4()

    # Enqueue Celery task (Kiro implements task body)
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
        status="queued",  # type: ignore[arg-type]
        attempts=0,
    )


@router.get("/{application_id}/stream")
async def stream_status(application_id: uuid.UUID) -> EventSourceResponse:
    """
    SSE stream of ApplicationStatusEvent objects for real-time status updates.

    Event format: { "event": "status_update", "data": "<json>" }
    Terminates when status is submitted, failed, or requires_human.
    """

    async def event_generator():
        # TODO (Codex): subscribe to Redis pub/sub channel for application_id
        # Placeholder: poll DB until terminal state
        terminal_statuses = {"submitted", "failed", "requires_human"}
        max_polls = 120  # 10 min timeout at 5s intervals

        for _ in range(max_polls):
            # TODO (Kiro): query DB for current status, yield event
            await asyncio.sleep(5)
            # Placeholder event — real implementation reads from DB/Redis
            yield {
                "event": "heartbeat",
                "data": json.dumps({"application_id": str(application_id)}),
            }

    return EventSourceResponse(event_generator())


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: uuid.UUID) -> ApplicationResponse:
    """Get current application state."""
    # TODO (Kiro): query DB
    raise HTTPException(status_code=404, detail="Application not found")
