"""AutoApply AI — FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.db import init_db
from core.telemetry import setup_telemetry
from routers import applications, jobs, resumes, user_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    setup_telemetry()
    # Ensure MinIO bucket exists (idempotent)
    try:
        from core.storage import ensure_bucket_exists
        await ensure_bucket_exists()
    except Exception:
        pass  # non-fatal in dev if MinIO isn't up yet
    yield


app = FastAPI(
    title="AutoApply AI",
    version="0.1.0",
    description="Intelligent job application automation API",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(resumes.router, prefix="/api/v1/resumes", tags=["resumes"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(user_settings.router, prefix="/api/v1/settings", tags=["settings"])


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "version": "0.1.0"})


@app.get("/health/deep")
async def health_deep() -> JSONResponse:
    checks: dict[str, str] = {}

    # DB check
    try:
        from sqlalchemy import text
        from core.db import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {exc}"

    # Redis check
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return JSONResponse({"status": status, **checks})
