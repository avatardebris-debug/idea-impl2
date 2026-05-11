"""Movie/Series auto-tracker package."""

from .models import Title, Episode, StreamingService, WatchlistEntry
from .search import StreamingSearchService
from .watchlist import WatchlistManager
from .cli import main

__all__ = [
    "Title",
    "Episode",
    "StreamingService",
    "WatchlistEntry",
    "StreamingSearchService",
    "WatchlistManager",
    "main",
]
