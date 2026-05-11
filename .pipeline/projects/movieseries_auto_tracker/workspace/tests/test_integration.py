"""Integration tests for the movieseries_tracker package."""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List

# Add the workspace to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "workspace"))

from movieseries_tracker.models import Title, Episode, StreamingService, WatchlistEntry
from movieseries_tracker.search import StreamingSearchService
from movieseries_tracker.watchlist import WatchlistManager
from movieseries_tracker.data import get_all_titles, get_all_platforms


class TestModels:
    """Test the data models."""

    def test_title_creation(self):
        """Test creating a Title."""
        title = Title(
            id="t001",
            title="Test Title",
            type="movie",
            year=2020,
            description="A test title",
            rating=8.0,
            genres=["Action"],
            streaming_services=[
                StreamingService(name="Test", url="https://test.com", type="paid"),
            ],
            seasons=1,
            episodes=[],
            poster_url="https://test.com/poster.jpg",
            affiliate_link="https://test.com/watch",
        )
        assert title.id == "t001"
        assert title.title == "Test Title"
        assert title.type == "movie"
        assert title.year == 2020
        assert title.rating == 8.0
        assert title.genres == ["Action"]
        assert len(title.streaming_services) == 1
        assert title.streaming_services[0].name == "Test"
        assert title.seasons == 1
        assert title.episodes == []
        assert title.poster_url == "https://test.com/poster.jpg"
        assert title.affiliate_link == "https://test.com/watch"

    def test_episode_creation(self):
        """Test creating an Episode."""
        episode = Episode(
            season=1,
            episode=1,
            title="Test Episode",
            description="A test episode",
            duration_minutes=30,
        )
        assert episode.season == 1
        assert episode.episode == 1
        assert episode.title == "Test Episode"
        assert episode.description == "A test episode"
        assert episode.duration_minutes == 30

    def test_streaming_service_creation(self):
        """Test creating a StreamingService."""
        service = StreamingService(
            name="Test",
            url="https://test.com",
            type="paid",
        )
        assert service.name == "Test"
        assert service.url == "https://test.com"
        assert service.type == "paid"

    def test_watchlist_entry_creation(self):
        """Test creating a WatchlistEntry."""
        entry = WatchlistEntry(
            title_id="t001",
            title="Test Title",
            title_type="movie",
            year=2020,
        )
        assert entry.title_id == "t001"
        assert entry.title == "Test Title"
        assert entry.title_type == "movie"
        assert entry.year == 2020
        assert entry.progress == "Not started"
        assert entry.progress_percentage == 0.0
        assert entry.last_watched_at is None
        assert entry.added_at is not None
        assert entry.notes == ""
        assert entry.rating_given == 0


class TestDataModule:
    """Test the data module."""

    def test_get_all_titles(self):
        """Test getting all mock titles."""
        titles = get_all_titles()
        assert len(titles) > 0
        assert isinstance(titles[0], Title)

    def test_get_all_platforms(self):
        """Test getting all platforms."""
        platforms = get_all_platforms()
        assert len(platforms) > 0
        assert isinstance(platforms, dict)


