"""CLI script for triggering a manual review sync."""

from __future__ import annotations

import argparse
import logging
import sys

# Ensure workspace is on sys.path
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.tasks.ingestion_task import sync_google_reviews
from app.database import SessionLocal
from app.repositories.review_repo import insert_or_update
from app.services.google_places_client import GooglePlacesClient
from app.services.sentiment_analyzer import analyze_sentiment
from app.services.normalizer import normalize_review
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manually sync reviews for a Google Place.")
    parser.add_argument("place_id", help="Google Place ID to sync reviews for")
    parser.add_argument("--business-name", default="Unknown Business", help="Business name (for logging)")
    args = parser.parse_args()

    logger.info(f"Manual sync triggered for place_id={args.place_id}")

    client = GooglePlacesClient(
        api_key=settings.google_places_api_key,
        default_delay=1.0,
        max_retries=5,
    )

    place_details = client.get_place_details(args.place_id)
    if not place_details:
        logger.warning(f"No place details found for place_id={args.place_id}")
        sys.exit(1)

    reviews_data = client.get_reviews(args.place_id)
    if not reviews_data:
        logger.info(f"No reviews found for place_id={args.place_id}")
        sys.exit(0)

    synced = 0
    skipped = 0

    for review in reviews_data:
        try:
            normalized = normalize_review(review)
            sentiment = analyze_sentiment(normalized["text"] or "")
            normalized["sentiment_score"] = sentiment["compound"]
            normalized["sentiment_label"] = sentiment["label"]

            db = SessionLocal()
            try:
                result = insert_or_update(db, normalized)
                if result:
                    synced += 1
                else:
                    skipped += 1
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error processing review: {e}")
            skipped += 1

    logger.info(f"Manual sync complete: synced={synced}, skipped={skipped}")


if __name__ == "__main__":
    main()
