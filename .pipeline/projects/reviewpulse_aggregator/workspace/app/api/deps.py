"""FastAPI dependencies for the reviews API."""

from __future__ import annotations

from fastapi import Depends, Query
from typing import Optional

from app.database import get_db, Session


def get_page(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
) -> tuple[int, int]:
    """Extract and validate pagination parameters."""
    return (page, page_size)


def get_filters(
    sentiment_label: Optional[str] = Query(None, description="Filter by sentiment label (positive/neutral/negative)"),
    rating_min: Optional[int] = Query(None, ge=1, le=5, description="Minimum rating filter"),
    rating_max: Optional[int] = Query(None, ge=1, le=5, description="Maximum rating filter"),
    date_from: Optional[str] = Query(None, description="Filter by date from (ISO 8601)"),
    date_to: Optional[str] = Query(None, description="Filter by date to (ISO 8601)"),
) -> dict:
    """Extract and validate filter parameters."""
    return {
        "sentiment_label": sentiment_label,
        "rating_min": rating_min,
        "rating_max": rating_max,
        "date_from": date_from,
        "date_to": date_to,
    }
