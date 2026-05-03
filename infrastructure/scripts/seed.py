"""
Seed script — populates DB with one sample user, base resume, and job.
Idempotent: safe to run multiple times.

Usage:
    cd apps/api && uv run python ../../infrastructure/scripts/seed.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure apps/api is on the path when run from repo root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "api"))


async def seed() -> None:
    import uuid

    from sqlalchemy import select

    from core.db import async_session_factory
    from db.models import Job, Resume, User

    SEED_CLERK_ID = "seed_user_clerk_001"
    SEED_EMAIL = "seed@example.com"
    SEED_JOB_URL = "https://jobs.lever.co/anthropic/software-engineer"

    async with async_session_factory() as db:
        # --- User ---
        result = await db.execute(select(User).where(User.clerk_id == SEED_CLERK_ID))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                clerk_id=SEED_CLERK_ID,
                email=SEED_EMAIL,
            )
            db.add(user)
            await db.flush()
            print(f"Created user: {user.id}")
        else:
            print(f"User already exists: {user.id}")

        # --- Base Resume ---
        result = await db.execute(
            select(Resume).where(Resume.user_id == user.id, Resume.is_base == True)  # noqa: E712
        )
        resume = result.scalar_one_or_none()
        if resume is None:
            resume_data = {
                "name": "Alex Sample",
                "email": "alex@example.com",
                "phone": "+1-555-0100",
                "location": "San Francisco, CA",
                "summary": "Full-stack engineer with 5 years of experience building scalable web applications.",
                "skills": ["Python", "TypeScript", "React", "FastAPI", "PostgreSQL", "Docker", "AWS"],
                "experience": [
                    {
                        "company": "Acme Corp",
                        "role": "Senior Software Engineer",
                        "start": "2021-06-01",
                        "end": None,
                        "location": "San Francisco, CA",
                        "bullets": [
                            "Led migration of monolith to microservices, reducing p99 latency by 40%",
                            "Built real-time data pipeline processing 1M events/day using Kafka + Python",
                            "Mentored 3 junior engineers and conducted 50+ technical interviews",
                        ],
                    },
                    {
                        "company": "StartupXYZ",
                        "role": "Software Engineer",
                        "start": "2019-01-01",
                        "end": "2021-05-31",
                        "location": "Remote",
                        "bullets": [
                            "Built customer-facing React dashboard used by 10k+ daily active users",
                            "Designed and implemented REST API with FastAPI + PostgreSQL",
                        ],
                    },
                ],
                "education": [
                    {
                        "institution": "University of California, Berkeley",
                        "degree": "B.S. Computer Science",
                        "field": "Computer Science",
                        "year": 2018,
                    }
                ],
                "projects": [
                    {
                        "name": "OpenMetrics",
                        "description": "Open-source observability library for Python async applications",
                        "url": "https://github.com/example/openmetrics",
                        "tech": ["Python", "asyncio", "Prometheus"],
                        "bullets": ["500+ GitHub stars", "Used in production by 20+ companies"],
                    }
                ],
                "certifications": [],
            }
            resume = Resume(
                user_id=user.id,
                name="Base Resume",
                data=resume_data,
                is_base=True,
            )
            db.add(resume)
            await db.flush()
            print(f"Created base resume: {resume.id}")
        else:
            print(f"Base resume already exists: {resume.id}")

        # --- Sample Job ---
        result = await db.execute(select(Job).where(Job.url == SEED_JOB_URL, Job.user_id == user.id))
        job = result.scalar_one_or_none()
        if job is None:
            job = Job(
                user_id=user.id,
                url=SEED_JOB_URL,
                status="pending",
            )
            db.add(job)
            await db.flush()
            print(f"Created sample job: {job.id}")
        else:
            print(f"Sample job already exists: {job.id}")

        await db.commit()
        print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
