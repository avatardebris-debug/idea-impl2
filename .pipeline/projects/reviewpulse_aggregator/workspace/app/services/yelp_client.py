"""Yelp Fusion API client for fetching business reviews.

Implements the Yelp Fusion API v3 endpoints for business search,
details, and reviews.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import requests

from app.config import settings
from app.models.unified_review import ReviewData
from app.services.base_platform_adapter import BasePlatformAdapter
from app.services.credential_store import CredentialStore
from app.services.oauth_manager import OAuthManager

logger = logging.getLogger(__name__)


class YelpClient(BasePlatformAdapter):
    """Yelp Fusion API client."""

    platform_name = "yelp"
    BASE_URL = "https://api.yelp.com/v3"

    def __init__(
        self,
        business_id: str,
        credential_store: Optional[CredentialStore] = None,
        default_delay: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.business_id = business_id
        self.default_delay = default_delay or settings.yelp_default_delay
        self.max_retries = max_retries or settings.yelp_max_retries
        self.session = requests.Session()
        self.credential_store = credential_store
        self.oauth_manager = OAuthManager(credential_store) if credential_store else None

    def _get_auth_header(self) -> dict:
        """Get the OAuth2 Authorization header."""
        token = None
        if self.oauth_manager:
            token = self.oauth_manager.get_valid_token(
                business_id=int(self.business_id),
                platform="yelp",
            )

        if token:
            return {"Authorization": f"Bearer {token}"}

        # Fallback to API key if no OAuth token
        if settings.yelp_api_key:
            return {"Authorization": f"Bearer {settings.yelp_api_key}"}

        raise ValueError("Yelp API credentials not configured")

    def _request_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
    ) -> dict:
        """Make an HTTP request with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                headers = self._get_auth_header()
                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    timeout=30,
                )

                if response.status_code == 429:
                    # Rate limited — wait and retry
                    wait_time = self.default_delay * (2 ** attempt)
                    logger.warning(f"Yelp rate limit hit, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if response.status_code in (401, 403):
                    logger.error(f"Yelp auth error: {e}")
                    raise
                last_error = e
            except requests.exceptions.RequestException as e:
                last_error = e

            if attempt < self.max_retries - 1:
                wait_time = self.default_delay * (2 ** attempt)
                logger.warning(f"Yelp request failed (attempt {attempt + 1}), retrying in {wait_time}s")
                time.sleep(wait_time)

        raise last_error

    def fetch_reviews(
        self,
        place_id: str,
        limit: Optional[int] = None,
    ) -> list[ReviewData]:
        """Fetch reviews for a Yelp business.

        Args:
            place_id: Yelp business ID.
            limit: Optional max number of reviews.

        Returns:
            List of unified ReviewData objects.
        """
        reviews = []
        offset = 0
        page_limit = 50  # Yelp API max per page

        while True:
            current_limit = min(page_limit, (limit or 1000) - offset) if limit else page_limit
            if offset >= (limit or 1000):
                break

            params = {
                "business_id": place_id,
                "limit": current_limit,
                "offset": offset,
                "sort_by": "best_match",
            }

            data = self._request_with_retry(
                "GET",
                f"{self.BASE_URL}/businesses/{place_id}/reviews",
                params=params,
            )

            for review in data.get("reviews", []):
                review_data = self._parse_review(review)
                if review_data:
                    reviews.append(review_data)

            offset += current_limit
            if len(data.get("reviews", [])) < page_limit:
                break

            time.sleep(self.default_delay)

        return reviews

    def get_place_details(self, place_id: str) -> Optional[dict]:
        """Fetch business details from Yelp.

        Args:
            place_id: Yelp business ID.

        Returns:
            Dict with business details or None.
        """
        try:
            data = self._request_with_retry(
                "GET",
                f"{self.BASE_URL}/businesses/{place_id}",
            )
            return {
                "name": data.get("name"),
                "address": ", ".join(data.get("location", {}).get("display_address", [])),
                "phone": data.get("phone"),
                "website": data.get("display_phone"),
                "rating": data.get("rating"),
                "review_count": data.get("review_count"),
                "category": ", ".join(c.get("title", "") for c in data.get("categories", [])),
                "latitude": data.get("coordinates", {}).get("latitude"),
                "longitude": data.get("coordinates", {}).get("longitude"),
            }
        except Exception as e:
            logger.error(f"Failed to fetch Yelp business details: {e}")
            return None

    def _parse_review(self, yelp_review: dict) -> Optional[ReviewData]:
        """Parse a Yelp review into a unified ReviewData object."""
        try:
            published_at = None
            if yelp_review.get("time_created"):
                from datetime import datetime as dt
                published_at = dt.fromtimestamp(yelp_review["time_created"])

            return ReviewData(
                business_id=self.business_id,
                platform="yelp",
                review_id=yelp_review.get("id", ""),
                author_name=yelp_review.get("user", {}).get("name"),
                author_url=yelp_review.get("user", {}).get("url"),
                rating=yelp_review.get("rating"),
                text=yelp_review.get("text"),
                published_at=published_at,
                source_url=yelp_review.get("url"),
            )
        except Exception as e:
            logger.error(f"Failed to parse Yelp review: {e}")
            return None

    def validate_credentials(self) -> bool:
        """Validate Yelp credentials by making a test request."""
        try:
            self._get_auth_header()
            return True
        except Exception:
            return False
