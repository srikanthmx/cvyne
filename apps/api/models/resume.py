"""Resume domain models — Pydantic v2. Mirrors packages/shared-types/src/resume.ts."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class ExperienceEntry(BaseModel):
    company: str
    role: str
    start: date
    end: Optional[date] = None
    location: str | None = None
    bullets: list[str] = Field(default_factory=list, max_length=10)


class EducationEntry(BaseModel):
    institution: str
    degree: str
    field: str | None = None
    year: int


class ProjectEntry(BaseModel):
    name: str
    description: str
    url: HttpUrl | None = None
    tech: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class CertificationEntry(BaseModel):
    name: str
    issuer: str
    date: Optional[date] = None
    url: Optional[HttpUrl] = None


class ResumeSchema(BaseModel):
    """Canonical resume structure — do not modify without updating shared-types."""

    name: str
    email: EmailStr
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    linkedin: HttpUrl | None = None
    github: HttpUrl | None = None
    portfolio: HttpUrl | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)


class TailoredResumeSchema(ResumeSchema):
    """Resume after personalization — includes metadata about changes."""

    tailored_for_job_id: uuid.UUID | None = None
    ats_score: Annotated[float, Field(ge=0, le=100)] | None = None
    keyword_coverage: Annotated[float, Field(ge=0, le=1)] | None = None
    changes_summary: list[str] = Field(default_factory=list)


class ResumeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    data: ResumeSchema
    is_base: bool = False


class ResumeResponse(BaseModel):
    id: uuid.UUID
    name: str
    data: ResumeSchema
    is_base: bool

    model_config = {"from_attributes": True}
