"""Data module for the Movie/Series auto-tracker.

This module provides access to mock title and platform data.
It re-exports from the services module for backward compatibility.
"""

from .services import get_all_titles, get_all_platforms

__all__ = ["get_all_titles", "get_all_platforms"]
