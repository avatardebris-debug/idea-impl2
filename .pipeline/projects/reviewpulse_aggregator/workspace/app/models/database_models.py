"""Database models for the ReviewPulse Aggregator.

Defines SQLAlchemy ORM models for business profiles, platform credentials,
and aggregated reviews.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class BusinessProfile(Base):
    """Business profile stored in the database."""

    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    category = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    credentials = relationship("PlatformCredential", back_populates="business", cascade="all, delete-orphan")
    reviews = relationship("AggregatedReview", back_populates="business", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<BusinessProfile(id={self.id}, name='{self.name}')>"


class PlatformCredential(Base):
    """OAuth credentials for a platform integration."""

    __tablename__ = "platform_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False, index=True)
    platform = Column(String, nullable=False)  # google, yelp, facebook
    api_key = Column(Text, nullable=True)
    api_secret = Column(Text, nullable=True)
    access_token = Column(Text, nullable=True)
    access_token_expires_at = Column(DateTime, nullable=True)
    refresh_token = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    business = relationship("BusinessProfile", back_populates="credentials")

    def __repr__(self) -> str:
        return f"<PlatformCredential(id={self.id}, platform='{self.platform}')>"


class AggregatedReview(Base):
    """Aggregated review from any platform."""

    __tablename__ = "aggregated_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False, index=True)
    platform = Column(String, nullable=False)  # google, yelp, facebook
    platform_review_id = Column(String, nullable=False)
    author_name = Column(String, nullable=True)
    author_url = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    text = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)
    response_draft = Column(Text, nullable=True)
    is_responded = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    business = relationship("BusinessProfile", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<AggregatedReview(id={self.id}, platform='{self.platform}', rating={self.rating})>"
