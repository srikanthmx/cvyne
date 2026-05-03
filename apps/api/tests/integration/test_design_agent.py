"""Integration checks for the open-design sidecar client and CV PDF rendering."""

from __future__ import annotations

import uuid
from datetime import date

import httpx
import pytest

from agents.design_agent import THEME_TO_DESIGN_SYSTEM, DesignAgent, OpenDesignClient
from models.job import CVTheme
from models.resume import ExperienceEntry, TailoredResumeSchema


def _sample_resume() -> TailoredResumeSchema:
    return TailoredResumeSchema(
        name="Jane Doe",
        email="jane@example.com",
        phone="+1 555 0100",
        location="Austin, TX",
        summary="Backend engineer focused on reliable Python APIs and cloud systems.",
        skills=["Python", "FastAPI", "PostgreSQL", "AWS", "Docker", "Observability"],
        experience=[
            ExperienceEntry(
                company="Acme Corp",
                role="Senior Software Engineer",
                start=date(2021, 1, 1),
                end=None,
                bullets=[
                    "Built FastAPI services used by internal product teams.",
                    "Improved API latency by 30% through query tuning and caching.",
                    "Led migration of batch jobs to containerized AWS workloads.",
                ],
            ),
            ExperienceEntry(
                company="Example Health",
                role="Software Engineer",
                start=date(2018, 6, 1),
                end=date(2020, 12, 31),
                bullets=[
                    "Maintained PostgreSQL-backed services for claims workflows.",
                    "Added structured logging and alerts for production incidents.",
                ],
            ),
        ],
    )


def _design_system_slug(item: dict) -> str | None:
    for key in ("slug", "id", "name"):
        value = item.get(key)
        if isinstance(value, str):
            return value
    return None


@pytest.mark.asyncio
async def test_open_design_theme_mapping_matches_daemon() -> None:
    client = OpenDesignClient()
    try:
        systems = await client.list_design_systems()
    except (httpx.HTTPError, httpx.ConnectError) as exc:
        pytest.skip(f"open-design daemon is not reachable: {exc}")
    finally:
        await client.close()

    slugs = {_design_system_slug(item) for item in systems}
    assert set(THEME_TO_DESIGN_SYSTEM.values()).issubset(slugs)


@pytest.mark.asyncio
async def test_generate_cv_pdf_non_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, bytes] = {}

    async def capture_upload(self: DesignAgent, data: bytes, s3_key: str) -> None:
        captured[s3_key] = data

    monkeypatch.setattr(DesignAgent, "_upload_to_s3", capture_upload)
    agent = DesignAgent(s3_client=object())
    application_id = str(uuid.uuid4())

    file_ref = await agent.generate_cv(
        resume=_sample_resume(),
        theme=CVTheme.ATS,
        application_id=application_id,
        user_id="user-123",
    )

    pdf_bytes = captured[file_ref.s3_key]
    assert file_ref.size_bytes == len(pdf_bytes)
    assert len(pdf_bytes) > 10_000
    assert pdf_bytes.startswith(b"%PDF")