class TestSearchService:
    """Test the search service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.search_service = StreamingSearchService()

    def test_search_by_title(self):
        """Test searching by title."""
        results = self.search_service.search(query="Stranger Things")
        assert len(results) == 1
        assert results[0].title == "Stranger Things"

    def test_search_by_genre(self):
        """Test searching by genre."""
        results = self.search_service.search(query="Sci-Fi")
        assert len(results) > 0
        for r in results:
            assert "Sci-Fi" in r.genres

    def test_search_by_type(self):
        """Test searching by type."""
        results = self.search_service.search(query="", title_type="movie")
        assert all(r.type == "movie" for r in results)

    def test_search_by_platform(self):
        """Test searching by platform."""
        results = self.search_service.search(query="", platform="Netflix")
        assert all("Netflix" in [s.name for s in r.streaming_services] for r in results)

    def test_search_by_availability(self):
        """Test searching by availability."""
        results = self.search_service.search(query="", availability="free")
        assert all(any(s.type == "free" for s in r.streaming_services) for r in results)

    def test_search_no_results(self):
        """Test searching with no results."""
        results = self.search_service.search(query="nonexistent title xyz123")
        assert len(results) == 0

    def test_search_case_insensitive(self):
        """Test that search is case insensitive."""
        results1 = self.search_service.search(query="stranger things")
        results2 = self.search_service.search(query="STRANGER THINGS")
        assert len(results1) == len(results2)
        assert results1[0].title == results2[0].title


class TestWatchlistManager:
    """Test the watchlist manager."""

    def setup_method(self):
        """Set up test fixtures with a temporary file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.temp_file.close()
        self.watchlist_manager = WatchlistManager(file_path=self.temp_file.name)

    def teardown_method(self):
        """Clean up temporary file."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_add_title(self):
        """Test adding a title to the watchlist."""
        entry = self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="movie",
            year=2020,
        )
        assert entry.title == "Test Title"
        assert entry.title_type == "movie"
        assert entry.progress == "Not started"

    def test_add_duplicate_title(self):
        """Test adding a duplicate title."""
        self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="movie",
            year=2020,
        )
        # Adding again should not create a duplicate
        entry = self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="movie",
            year=2020,
        )
        assert entry is not None
        # The manager should return the existing entry
        entries = self.watchlist_manager.get_all()
        assert len(entries) == 1

    def test_remove_title(self):
        """Test removing a title from the watchlist."""
        self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="movie",
            year=2020,
        )
        self.watchlist_manager.remove("t001")
        entries = self.watchlist_manager.get_all()
        assert len(entries) == 0

    def test_get_by_title_id(self):
        """Test getting a title by ID."""
        self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="movie",
            year=2020,
        )
        entry = self.watchlist_manager.get_by_title_id("t001")
        assert entry is not None
        assert entry.title == "Test Title"

    def test_get_by_title_name(self):
        """Test getting a title by name."""
        self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="movie",
            year=2020,
        )
        entry = self.watchlist_manager.get_by_title_name("Test Title")
        assert entry is not None
        assert entry.title == "Test Title"

    def test_set_rating(self):
        """Test setting a rating."""
        entry = self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="movie",
            year=2020,
        )
        self.watchlist_manager.set_rating("t001", 9.0)
        entry = self.watchlist_manager.get_by_title_id("t001")
        assert entry.rating_given == 9.0

    def test_update_notes(self):
        """Test updating notes."""
        entry = self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="movie",
            year=2020,
        )
        self.watchlist_manager.update_notes("t001", "Test notes")
        entry = self.watchlist_manager.get_by_title_id("t001")
        assert entry.notes == "Test notes"

    def test_update_progress(self):
        """Test updating progress."""
        entry = self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="series",
            year=2020,
        )
        self.watchlist_manager.update_progress("t001", "Watching", 50.0)
        entry = self.watchlist_manager.get_by_title_id("t001")
        assert entry.progress == "Watching"
        assert entry.progress_percentage == 50.0

    def test_complete_episode(self):
        """Test completing an episode."""
        entry = self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="series",
            year=2020,
        )
        self.watchlist_manager.complete_episode("t001", 1, 1)
        entry = self.watchlist_manager.get_by_title_id("t001")
        assert entry.progress == "Watching"
        assert entry.progress_percentage > 0

    def test_get_continue_watching(self):
        """Test getting continue watching titles."""
        self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="series",
            year=2020,
        )
        self.watchlist_manager.update_progress("t001", "Watching", 50.0)
        entries = self.watchlist_manager.get_continue_watching()
        assert len(entries) == 1
        assert entries[0].title == "Test Title"

    def test_persistence(self):
        """Test that data persists to file."""
        self.watchlist_manager.add(
            title_id="t001",
            title="Test Title",
            title_type="movie",
            year=2020,
        )
        # Create a new manager with the same file
        new_manager = WatchlistManager(file_path=self.temp_file.name)
        entries = new_manager.get_all()
        assert len(entries) == 1
        assert entries[0].title == "Test Title"


class TestCLI:
    """Test the CLI."""

    def test_cli_search(self):
        """Test the CLI search command."""
        from movieseries_tracker.cli import main
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            main(["search", "Stranger Things"])
        output = f.getvalue()
        assert "Stranger Things" in output

    def test_cli_watchlist_empty(self):
        """Test the CLI watchlist command with empty watchlist."""
        from movieseries_tracker.cli import main
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            main(["watchlist"])
        output = f.getvalue()
        assert "empty" in output.lower() or "watchlist" in output.lower()

    def test_cli_add(self):
        """Test the CLI add command."""
        from movieseries_tracker.cli import main
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            main(["add", "Test Title", "--notes", "Test notes"])
        output = f.getvalue()
        assert "Added" in output

    def test_cli_details(self):
        """Test the CLI details command."""
        from movieseries_tracker.cli import main
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            main(["details", "Stranger Things"])
        output = f.getvalue()
        assert "Stranger Things" in output


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
