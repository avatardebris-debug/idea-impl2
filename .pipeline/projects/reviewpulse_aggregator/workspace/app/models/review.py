"""SQLAlchemy model for the Review entity."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class Review(Base):
    """Review table mapping.

    Each row represents a single review from any platform (Google, Yelp, etc.).
    The review_hash column provides deduplication — upsert logic should skip
    rows with an existing hash.
    """

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False)
    author = Column(String, nullable=True)
    rating = Column(Integer, nullable=True)
    text = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)
    source_url = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String, nullable=True)
    sentiment_feedback = Column(String, nullable=True)
    review_hash = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("review_hash"),
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, business_id={self.business_id}, rating={self.rating})>"
