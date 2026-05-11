"""Platform adapter factory for review ingestion.

Provides a unified interface to create and manage platform-specific
review adapters (Google, Yelp, Facebook).
"""

from __future__ import annotations

import logging
from typing import Optional

from app.services.base_platform_adapter import BasePlatformAdapter
from app.services.credential_store import CredentialStore
from app.services.facebook_client import FacebookClient
from app.services.google_client import GoogleClient
from app.services.yelp_client import YelpClient

logger = logging.getLogger(__name__)


class PlatformAdapterFactory:
    """Factory for creating platform-specific review adapters."""

    @staticmethod
    def create(
        platform: str,
        business_id: str,
        credential_store: Optional[CredentialStore] = None,
    ) -> BasePlatformAdapter:
        """Create a platform adapter for the given platform.

        Args:
            platform: Platform name (google, yelp, facebook).
            business_id: Platform-specific business identifier.
            credential_store: Optional credential store for OAuth management.

        Returns:
            A platform adapter instance.

        Raises:
            ValueError: If the platform is not supported.
        """
        platform = platform.lower()

        if platform == "google":
            return GoogleClient(
                place_id=business_id,
                credential_store=credential_store,
            )
        elif platform == "yelp":
            return YelpClient(
                business_id=business_id,
                credential_store=credential_store,
            )
        elif platform == "facebook":
            return FacebookClient(
                page_id=business_id,
                credential_store=credential_store,
            )
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    @staticmethod
    def supported_platforms() -> list[str]:
        """Return list of supported platforms."""
        return ["google", "yelp", "facebook"]
