"""Review repository with idempotent upsert logic."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review import Review


def _compute_hash(
    business_id: str,
    platform: str,
    author: str,
    text: str,
) -> str:
    """Compute a deterministic hash for deduplication."""
    key = f"{business_id}|{platform}|{author}|{text}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def insert_or_update(db: Session, review_data: dict) -> Optional[Review]:
    """Insert a new review or skip if a review with the same hash exists.

    Args:
        db: SQLAlchemy session.
        review_data: Dict with keys matching the Review model fields.

    Returns:
        The newly inserted Review object, or None if a duplicate was found.
    """
    # Compute hash from the review data
    review_hash = _compute_hash(
        business_id=review_data["business_id"],
        platform=review_data["platform"],
        author=review_data.get("author", ""),
        text=review_data.get("text", ""),
    )

    # Check for existing review with the same hash
    existing = db.execute(
        select(Review).where(Review.review_hash == review_hash)
    ).scalar_one_or_none()

    if existing:
        return None

    # Build the review object
    review = Review(
        business_id=review_data["business_id"],
        platform=review_data["platform"],
        author=review_data.get("author"),
        rating=review_data.get("rating"),
        text=review_data.get("text"),
        published_at=review_data.get("published_at"),
        source_url=review_data.get("source_url"),
        sentiment_score=review_data.get("sentiment_score"),
        sentiment_label=review_data.get("sentiment_label"),
        review_hash=review_hash,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(review)
    db.flush()
    db.refresh(review)
    return review
