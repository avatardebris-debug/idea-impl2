"""Celery task for syncing Google Places reviews."""

from __future__ import annotations

import logging
from datetime import datetime

from celery import Celery

from app.config import settings
from app.services.google_places_client import GooglePlacesClient
from app.services.sentiment_analyzer import analyze_sentiment
from app.services.normalizer import normalize_review
from app.services.rate_limiter import RateLimiter
from app.repositories.review_repo import insert_or_update
from app.database import SessionLocal

logger = logging.getLogger(__name__)

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
    task_time_limit=300,  # 5 minutes
    broker_connection_retry_on_startup=True,
)


@celery_app.task(
    name="tasks.sync_google_reviews",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def sync_google_reviews(self, place_id: str, business_name: str) -> dict:
    """Sync reviews from Google Places for a given place.

    Args:
        place_id: Google Place ID.
        business_name: Name of the business (for logging).

    Returns:
        Dict with sync results.
    """
    logger.info(f"Starting Google Places sync for place_id={place_id} ({business_name})")

    client = GooglePlacesClient(
        api_key=settings.google_places_api_key,
        default_delay=1.0,
        max_retries=5,
    )

    reviews = client.fetch_reviews(place_id)
    logger.info(f"Fetched {len(reviews)} reviews for {place_id}")

    db = SessionLocal()
    inserted_count = 0
    skipped_count = 0

    try:
        for raw_review in reviews:
            normalized = normalize_review(raw_review)
            if not normalized:
                skipped_count += 1
                continue

            # Run sentiment analysis
            sentiment = analyze_sentiment(normalized["text"] or "")
            normalized["sentiment_score"] = sentiment["compound"]
            normalized["sentiment_label"] = sentiment["label"]
            normalized["published_at"] = datetime.fromtimestamp(
                raw_review.get("time", 0), tz=None
            )

            # Upsert into DB
            result = insert_or_update(db, normalized)
            if result:
                inserted_count += 1
            else:
                skipped_count += 1

            # Rate limiting
            client.rate_limiter.wait()

        db.commit()
        logger.info(
            f"Sync complete for {place_id}: {inserted_count} inserted, {skipped_count} skipped"
        )
        return {
            "place_id": place_id,
            "business_name": business_name,
            "inserted": inserted_count,
            "skipped": skipped_count,
        }
    except Exception as exc:
        db.rollback()
        logger.error(f"Sync failed for {place_id}: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()
