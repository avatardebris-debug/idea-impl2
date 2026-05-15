"""Celery task for syncing Google Places reviews."""

from __future__ import annotations

import logging
from datetime import datetime

from celery import Celery

from app.config import settings
from app.services.google_places_client import GooglePlacesClient
from app.services.sentiment_analyzer import analyze_sentiment
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

    # Get place details
    place_details = client.get_place_details(place_id)
    if not place_details:
        logger.warning(f"No place details found for place_id={place_id}")
        return {"status": "error", "message": "No place details found"}

    # Get reviews
    reviews_data = client.get_reviews(place_id)
    if not reviews_data:
        logger.info(f"No reviews found for place_id={place_id}")
        return {"status": "success", "synced": 0, "skipped": 0}

    synced = 0
    skipped = 0

    for review in reviews_data:
        try:
            # Prepare review data
            review_text = review.get("text", "")
            sentiment = analyze_sentiment(review_text)

            review_data = {
                "business_id": place_id,
                "platform": "google",
                "author": review.get("author_name"),
                "rating": review.get("rating"),
                "text": review_text,
                "published_at": datetime.fromtimestamp(review.get("time", 0)) if review.get("time") else None,
                "source_url": review.get("profile_photo_url"),
                "sentiment_score": sentiment["compound"],
                "sentiment_label": sentiment["label"],
            }

            # Insert or skip (idempotent)
            result = insert_or_update(SessionLocal(), review_data)
            if result:
                synced += 1
                try:
                    import asyncio
                    from app.api.ws_manager import ws_manager
                    
                    # Convert datetime to string for JSON serialization
                    if isinstance(review_data.get("published_at"), datetime):
                        review_data["published_at"] = review_data["published_at"].isoformat()
                        
                    asyncio.run(ws_manager.broadcast_to_business(place_id, {
                        "type": "new_review",
                        "data": review_data
                    }))
                except Exception as e:
                    logger.error(f"Failed to broadcast websocket notification: {e}")
            else:
                skipped += 1

        except Exception as e:
            logger.error(f"Error processing review: {e}")
            skipped += 1

    logger.info(f"Sync completed for place_id={place_id}: synced={synced}, skipped={skipped}")
    return {"status": "success", "synced": synced, "skipped": skipped}
