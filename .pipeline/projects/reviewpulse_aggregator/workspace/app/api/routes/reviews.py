"""FastAPI routes for querying reviews."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.review import Review
from app.schemas.review import ReviewResponse, ReviewListResponse
from app.api.deps import get_page, get_filters

router = APIRouter()


@router.get("/reviews", response_model=ReviewListResponse, summary="List reviews")
def list_reviews(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sentiment_label: Optional[str] = Query(None, description="Filter by sentiment label (positive/neutral/negative)"),
    rating_min: Optional[int] = Query(None, ge=1, le=5, description="Minimum rating"),
    rating_max: Optional[int] = Query(None, ge=1, le=5, description="Maximum rating"),
    date_from: Optional[str] = Query(None, description="Filter by date from (ISO 8601)"),
    date_to: Optional[str] = Query(None, description="Filter by date to (ISO 8601)"),
    db: Session = Depends(get_db),
) -> ReviewListResponse:
    """List reviews with optional filters and pagination."""
    query = select(Review)

    # Apply filters
    if sentiment_label:
        query = query.where(Review.sentiment_label == sentiment_label)
    if rating_min is not None:
        query = query.where(Review.rating >= rating_min)
    if rating_max is not None:
        query = query.where(Review.rating <= rating_max)
    if date_from:
        query = query.where(Review.published_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(Review.published_at <= datetime.fromisoformat(date_to))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar_one()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Review.published_at.desc()).offset(offset).limit(page_size)
    reviews = db.execute(query).scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ReviewListResponse(
        items=[ReviewResponse.model_validate(r) for r in reviews],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/reviews/{review_id}", response_model=ReviewResponse, summary="Get a review")
def get_review(
    review_id: int,
    db: Session = Depends(get_db),
) -> ReviewResponse:
    """Get a single review by ID."""
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse.model_validate(review)


@router.get("/reviews/business/{business_id}", response_model=ReviewListResponse, summary="List reviews for a business")
def list_reviews_by_business(
    business_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> ReviewListResponse:
    """List reviews for a specific business."""
    query = select(Review).where(Review.business_id == business_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar_one()

    offset = (page - 1) * page_size
    query = query.order_by(Review.published_at.desc()).offset(offset).limit(page_size)
    reviews = db.execute(query).scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ReviewListResponse(
        items=[ReviewResponse.model_validate(r) for r in reviews],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
