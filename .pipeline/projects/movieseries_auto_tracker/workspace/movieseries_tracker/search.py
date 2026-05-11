"""Streaming search module for querying mock/streaming data sources."""

import os
from typing import List, Optional
from .models import Title, StreamingService
from .services import get_all_titles, get_all_platforms


class StreamingSearchService:
    """Searches across streaming platforms for movie/series titles."""

    def __init__(self):
        self._titles = get_all_titles()
        self._platforms = get_all_platforms()

    def search(
        self,
        query: str,
        title_type: Optional[str] = None,
        platform: Optional[str] = None,
        availability: Optional[str] = None,
    ) -> List[Title]:
        """
        Search for titles by query string with optional filters.

        Args:
            query: Search term (matched against title, genres, description).
            title_type: Filter by "movie" or "series".
            platform: Filter by streaming service name.
            availability: Filter by "paid", "free", or "freemium".

        Returns:
            List of matching Title objects.
        """
        results = []
        query_lower = query.lower()

        for title in self._titles:
            # Filter by title type
            if title_type and title.type != title_type:
                continue

            # Filter by platform
            if platform:
                platform_lower = platform.lower()
                matching_services = [
                    s for s in title.streaming_services
                    if platform_lower in s.name.lower()
                ]
                if not matching_services:
                    continue

            # Filter by availability
            if availability:
                avail_lower = availability.lower()
                matching_services = [
                    s for s in title.streaming_services
                    if s.type.lower() == avail_lower
                ]
                if not matching_services:
                    continue

            # Text search across title, genres, description
            searchable = f"{title.title} {' '.join(title.genres)} {title.description}".lower()
            if query_lower in searchable:
                results.append(title)

        return results

    def search_by_platform(
        self,
        platform: str,
        title_type: Optional[str] = None,
    ) -> List[Title]:
        """
        Get all titles available on a specific platform.

        Args:
            platform: Streaming service name.
            title_type: Optional filter by "movie" or "series".

        Returns:
            List of Title objects available on the platform.
        """
        results = []
        platform_lower = platform.lower()

        for title in self._titles:
            if title_type and title.type != title_type:
                continue

            matching_services = [
                s for s in title.streaming_services
                if platform_lower in s.name.lower()
            ]
            if matching_services:
                results.append(title)

        return results

    def get_platforms(self) -> List[StreamingService]:
        """Return all available streaming platforms."""
        return list(self._platforms.values())

    def get_all_titles(self) -> List[Title]:
        """Return all available titles."""
        return self._titles

    def get_title_by_id(self, title_id: str) -> Optional[Title]:
        """Get a title by its ID."""
        for title in self._titles:
            if title.id == title_id:
                return title
        return None

    def _get_db_path(self) -> str:
        """Return the path to the database file."""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "titles.json")
