"""
Celery tasks — async job processing. Kiro owns this file.

All tasks are idempotent — safe to retry on failure.
Max retries: 3, exponential backoff starting at 60s.
"""

from __future__ import annotations

import asyncio

from celery import Task

from workers.celery_app import celery_app


class AsyncTask(Task):
    """Base task class that runs async coroutines in a new event loop."""

    def run_async(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(
    bind=True,
    base=AsyncTask,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
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

    async def _run():
        # TODO (Kiro): load job + resume from DB
        # TODO (Codex): wire OrchestratorService here
        # TODO (Kiro): publish events to Redis pub/sub channel f"app:{application_id}"
        raise NotImplementedError("Task body not yet implemented — see AGENTS.md")

    return self.run_async(_run())


@celery_app.task(name="workers.tasks.retry_failed_applications")
def retry_failed_applications() -> dict:
    """
    Beat task: find applications with status=failed and attempts<3, re-queue them.
    Kiro implements: query DB, filter eligible, call process_application_task.delay()
    """
    # TODO (Kiro): implement
    return {"requeued": 0}


@celery_app.task(name="workers.tasks.extract_jd")
def extract_jd_task(job_id: str, url: str) -> dict:
    """Extract JD from URL and update job record."""

    async def _run():
        from agents.browser_agent import BrowserAgent
        agent = BrowserAgent()
        jd = await agent.extract_jd(url)
        # TODO (Kiro): update DB
        return jd.model_dump()

    loop = asyncio.new_event_loop()
    return loop.run_until_complete(_run())
