"""Facebook Graph API client for fetching business reviews.

Implements the Facebook Graph API endpoints for business pages,
reviews, and ratings.
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


class FacebookClient(BasePlatformAdapter):
    """Facebook Graph API client for business reviews."""

    platform_name = "facebook"
    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(
        self,
        page_id: str,
        credential_store: Optional[CredentialStore] = None,
        default_delay: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.page_id = page_id
        self.default_delay = default_delay or settings.facebook_default_delay
        self.max_retries = max_retries or settings.facebook_max_retries
        self.session = requests.Session()
        self.credential_store = credential_store
        self.oauth_manager = OAuthManager(credential_store) if credential_store else None

    def _get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        token = None
        if self.oauth_manager:
            token = self.oauth_manager.get_valid_token(
                business_id=int(self.page_id),
                platform="facebook",
            )

        if token:
            return token

        # Fallback to app-level token
        if settings.facebook_app_id and settings.facebook_app_secret:
            try:
                response = requests.get(
                    "https://graph.facebook.com/v18.0/oauth/access_token",
                    params={
                        "client_id": settings.facebook_app_id,
                        "client_secret": settings.facebook_app_secret,
                        "grant_type": "client_credentials",
                    },
                    timeout=30,
                )
                response.raise_for_status()
                return response.json()["access_token"]
            except Exception as e:
                logger.error(f"Failed to get app-level token: {e}")

        raise ValueError("Facebook API credentials not configured")

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
                access_token = self._get_access_token()
                if params is None:
                    params = {}
                params["access_token"] = access_token

                response = self.session.request(
                    method,
                    url,
                    params=params,
                    timeout=30,
                )

                if response.status_code == 429:
                    wait_time = self.default_delay * (2 ** attempt)
                    logger.warning(f"Facebook rate limit hit, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if response.status_code in (401, 403):
                    logger.error(f"Facebook auth error: {e}")
                    raise
                last_error = e
            except requests.exceptions.RequestException as e:
                last_error = e

            if attempt < self.max_retries - 1:
                wait_time = self.default_delay * (2 ** attempt)
                logger.warning(f"Facebook request failed (attempt {attempt + 1}), retrying in {wait_time}s")
                time.sleep(wait_time)

        raise last_error

    def fetch_reviews(
        self,
        page_id: str,
        limit: Optional[int] = None,
    ) -> list[ReviewData]:
        """Fetch reviews for a Facebook business page.

        Args:
            page_id: Facebook page ID.
            limit: Optional max number of reviews.

        Returns:
            List of unified ReviewData objects.
        """
        reviews = []
        offset = 0
        page_limit = 25  # Facebook API default

        while True:
            current_limit = min(page_limit, (limit or 1000) - offset) if limit else page_limit
            if offset >= (limit or 1000):
                break

            params = {
                "fields": "id,from,message,rating,created_time",
                "limit": current_limit,
                "offset": offset,
            }

            data = self._request_with_retry(
                "GET",
                f"{self.BASE_URL}/{page_id}/ratings",
                params=params,
            )

            for review in data.get("data", []):
                review_data = self._parse_review(review, page_id)
                if review_data:
                    reviews.append(review_data)

            offset += current_limit
            paging = data.get("paging", {})
            next_url = paging.get("next")
            if not next_url:
                break

            time.sleep(self.default_delay)

        return reviews

    def get_place_details(self, page_id: str) -> Optional[dict]:
        """Fetch business details from Facebook.

        Args:
            page_id: Facebook page ID.

        Returns:
            Dict with business details or None.
        """
        try:
            data = self._request_with_retry(
                "GET",
                f"{self.BASE_URL}/{page_id}",
                params={
                    "fields": "name,about,phone,website,location,rating_count,overall_star_rating",
                },
            )
            return {
                "name": data.get("name"),
                "address": data.get("location", {}).get("street") + ", " + data.get("location", {}).get("city") if data.get("location") else None,
                "phone": data.get("phone"),
                "website": data.get("website"),
                "rating": data.get("overall_star_rating"),
                "review_count": data.get("rating_count"),
                "category": data.get("category"),
            }
        except Exception as e:
            logger.error(f"Failed to fetch Facebook business details: {e}")
            return None

    def _parse_review(self, fb_review: dict, page_id: str) -> Optional[ReviewData]:
        """Parse a Facebook review into a unified ReviewData object."""
        try:
            from datetime import datetime as dt
            from datetime import timezone

            created_time = fb_review.get("created_time")
            published_at = None
            if created_time:
                published_at = dt.fromisoformat(created_time.replace("Z", "+00:00"))

            from_user = fb_review.get("from", {})

            return ReviewData(
                business_id=page_id,
                platform="facebook",
                review_id=fb_review.get("id", ""),
                author_name=from_user.get("name"),
                author_url=f"https://www.facebook.com/{from_user.get('id')}" if from_user.get("id") else None,
                rating=fb_review.get("rating"),
                text=fb_review.get("message"),
                published_at=published_at,
                source_url=f"https://www.facebook.com/{page_id}/ratings",
            )
        except Exception as e:
            logger.error(f"Failed to parse Facebook review: {e}")
            return None

    def validate_credentials(self) -> bool:
        """Validate Facebook credentials by making a test request."""
        try:
            self._get_access_token()
            return True
        except Exception:
            return False
