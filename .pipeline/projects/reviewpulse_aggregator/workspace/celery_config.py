"""Celery configuration for ReviewPulse Aggregator."""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "reviewpulse",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    broker_connection_retry_on_startup=True,
)

# Periodic task: sync reviews every hour
celery_app.conf.beat_schedule = {
    # Every day at 8:00 AM UTC
    "daily-email-digest": {
        "task": "tasks.send_daily_digest",
        "schedule": crontab(hour=8, minute=0),
    },
    "sync-reviews-hourly": {
        "task": "tasks.sync_google_reviews",
        "schedule": 3600.0,
        "args": ("PLACE_ID_PLACEHOLDER", "Business Name"),
    },
}

# Import tasks so Celery can discover them
import app.tasks.ingestion_task  # noqa: F401
