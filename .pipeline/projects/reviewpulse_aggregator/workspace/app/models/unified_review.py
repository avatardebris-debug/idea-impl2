"""Unified review model shared across all platform adapters.

This module defines the canonical ReviewData schema that all platform
adapters (Google, Yelp, Facebook) must produce.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ReviewData:
    """Canonical review representation.

    All platform adapters transform their native review format into this
    unified schema before persisting or further processing.
    """

    # Identity
    business_id: str
    platform: str  # google, yelp, facebook
    review_id: str  # platform-specific unique ID
    author_name: Optional[str] = None
    author_url: Optional[str] = None

    # Content
    rating: Optional[int] = field(default=None)  # 1-5
    text: Optional[str] = None
    title: Optional[str] = None

    # Metadata
    published_at: Optional[datetime] = None
    source_url: Optional[str] = None

    # Derived fields (filled by downstream services)
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None

    def __post_init__(self):
        # Normalize rating to 1-5
        if self.rating is not None:
            self.rating = max(1, min(5, int(self.rating)))

    def to_dict(self) -> dict:
        """Serialize to dict for DB insertion."""
        return {
            "business_id": self.business_id,
            "platform": self.platform,
            "author": self.author_name,
            "rating": self.rating,
            "text": self.text,
            "published_at": self.published_at,
            "source_url": self.source_url,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "review_hash": self._compute_hash(),
        }

    def _compute_hash(self) -> str:
        """Compute a deterministic hash for deduplication."""
        import hashlib

        key = f"{self.business_id}|{self.platform}|{self.review_id}|{self.text or ''}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()
