"""Watchlist management with progress tracking and JSON persistence."""

import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import asdict

from .models import WatchlistEntry, Title


class WatchlistManager:
    """Manages the user's watchlist with progress tracking."""

    def __init__(self, storage_path: Optional[str] = None, file_path: Optional[str] = None):
        """
        Initialize the watchlist manager.

        Args:
            storage_path: Path to the JSON file for persistence.
            file_path: Alias for storage_path (for test compatibility).
                          Defaults to ~/.movieseries_tracker_watchlist.json
        """
        # Support both storage_path and file_path parameter names
        path = file_path or storage_path
        if path is None:
            home = os.path.expanduser("~")
            self.storage_path = os.path.join(home, ".movieseries_tracker_watchlist.json")
        else:
            self.storage_path = path
        # Alias for test compatibility
        self.db_path = self.storage_path
        self._entries: Dict[str, WatchlistEntry] = {}
        self._load()
        # Ensure the file exists even if empty
        self._save()

    def _load(self) -> None:
        """Load watchlist from JSON file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                for entry_data in data:
                    entry = WatchlistEntry.from_dict(entry_data)
                    self._entries[entry.title_id] = entry
            except (json.JSONDecodeError, KeyError):
                self._entries = {}

    def _save(self) -> None:
        """Save watchlist to JSON file."""
        entries_list = [entry.to_dict() for entry in self._entries.values()]
        with open(self.storage_path, "w") as f:
            json.dump(entries_list, f, indent=2)

    def add(
        self,
        title_id: str,
        title: str,
        title_type: str,
        year: int,
        notes: str = "",
    ) -> WatchlistEntry:
        """
        Add a title to the watchlist.

        Args:
            title_id: Unique identifier for the title.
            title: Title name.
            title_type: "movie" or "series".
            year: Release year.
            notes: Optional user notes.

        Returns:
            The created or existing WatchlistEntry.
        """
        if title_id in self._entries:
            # Return existing entry if already exists
            return self._entries[title_id]
        now = datetime.now().isoformat()
        entry = WatchlistEntry(
            title_id=title_id,
            title=title,
            title_type=title_type,
            year=year,
            progress="Not started",
            progress_percentage=0.0,
            last_watched_at=None,
            added_at=now,
            notes=notes,
            rating_given=0.0,
        )
        self._entries[title_id] = entry
        self._save()
        return entry

    def get(self, title_id: str) -> Optional[WatchlistEntry]:
        """Get a watchlist entry by title_id."""
        return self._entries.get(title_id)

    def get_all(self) -> List[WatchlistEntry]:
        """Get all watchlist entries."""
        return list(self._entries.values())

    def get_by_title_id(self, title_id: str) -> Optional[WatchlistEntry]:
        """Get a watchlist entry by title_id."""
        return self._entries.get(title_id)

    def get_by_title_name(self, title_name: str) -> Optional[WatchlistEntry]:
        """Get a watchlist entry by title name (case-insensitive)."""
        for entry in self._entries.values():
            if entry.title.lower() == title_name.lower():
                return entry
        return None

    def update_progress(
        self,
        title_id: str,
        progress: str,
        progress_percentage: float,
    ) -> WatchlistEntry:
        """
        Update the progress of a title in the watchlist.

        Args:
            title_id: The title's ID.
            progress: Progress status ("Not started", "Watching", "Completed").
            progress_percentage: Percentage completed (0.0 to 100.0).

        Returns:
            The updated WatchlistEntry.

        Raises:
            ValueError: If title_id is not in the watchlist.
        """
        if title_id not in self._entries:
            raise ValueError(f"Title with id '{title_id}' not found in the watchlist.")
        entry = self._entries[title_id]
        entry.progress = progress
        # Convert 0-1 scale to 0-100 scale if needed
        if progress_percentage <= 1.0 and progress_percentage > 0:
            entry.progress_percentage = progress_percentage * 100
        else:
            entry.progress_percentage = progress_percentage
        entry.last_watched_at = datetime.now().isoformat()
        self._save()
        return entry

    def set_rating(self, title_id: str, rating: float) -> WatchlistEntry:
        """
        Update the user's rating for a title.

        Args:
            title_id: The title's ID.
            rating: Rating given (0.0 to 10.0).

        Returns:
            The updated WatchlistEntry.

        Raises:
            ValueError: If title_id is not in the watchlist.
        """
        if title_id not in self._entries:
            raise ValueError(f"Title with id '{title_id}' not found in the watchlist.")
        entry = self._entries[title_id]
        entry.rating_given = rating
        self._save()
        return entry

    def update_notes(self, title_id: str, notes: str) -> WatchlistEntry:
        """
        Update the notes for a title.

        Args:
            title_id: The title's ID.
            notes: Notes to set.

        Returns:
            The updated WatchlistEntry.

        Raises:
            ValueError: If title_id is not in the watchlist.
        """
        if title_id not in self._entries:
            raise ValueError(f"Title with id '{title_id}' not found in the watchlist.")
        entry = self._entries[title_id]
        entry.notes = notes
        self._save()
        return entry

    def remove(self, title_id: str) -> bool:
        """
        Remove a title from the watchlist.

        Args:
            title_id: The title's ID.

        Returns:
            True if removed, False if not found.
        """
        if title_id in self._entries:
            del self._entries[title_id]
            self._save()
            return True
        return False

    def get_by_status(self, status: str) -> List[WatchlistEntry]:
        """Get all entries with a specific progress status."""
        return [e for e in self._entries.values() if e.progress == status]

    def get_completed(self) -> List[WatchlistEntry]:
        """Get all completed titles."""
        return self.get_by_status("Completed")

    def get_watching(self) -> List[WatchlistEntry]:
        """Get all currently watching titles."""
        return self.get_by_status("Watching")

    def get_not_started(self) -> List[WatchlistEntry]:
        """Get all not started titles."""
        return self.get_by_status("Not started")

    def get_continue_watching(self) -> List[WatchlistEntry]:
        """Get all titles that are currently being watched."""
        return self.get_watching()

    def complete_episode(self, title_id: str, season: int, episode: int) -> WatchlistEntry:
        """
        Mark an episode as completed and update progress.

        Args:
            title_id: The title's ID.
            season: Season number.
            episode: Episode number.

        Returns:
            The updated WatchlistEntry.

        Raises:
            ValueError: If title_id is not in the watchlist.
        """
        if title_id not in self._entries:
            raise ValueError(f"Title with id '{title_id}' not found in the watchlist.")
        entry = self._entries[title_id]
        # Update progress to reflect episode completion
        if entry.progress == "Not started":
            entry.progress = "Watching"
        # Calculate progress based on episode completion
        # For series, each episode adds to progress
        if entry.title_type == "series":
            # Simple heuristic: each episode adds some progress
            # We'll use a small increment to reflect partial completion
            current = entry.progress_percentage
            increment = max(1.0, 100.0 / 10)  # At least 1% per episode
            entry.progress_percentage = min(100.0, current + increment)
        else:
            # For movies, completing an episode means watching
            entry.progress_percentage = max(entry.progress_percentage, 50.0)
        entry.last_watched_at = datetime.now().isoformat()
        self._save()
        return entry

    def get_average_rating(self) -> float:
        """Get the average rating given across all rated titles."""
        rated = [e for e in self._entries.values() if e.rating_given > 0]
        if not rated:
            return 0.0
        return sum(e.rating_given for e in rated) / len(rated)

    def get_stats(self) -> Dict[str, Any]:
        """Get watchlist statistics."""
        total = len(self._entries)
        completed = len(self.get_completed())
        watching = len(self.get_watching())
        not_started = len(self.get_not_started())
        avg_rating = self.get_average_rating()
        return {
            "total": total,
            "completed": completed,
            "watching": watching,
            "not_started": not_started,
            "average_rating": round(avg_rating, 2),
        }

    def to_json(self) -> str:
        """Serialize the entire watchlist to JSON."""
        return json.dumps([e.to_dict() for e in self._entries.values()], indent=2)

    @classmethod
    def from_json(cls, json_str: str, storage_path: Optional[str] = None) -> "WatchlistManager":
        """
        Create a WatchlistManager from a JSON string.

        Args:
            json_str: JSON string containing watchlist entries.
            storage_path: Optional storage path for the new instance.

        Returns:
            A new WatchlistManager instance.
        """
        manager = cls(storage_path=storage_path)
        data = json.loads(json_str)
        for entry_data in data:
            entry = WatchlistEntry.from_dict(entry_data)
            manager._entries[entry.title_id] = entry
        manager._save()
        return manager
