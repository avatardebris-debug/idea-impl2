"""Google Places API client for fetching business reviews.

Implements the Google Places API New JSON endpoints for business details
and reviews.
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


class GoogleClient(BasePlatformAdapter):
    """Google Places API client for business reviews."""

    platform_name = "google"
    BASE_URL = "https://places.googleapis.com/v1"

    def __init__(
        self,
        place_id: str,
        credential_store: Optional[CredentialStore] = None,
        default_delay: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.place_id = place_id
        self.default_delay = default_delay or settings.google_places_default_delay
        self.max_retries = max_retries or settings.google_places_max_retries
        self.session = requests.Session()
        self.credential_store = credential_store
        self.oauth_manager = OAuthManager(credential_store) if credential_store else None

    def _get_headers(self) -> dict:
        """Get the request headers with API key."""
        api_key = settings.google_places_api_key
        if not api_key:
            raise ValueError("Google Places API key not configured")
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
        }

    def _request_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
    ) -> dict:
        """Make an HTTP request with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                headers = self._get_headers()
                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=30,
                )

                if response.status_code == 429:
                    wait_time = self.default_delay * (2 ** attempt)
                    logger.warning(f"Google rate limit hit, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if response.status_code in (401, 403):
                    logger.error(f"Google auth error: {e}")
                    raise
                last_error = e
            except requests.exceptions.RequestException as e:
                last_error = e

            if attempt < self.max_retries - 1:
                wait_time = self.default_delay * (2 ** attempt)
                logger.warning(f"Google request failed (attempt {attempt + 1}), retrying in {wait_time}s")
                time.sleep(wait_time)

        raise last_error

    def fetch_reviews(
        self,
        place_id: str,
        limit: Optional[int] = None,
    ) -> list[ReviewData]:
        """Fetch reviews for a Google business.

        Args:
            place_id: Google Place ID.
            limit: Optional max number of reviews.

        Returns:
            List of unified ReviewData objects.
        """
        reviews = []
        offset = 0
        page_limit = 20  # Google API max per request

        while True:
            current_limit = min(page_limit, (limit or 1000) - offset) if limit else page_limit
            if offset >= (limit or 1000):
                break

            json_body = {
                "placeIds": [place_id],
                "languageCode": "en",
                "reviewMaxCount": current_limit,
                "reviewSortBuckets": [
                    {
                        "maxRating": 5,
                        "minRating": 1,
                    }
                ],
            }

            data = self._request_with_retry(
                "POST",
                f"{self.BASE_URL}/places:batchGetReviews",
                json_body=json_body,
            )

            place_reviews = data.get("placeReviews", [])
            if not place_reviews:
                break

            for place_review in place_reviews:
                for review in place_review.get("reviews", []):
                    review_data = self._parse_review(review, place_id)
                    if review_data:
                        reviews.append(review_data)

            offset += current_limit
            if len(reviews) >= (limit or 1000):
                break

            time.sleep(self.default_delay)

        return reviews

    def get_place_details(self, place_id: str) -> Optional[dict]:
        """Fetch business details from Google Places.

        Args:
            place_id: Google Place ID.

        Returns:
            Dict with business details or None.
        """
        try:
            data = self._request_with_retry(
                "GET",
                f"{self.BASE_URL}/places/{place_id}",
                params={
                    "languageCode": "en",
                    "requiredFields": "displayName,formattedAddress,phoneNumber,websiteUri,primaryCategory,rating,reviewCount,location",
                },
            )
            return {
                "name": data.get("displayName"),
                "address": data.get("formattedAddress"),
                "phone": data.get("phoneNumber"),
                "website": data.get("websiteUri"),
                "rating": data.get("rating"),
                "review_count": data.get("reviewCount"),
                "category": data.get("primaryCategory", {}).get("displayName"),
                "latitude": data.get("location", {}).get("latitude"),
                "longitude": data.get("location", {}).get("longitude"),
            }
        except Exception as e:
            logger.error(f"Failed to fetch Google business details: {e}")
            return None

    def _parse_review(self, google_review: dict, place_id: str) -> Optional[ReviewData]:
        """Parse a Google review into a unified ReviewData object."""
        try:
            from datetime import datetime as dt

            # Google uses seconds since epoch in some fields
            time = google_review.get("time")
            published_at = None
            if time:
                published_at = dt.fromtimestamp(time)

            author = google_review.get("user", {})

            return ReviewData(
                business_id=place_id,
                platform="google",
                review_id=google_review.get("name", "").split("/")[-1],
                author_name=author.get("displayName"),
                author_url=author.get("uri"),
                rating=google_review.get("rating"),
                text=google_review.get("text"),
                published_at=published_at,
                source_url=google_review.get("originalText"),
            )
        except Exception as e:
            logger.error(f"Failed to parse Google review: {e}")
            return None

    def validate_credentials(self) -> bool:
        """Validate Google credentials by making a test request."""
        try:
            self._get_headers()
            return True
        except Exception:
            return False
