"""Celery application — Kiro owns this file."""

from celery import Celery

from core.config import settings

celery_app = Celery(
    "cvyne",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    result_expires=86400,  # 24 hours
    worker_prefetch_multiplier=1,  # fair dispatch for long tasks
)

# Beat schedule: retry failed applications every 5 minutes
celery_app.conf.beat_schedule = {}  # No automatic retries — user triggers retry manually
