"""Base platform adapter interface for review ingestion.

All platform adapters (Google, Yelp, Facebook) must implement this
interface to produce unified ReviewData objects.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.models.unified_review import ReviewData

logger = logging.getLogger(__name__)


class BasePlatformAdapter(ABC):
    """Abstract base class for platform review adapters."""

    platform_name: str = "base"

    @abstractmethod
    def fetch_reviews(
        self,
        place_id: str,
        limit: Optional[int] = None,
    ) -> list[ReviewData]:
        """Fetch reviews for a given business/place.

        Args:
            place_id: Platform-specific business identifier.
            limit: Optional max number of reviews to fetch.

        Returns:
            List of unified ReviewData objects.
        """
        ...

    @abstractmethod
    def get_place_details(self, place_id: str) -> Optional[dict]:
        """Fetch business details from the platform.

        Args:
            place_id: Platform-specific business identifier.

        Returns:
            Dict with business details (name, address, rating, etc.)
            or None if not found.
        """
        ...

    def validate_credentials(self) -> bool:
        """Validate that the platform credentials are configured correctly.

        Returns:
            True if credentials are valid, False otherwise.
        """
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} platform={self.platform_name}>"
