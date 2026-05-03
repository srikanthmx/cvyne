"""End-to-end orchestrator pipeline test with side-effecting steps mocked."""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from agents.browser_agent import AutofillResult
from agents.design_agent import FileRef
from models.job import ApplicationStatus, CVTheme, JDSchema
from models.resume import ExperienceEntry, ResumeSchema, TailoredResumeSchema
from services.orchestrator import OrchestratorService


class MockBrowserAgent:
    async def extract_jd(self, url: str) -> JDSchema:
        return JDSchema(
            title="Senior Python Engineer",
            company="Acme Corp",
            location="Remote",
            remote=True,
            employment_type="full-time",
            experience_level="senior",
            skills_required=["Python", "FastAPI", "AWS", "PostgreSQL"],
            skills_preferred=["Docker"],
            description="Build backend APIs with Python, FastAPI, AWS, and PostgreSQL.",
            apply_url=url,
        )

    async def autofill_form(
        self,
        url: str,
        resume: TailoredResumeSchema,
        cv_file_path: str,
        cover_letter: str | None = None,
        auto_submit: bool = False,
    ) -> AutofillResult:
        assert auto_submit is False
        assert cv_file_path.endswith("/ats.pdf")
        return AutofillResult(status=ApplicationStatus.SUBMITTED)


class MockPersonalizer:
    async def personalize(self, resume: ResumeSchema, jd: JDSchema) -> TailoredResumeSchema:
        return TailoredResumeSchema.model_validate(
            {
                **resume.model_dump(),
                "ats_score": 82,
                "keyword_coverage": 0.75,
                "changes_summary": ["Reordered Python API experience first."],
            }
        )


class MockATSOptimizer:
    async def optimize(self, resume: TailoredResumeSchema, jd: JDSchema) -> TailoredResumeSchema:
        resume.ats_score = 91
        return resume


class MockDesignAgent:
    def __init__(self) -> None:
        self.file_ref: FileRef | None = None

    async def generate_cv(
        self,
        resume: TailoredResumeSchema,
        theme: CVTheme,
        application_id: str,
        user_id: str,
    ) -> FileRef:
        self.file_ref = FileRef(
            s3_key=f"{user_id}/cvs/{application_id}/{theme.value}.pdf",
            filename=f"cv_{theme.value}.pdf",
            mime_type="application/pdf",
            size_bytes=12_345,
        )
        return self.file_ref


def _base_resume() -> ResumeSchema:
    return ResumeSchema(
        name="Jane Doe",
        email="jane@example.com",
        skills=["Python", "FastAPI", "PostgreSQL"],
        experience=[
            ExperienceEntry(
                company="Acme Corp",
                role="Software Engineer",
                start=date(2020, 1, 1),
                end=None,
                bullets=["Built Python APIs with FastAPI and PostgreSQL."],
            )
        ],
    )


@pytest.mark.asyncio
async def test_run_application_pipeline_yields_statuses_and_cv_ref() -> None:
    design_agent = MockDesignAgent()
    service = OrchestratorService(
        browser_agent=MockBrowserAgent(),
        design_agent=design_agent,
        personalizer=MockPersonalizer(),
        ats_optimizer=MockATSOptimizer(),
    )

    events = [
        event
        async for event in service.run_application(
            application_id=uuid.uuid4(),
            job_url="https://jobs.lever.co/anthropic",
            base_resume=_base_resume(),
            user_id="user-123",
            theme=CVTheme.ATS,
            generate_cover_letter=False,
        )
    ]

    assert len(events) >= 5
    assert events[-1].status == ApplicationStatus.SUBMITTED
    assert design_agent.file_ref is not None
    assert design_agent.file_ref.s3_key.endswith("/ats.pdf")
