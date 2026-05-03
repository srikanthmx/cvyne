"""OpenTelemetry + Langfuse setup — Kiro implements, Codex uses."""

from __future__ import annotations


def setup_telemetry() -> None:
    """Initialize observability. Called once on app startup."""
    from core.config import settings

    # --- OpenTelemetry ---
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        resource = Resource.create({"service.name": "cvyne-api", "deployment.environment": settings.app_env})
        provider = TracerProvider(resource=resource)

        # Only attach OTLP exporter if endpoint is configured
        otlp_endpoint = getattr(settings, "otlp_endpoint", None)
        if otlp_endpoint:
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))

        trace.set_tracer_provider(provider)

        FastAPIInstrumentor().instrument()

        from core.db import engine
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("OpenTelemetry setup failed: %s", exc)

    # --- Langfuse (wired as litellm callback) ---
    if settings.langfuse_secret_key:
        try:
            import litellm
            from langfuse.callback import CallbackHandler

            langfuse_handler = CallbackHandler(
                secret_key=settings.langfuse_secret_key,
                public_key=settings.langfuse_public_key,
                host=settings.langfuse_host,
            )
            litellm.callbacks = [langfuse_handler]
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Langfuse setup failed: %s", exc)
