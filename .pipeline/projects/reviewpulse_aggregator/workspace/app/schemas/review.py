"""Pydantic schemas for Review data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    """Base fields shared across all review schemas."""

    business_id: str
    platform: str
    author: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    text: Optional[str] = None
    published_at: Optional[datetime] = None
    source_url: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""

    review_hash: str = Field(..., description="Unique hash for deduplication")


class ReviewUpdate(BaseModel):
    """Schema for updating an existing review."""

    rating: Optional[int] = Field(None, ge=1, le=5)
    text: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None


class ReviewResponse(ReviewBase):
    """Schema returned to API consumers."""

    id: int
    review_hash: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ReviewListResponse(BaseModel):
    """Paginated list of reviews."""

    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
