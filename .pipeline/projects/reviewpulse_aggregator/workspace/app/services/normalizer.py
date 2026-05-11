"""Normalization pipeline for raw review data."""

from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Optional


def normalize_review(raw: dict) -> dict:
    """Transform a raw review dict (e.g. from Google Places) into a clean dict.

    Handles:
        - HTML entity decoding
        - Whitespace normalization
        - Date parsing from Unix timestamps
        - Field mapping to the unified Review schema

    Args:
        raw: Raw review dict from an external API.

    Returns:
        Dict with keys matching the Review model schema.
    """
    # Decode HTML entities
    text = raw.get("text", "") or ""
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Parse published_at from Unix timestamp
    published_at = None
    time_val = raw.get("time")
    if time_val:
        try:
            published_at = datetime.fromtimestamp(time_val)
        except (ValueError, OSError, OverflowError):
            published_at = None

    return {
        "business_id": raw.get("place_id", ""),
        "platform": raw.get("platform", "google"),
        "author": raw.get("author_name", raw.get("author", "")),
        "rating": _parse_rating(raw.get("rating")),
        "text": text,
        "published_at": published_at,
        "source_url": raw.get("profile_photo_url", raw.get("source_url")),
        "sentiment_score": None,
        "sentiment_label": None,
    }


def _parse_rating(value) -> Optional[int]:
    """Convert a rating value to an integer 1-5."""
    if value is None:
        return None
    try:
        rating = int(float(value))
        return max(1, min(5, rating))
    except (ValueError, TypeError):
        return None
