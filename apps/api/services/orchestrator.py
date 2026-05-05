"""
Application Orchestrator — composes agents into the end-to-end apply flow.

This is the main service coordinating: JD extraction → personalization →
ATS optimization → CV generation → autofill → submit.

Codex owns this file.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from typing import Any

from agents.browser_agent import BrowserAgent
from agents.design_agent import DesignAgent
from models.job import ApplicationStatus, ApplicationStatusEvent, CVTheme, JDSchema
from models.resume import ResumeSchema, TailoredResumeSchema
from services.ats_optimizer import ATSOptimizer
from services.cover_letter import CoverLetterService
from services.jd_extractor import JDExtractorService
from services.resume_personalizer import ResumePersonalizer


class OrchestratorService:
    """
    Coordinates the full job application pipeline.

    Yields ApplicationStatusEvent objects for SSE streaming.
    Each step is independently retryable via Celery tasks.
    """

    def __init__(
        self,
        browser_agent: BrowserAgent | None = None,
        design_agent: DesignAgent | None = None,
        jd_extractor: JDExtractorService | None = None,
        personalizer: ResumePersonalizer | None = None,
        ats_optimizer: ATSOptimizer | None = None,
        cover_letter_svc: CoverLetterService | None = None,
    ) -> None:
        self._browser = browser_agent or BrowserAgent()
        self._design = design_agent or DesignAgent()
        self._jd_extractor = jd_extractor or JDExtractorService()
        self._personalizer = personalizer or ResumePersonalizer()
        self._ats_optimizer = ats_optimizer or ATSOptimizer()
        self._cover_letter = cover_letter_svc or CoverLetterService()

    async def run_application(
        self,
        application_id: uuid.UUID,
        job_url: str,
        base_resume: ResumeSchema,
        user_id: str,
        theme: CVTheme = CVTheme.ATS,
        generate_cover_letter: bool = False,
    ) -> AsyncIterator[ApplicationStatusEvent]:
        """
        Full pipeline as an async generator. Yields status events at each step.

        Consumer (SSE endpoint) forwards events to the client in real-time.
        """

        def event(status: ApplicationStatus, step: str, progress: int, message: str | None = None) -> ApplicationStatusEvent:
            return ApplicationStatusEvent(
                application_id=application_id,
                status=status,
                step=step,
                progress=progress,
                message=message,
            )

        yield event(ApplicationStatus.PROCESSING, "jd_extraction", 10)
        jd = await self._browser.extract_jd(job_url)

        yield event(ApplicationStatus.PROCESSING, "resume_personalization", 30)
        tailored = await self._personalizer.personalize(base_resume, jd)

        yield event(ApplicationStatus.PROCESSING, "ats_optimization", 50)
        tailored = await self._ats_optimizer.optimize(tailored, jd)

        cover_letter: str | None = None
        if generate_cover_letter:
            yield event(ApplicationStatus.PROCESSING, "cover_letter", 60)
            cover_letter = await self._cover_letter.generate(tailored, jd)

        yield event(ApplicationStatus.GENERATING_CV, "cv_generation", 70)
        cv_file = await self._design.generate_cv(tailored, theme, str(application_id), user_id)

        yield event(ApplicationStatus.FILLING_FORM, "form_autofill", 85)

        # Re-instantiate the browser agent with application_id wiring so it
        # publishes per-step screenshots to Redis pub/sub. The frontend's SSE
        # stream picks these up and renders a live "agent's-eye view".
        from core.config import settings
        browser_for_form = BrowserAgent(
            provider=self._browser._provider,
            api_key=self._browser._api_key,
            model=self._browser._model,
            headless=self._browser._headless,
            application_id=str(application_id),
            redis_url=settings.redis_url,
        )
        result = await browser_for_form.autofill_form(
            url=job_url,
            resume=tailored,
            cv_file_path=cv_file.s3_key,
            cover_letter=cover_letter,
        )

        if result.status == ApplicationStatus.REQUIRES_HUMAN:
            yield ApplicationStatusEvent(
                application_id=application_id,
                status=ApplicationStatus.REQUIRES_HUMAN,
                step="captcha",
                progress=85,
                error_code="captcha_required",
                message="CAPTCHA encountered — please complete manually",
            )
            return

        if result.status == ApplicationStatus.FAILED:
            yield ApplicationStatusEvent(
                application_id=application_id,
                status=ApplicationStatus.FAILED,
                step="autofill",
                progress=85,
                error_code=result.error_code,
                message=result.error_message,
            )
            return

        yield event(ApplicationStatus.SUBMITTED, "done", 100, "Application submitted successfully")
