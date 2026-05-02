"""Job and application domain models."""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl


class JobStatus(StrEnum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    FAILED = "failed"


class ApplicationStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    GENERATING_CV = "generating_cv"
    FILLING_FORM = "filling_form"
    SUBMITTED = "submitted"
    FAILED = "failed"
    REQUIRES_HUMAN = "requires_human"


class CVTheme(StrEnum):
    ATS = "ats"
    MODERN = "modern"
    CREATIVE = "creative"
    PORTFOLIO = "portfolio"


class JDSchema(BaseModel):
    """Extracted, normalized job description."""

    title: str
    company: str
    location: str | None = None
    remote: bool | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    skills_required: list[str] = Field(default_factory=list)
    skills_preferred: list[str] = Field(default_factory=list)
    description: str
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    apply_url: str | None = None


class JobCreateRequest(BaseModel):
    url: str = Field(min_length=1)


class JobResponse(BaseModel):
    id: uuid.UUID
    url: str
    status: JobStatus
    jd: JDSchema | None = None

    model_config = {"from_attributes": True}


class ApplicationCreateRequest(BaseModel):
    job_id: uuid.UUID
    resume_id: uuid.UUID
    theme: CVTheme = CVTheme.ATS
    generate_cover_letter: bool = False


class ApplicationStatusEvent(BaseModel):
    """SSE event payload for real-time status updates."""

    application_id: uuid.UUID
    status: ApplicationStatus
    step: str
    progress: Annotated[int, Field(ge=0, le=100)]
    message: str | None = None
    error_code: str | None = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID
    status: ApplicationStatus
    cv_url: str | None = None
    error: str | None = None
    attempts: int

    model_config = {"from_attributes": True}
