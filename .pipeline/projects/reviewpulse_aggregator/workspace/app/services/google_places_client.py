"""Google Places API client for fetching business reviews."""

from __future__ import annotations

import logging
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class GooglePlacesClient:
    """Client for Google Places API."""

    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def __init__(
        self,
        api_key: str,
        default_delay: float = 1.0,
        max_retries: int = 5,
    ):
        self.api_key = api_key
        self.default_delay = default_delay
        self.max_retries = max_retries
        self.session = requests.Session()

    def _request(
        self,
        endpoint: str,
        params: dict,
    ) -> Optional[dict]:
        """Make a request with retry and rate-limiting."""
        params["key"] = self.api_key

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Google Places request (attempt {attempt}): {endpoint} {params}")
                response = self.session.get(
                    f"{self.BASE_URL}/{endpoint}",
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response else None
                logger.warning(f"Google Places HTTP error (attempt {attempt}): {status} - {e}")
                if status == 429:
                    # Rate limited — wait longer
                    wait = self.default_delay * (2 ** attempt)
                    logger.info(f"Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if status in (400, 403, 404):
                    logger.error(f"Non-retryable Google Places error: {status}")
                    return None
            except requests.exceptions.RequestException as e:
                logger.warning(f"Google Places request error (attempt {attempt}): {e}")

            if attempt < self.max_retries:
                time.sleep(self.default_delay * attempt)

        logger.error(f"Google Places request failed after {self.max_retries} attempts")
        return None

    def get_place_details(self, place_id: str) -> Optional[dict]:
        """Get details for a specific place."""
        params = {"place_id": place_id, "fields": "place_id,name,formatted_address,rating,review_count"}
        data = self._request("details", params)
        if data and data.get("result"):
            return data["result"]
        return None

    def search_text(self, query: str, location: Optional[tuple[float, float]] = None) -> Optional[dict]:
        """Search for places by text query."""
        params = {"query": query, "type": "restaurant"}
        if location:
            params["location"] = f"{location[0]},{location[1]}"
        data = self._request("textsearch", params)
        if data and data.get("results"):
            return data
        return None

    def get_reviews(self, place_id: str) -> Optional[list[dict]]:
        """Get all reviews for a specific place, following pagination."""
        all_reviews: list[dict] = []
        params = {"place_id": place_id, "fields": "place_id,reviews"}

        while True:
            data = self._request("details", params)
            if not data or not data.get("result"):
                break

            result = data["result"]
            reviews = result.get("reviews")
            if reviews:
                all_reviews.extend(reviews)

            next_page_token = result.get("next_page_token")
            if not next_page_token:
                break

            params = {"place_id": place_id, "fields": "place_id,reviews", "pagetoken": next_page_token}

        return all_reviews if all_reviews else None
