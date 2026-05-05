"""
Celery tasks — async job processing. Kiro owns this file.

All tasks are idempotent — safe to retry on failure.
Max retries: 3, exponential backoff starting at 60s.
"""

from __future__ import annotations

import asyncio
import uuid

from celery import Task

from workers.celery_app import celery_app


class AsyncTask(Task):
    """Base task class that runs async coroutines in a new event loop."""

    def run_async(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


@celery_app.task(
    bind=True,
    base=AsyncTask,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=300,
    name="workers.tasks.process_application",
)
def process_application_task(
    self,
    application_id: str,
    job_id: str,
    resume_id: str,
    theme: str,
    generate_cover_letter: bool = False,
    user_id: str = "",
) -> dict:
    """
    Full application pipeline task.

    Steps:
    1. Load job + resume from DB
    2. Run OrchestratorService pipeline
    3. Publish status events to Redis pub/sub (consumed by SSE endpoint)
    4. Update DB application record at each step
    """

    async def _run() -> dict:
        import json

        import redis.asyncio as aioredis
        from sqlalchemy import select

        from core.config import settings
        from core.db import async_session_factory
        from db.models import Application, Job, Resume
        from models.job import ApplicationStatus, CVTheme
        from models.resume import ResumeSchema
        from services.orchestrator import OrchestratorService

        app_uuid = uuid.UUID(application_id)
        r = aioredis.from_url(settings.redis_url)
        channel = f"app:{application_id}"

        async def publish(event_json: str) -> None:
            await r.publish(channel, event_json)

        async with async_session_factory() as db:
            # Load application
            app = await db.get(Application, app_uuid)
            if app is None:
                raise ValueError(f"Application {application_id} not found")

            # Idempotency: skip if already in a terminal state
            terminal = {"submitted", "failed", "requires_human", "cancelled"}
            if app.status in terminal:
                return {"status": app.status, "skipped": True}

            # Load job and resume
            job = await db.get(Job, app.job_id)
            resume_row = await db.get(Resume, app.resume_id)
            if job is None or resume_row is None:
                raise ValueError("Job or resume not found")

            app.status = "processing"
            app.attempts = (app.attempts or 0) + 1
            await db.commit()

            try:
                resume = ResumeSchema.model_validate(resume_row.data)
                cv_theme = CVTheme(theme) if theme else CVTheme.ATS
                orch = OrchestratorService()

                final_status = "processing"
                async for event in orch.run_application(
                    application_id=app_uuid,
                    job_url=job.url,
                    base_resume=resume,
                    user_id=user_id or str(app.user_id),
                    theme=cv_theme,
                    generate_cover_letter=generate_cover_letter,
                ):
                    # Check if cancelled mid-run
                    await db.refresh(app)
                    if app.status == "cancelled":
                        return {"status": "cancelled", "skipped": True}

                    event_json = event.model_dump_json()
                    await publish(event_json)

                    # Update DB status at each step
                    app.status = event.status.value
                    final_status = event.status.value

                    if event.status == ApplicationStatus.SUBMITTED:
                        from datetime import datetime, timezone
                        app.submitted_at = datetime.now(timezone.utc)

                    if event.error_code:
                        app.error = event.message

                    await db.commit()

                # Publish terminal sentinel so SSE subscriber knows to close
                sentinel = json.dumps({"terminal": True, "status": final_status})
                await publish(sentinel)
                return {"status": final_status}

            except Exception as exc:
                app.status = "failed"
                app.error = str(exc)
                await db.commit()
                # Publish failure event
                import json as _json
                from models.job import ApplicationStatusEvent
                err_event = ApplicationStatusEvent(
                    application_id=app_uuid,
                    status=ApplicationStatus.FAILED,
                    step="error",
                    progress=0,
                    message=str(exc),
                    error_code="internal_error",
                )
                await publish(err_event.model_dump_json())
                await publish(_json.dumps({"terminal": True, "status": "failed"}))
                raise
            finally:
                await r.aclose()

    return self.run_async(_run())


@celery_app.task(name="workers.tasks.extract_jd")
def extract_jd_task(job_id: str, url: str) -> dict:
    """Extract JD from URL and update job record."""

    async def _run() -> dict:
        from core.db import async_session_factory
        from db.models import Job

        job_uuid = uuid.UUID(job_id)

        async with async_session_factory() as db:
            job = await db.get(Job, job_uuid)
            if job is None:
                raise ValueError(f"Job {job_id} not found")

            job.status = "extracting"
            await db.commit()

            try:
                from agents.browser_agent import BrowserAgent
                agent = BrowserAgent()
                jd = await agent.extract_jd(url)
                job.raw_jd = jd.model_dump()
                job.status = "extracted"
                await db.commit()
                return jd.model_dump()
            except Exception as exc:
                job.status = "failed"
                await db.commit()
                raise

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
