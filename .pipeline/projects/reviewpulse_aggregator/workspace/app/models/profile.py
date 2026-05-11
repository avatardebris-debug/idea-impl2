"""SQLAlchemy models for business profiles and platform credentials."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class BusinessProfile(Base):
    """Business profile model.

    Represents a local business whose reviews are being aggregated.
    """

    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    category = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    credentials = relationship("PlatformCredential", back_populates="business", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<BusinessProfile(id={self.id}, name={self.name})>"


class PlatformCredential(Base):
    """Platform-specific API credentials for a business.

    Stores API keys/tokens for platforms like Google, Yelp, Facebook, etc.
    """

    __tablename__ = "platform_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False, index=True)
    platform = Column(String, nullable=False)  # google, yelp, facebook
    api_key = Column(Text, nullable=True)
    api_secret = Column(Text, nullable=True)
    access_token = Column(Text, nullable=True)
    access_token_expires_at = Column(DateTime, nullable=True)
    refresh_token = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    business = relationship("BusinessProfile", back_populates="credentials")

    def __repr__(self) -> str:
        return f"<PlatformCredential(id={self.id}, platform={self.platform}, business_id={self.business_id})>"
