"""Tests for watchlist module."""

import json
import os
import tempfile
import pytest
from movieseries_tracker.watchlist import WatchlistManager
from movieseries_tracker.models import WatchlistEntry


class TestWatchlistManager:
    def _create_temp_db(self):
        """Create a temporary database file for testing."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(path, "w") as f:
            json.dump([], f)
        return path

    def test_create_manager(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            assert mgr.db_path == db_path
            entries = mgr.get_all()
            assert len(entries) == 0
        finally:
            os.unlink(db_path)

    def test_add_entry(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            entry = mgr.add(
                title_id="t1",
                title="Inception",
                title_type="movie",
                year=2010,
            )
            assert entry.title_id == "t1"
            assert entry.title == "Inception"
            assert entry.title_type == "movie"
            assert entry.year == 2010
            assert entry.progress == "Not started"
            assert entry.rating_given == 0
            assert entry.notes == ""
            assert entry.added_at is not None

            entries = mgr.get_all()
            assert len(entries) == 1
        finally:
            os.unlink(db_path)

    def test_add_multiple_entries(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            mgr.add(title_id="t2", title="Stranger Things", title_type="series", year=2016)
            entries = mgr.get_all()
            assert len(entries) == 2
        finally:
            os.unlink(db_path)

    def test_remove_entry(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            entry = mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            assert len(mgr.get_all()) == 1
            mgr.remove("t1")
            assert len(mgr.get_all()) == 0
        finally:
            os.unlink(db_path)

    def test_remove_nonexistent(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            mgr.remove("nonexistent")
            assert len(mgr.get_all()) == 0
        finally:
            os.unlink(db_path)

    def test_get_by_title_id(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            entry = mgr.get_by_title_id("t1")
            assert entry is not None
            assert entry.title == "Inception"
            entry_none = mgr.get_by_title_id("nonexistent")
            assert entry_none is None
        finally:
            os.unlink(db_path)

    def test_get_by_title_name(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            entry = mgr.get_by_title_name("Inception")
            assert entry is not None
            assert entry.title == "Inception"
        finally:
            os.unlink(db_path)

    def test_update_progress(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            entry = mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            assert entry.progress == "Not started"
            mgr.update_progress("t1", "Watching", 0.5)
            entry = mgr.get_by_title_id("t1")
            assert entry.progress == "Watching"
            assert entry.progress_percentage == 50
        finally:
            os.unlink(db_path)

    def test_set_rating(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            entry = mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            mgr.set_rating("t1", 8)
            entry = mgr.get_by_title_id("t1")
            assert entry.rating_given == 8
        finally:
            os.unlink(db_path)

    def test_update_notes(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            entry = mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            mgr.update_notes("t1", "Great movie!")
            entry = mgr.get_by_title_id("t1")
            assert entry.notes == "Great movie!"
        finally:
            os.unlink(db_path)

    def test_get_continue_watching(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            mgr.update_progress("t1", "Watching", 0.5)
            entries = mgr.get_continue_watching()
            assert len(entries) == 1
            assert entries[0].title == "Inception"
        finally:
            os.unlink(db_path)

    def test_get_continue_watching_empty(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            entries = mgr.get_continue_watching()
            assert len(entries) == 0
        finally:
            os.unlink(db_path)

    def test_get_completed(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            mgr.update_progress("t1", "Completed", 1.0)
            completed = mgr.get_completed()
            assert len(completed) == 1
            assert completed[0].title == "Inception"
        finally:
            os.unlink(db_path)

    def test_get_not_started(self):
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            not_started = mgr.get_not_started()
            assert len(not_started) == 1
            assert not_started[0].title == "Inception"
        finally:
            os.unlink(db_path)

    def test_persistence(self):
        """Test that data persists across manager instances."""
        db_path = self._create_temp_db()
        try:
            mgr1 = WatchlistManager(db_path)
            mgr1.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            mgr1.update_progress("t1", "Watching", 0.5)
            mgr1.set_rating("t1", 9)

            # Create a new manager instance pointing to the same db
            mgr2 = WatchlistManager(db_path)
            entry = mgr2.get_by_title_id("t1")
            assert entry is not None
            assert entry.title == "Inception"
            assert entry.progress == "Watching"
            assert entry.progress_percentage == 50
            assert entry.rating_given == 9
        finally:
            os.unlink(db_path)

    def test_add_duplicate_title_id(self):
        """Test that adding a duplicate title_id returns the existing entry."""
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            entry1 = mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            entry2 = mgr.add(title_id="t1", title="Another", title_type="movie", year=2020)
            # Should return the existing entry, not raise
            assert entry1.title_id == entry2.title_id
            assert entry1.title == "Inception"  # Original title preserved
            assert len(mgr.get_all()) == 1  # Still only one entry
        finally:
            os.unlink(db_path)

    def test_db_file_created(self):
        """Test that the database file is created if it doesn't exist."""
        db_path = self._create_temp_db()
        os.unlink(db_path)
        mgr = WatchlistManager(db_path)
        assert os.path.exists(db_path)
        os.unlink(db_path)

    def test_db_file_valid_json(self):
        """Test that the database file is valid JSON."""
        db_path = self._create_temp_db()
        try:
            mgr = WatchlistManager(db_path)
            mgr.add(title_id="t1", title="Inception", title_type="movie", year=2010)
            with open(db_path, "r") as f:
                data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["title_id"] == "t1"
        finally:
            os.unlink(db_path)
