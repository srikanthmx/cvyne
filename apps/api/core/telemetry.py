"""OpenTelemetry + Langfuse setup — Kiro implements, Codex uses."""

from __future__ import annotations


def setup_telemetry() -> None:
    """Initialize observability. Called once on app startup."""
    from core.config import settings

    if not settings.langfuse_secret_key:
        return  # skip in dev if not configured

    # TODO (Kiro): configure OpenTelemetry SDK with OTLP exporter
    # TODO (Kiro): instrument FastAPI (opentelemetry-instrumentation-fastapi)
    # TODO (Kiro): instrument SQLAlchemy (opentelemetry-instrumentation-sqlalchemy)
    # TODO (Codex): add Langfuse tracing to LLMClient calls
