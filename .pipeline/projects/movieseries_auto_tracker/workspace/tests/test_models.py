"""Tests for core data models."""

import json
import pytest
from movieseries_tracker.models import Episode, StreamingService, Title, WatchlistEntry


class TestEpisode:
    def test_create_episode(self):
        ep = Episode(season=1, episode=1, title="Pilot", duration_minutes=45)
        assert ep.season == 1
        assert ep.episode == 1
        assert ep.title == "Pilot"
        assert ep.duration_minutes == 45
        assert ep.watched is False

    def test_mark_watched(self):
        ep = Episode(season=1, episode=1, title="Pilot")
        ep.mark_watched()
        assert ep.watched is True

    def test_to_dict_and_from_dict(self):
        ep = Episode(season=2, episode=3, title="Midpoint", duration_minutes=50)
        d = ep.to_dict()
        assert d["season"] == 2
        assert d["episode"] == 3
        assert d["title"] == "Midpoint"
        assert d["duration_minutes"] == 50
        assert d["watched"] is False

        ep2 = Episode.from_dict(d)
        assert ep2.season == 2
        assert ep2.episode == 3
        assert ep2.title == "Midpoint"
        assert ep2.duration_minutes == 50
        assert ep2.watched is False

    def test_watched_progress(self):
        ep1 = Episode(season=1, episode=1)
        ep2 = Episode(season=1, episode=2)
        ep1.mark_watched()
        assert ep1.watched_progress == 1.0
        assert ep2.watched_progress == 0.0


class TestStreamingService:
    def test_create_service(self):
        svc = StreamingService(name="Netflix", type="paid", url="https://netflix.com")
        assert svc.name == "Netflix"
        assert svc.type == "paid"
        assert svc.url == "https://netflix.com"

    def test_to_dict_and_from_dict(self):
        svc = StreamingService(name="Tubi", type="free", url="https://tubi.tv")
        d = svc.to_dict()
        assert d["name"] == "Tubi"
        assert d["type"] == "free"

        svc2 = StreamingService.from_dict(d)
        assert svc2.name == "Tubi"
        assert svc2.type == "free"


class TestTitle:
    def test_create_title(self):
        title = Title(
            id="t1",
            title="Inception",
            type="movie",
            year=2010,
            rating=8.8,
            genres=["Sci-Fi", "Action"],
            description="Dream heist",
            streaming_services=[
                StreamingService(name="Prime Video", type="paid", url="https://prime.com"),
                StreamingService(name="Tubi", type="free", url="https://tubi.tv"),
            ],
        )
        assert title.id == "t1"
        assert title.title == "Inception"
        assert title.type == "movie"
        assert title.year == 2010
        assert title.rating == 8.8
        assert len(title.streaming_services) == 2

    def test_is_available_on(self):
        title = Title(
            id="t1",
            title="Test",
            type="movie",
            year=2020,
            streaming_services=[
                StreamingService(name="Netflix", type="paid", url="https://netflix.com"),
            ],
        )
        assert title.is_available_on("netflix") is True
        assert title.is_available_on("hulu") is False

    def test_is_free_available(self):
        title_paid = Title(
            id="t1",
            title="Paid Only",
            type="movie",
            year=2020,
            streaming_services=[
                StreamingService(name="Netflix", type="paid", url="https://netflix.com"),
            ],
        )
        title_free = Title(
            id="t2",
            title="Free Available",
            type="movie",
            year=2020,
            streaming_services=[
                StreamingService(name="Tubi", type="free", url="https://tubi.tv"),
            ],
        )
        assert title_paid.is_free_available is False
        assert title_free.is_free_available is True

    def test_to_dict_and_from_dict(self):
        title = Title(
            id="t1",
            title="Test Title",
            type="movie",
            year=2020,
            rating=7.5,
            genres=["Drama"],
            description="A test",
            streaming_services=[
                StreamingService(name="Netflix", type="paid", url="https://netflix.com"),
            ],
        )
        d = title.to_dict()
        assert d["id"] == "t1"
        assert d["title"] == "Test Title"
        assert d["type"] == "movie"
        assert d["year"] == 2020
        assert d["rating"] == 7.5
        assert len(d["streaming_services"]) == 1

        title2 = Title.from_dict(d)
        assert title2.id == "t1"
        assert title2.title == "Test Title"
        assert title2.type == "movie"
        assert title2.year == 2020
        assert title2.rating == 7.5
        assert len(title2.streaming_services) == 1
        assert title2.streaming_services[0].name == "Netflix"


class TestWatchlistEntry:
    def test_create_entry(self):
        entry = WatchlistEntry(
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

    def test_update_progress(self):
        entry = WatchlistEntry(title_id="t1", title="Test", title_type="movie", year=2020)
        entry.update_progress("Watching", 0.5)
        assert entry.progress == "Watching"
        assert entry.progress_percentage == 50

    def test_set_rating(self):
        entry = WatchlistEntry(title_id="t1", title="Test", title_type="movie", year=2020)
        entry.set_rating(8)
        assert entry.rating_given == 8

    def test_to_dict_and_from_dict(self):
        entry = WatchlistEntry(
            title_id="t1",
            title="Test",
            title_type="movie",
            year=2020,
            progress="Watching",
            progress_percentage=50,
            rating_given=7,
            notes="Great movie",
        )
        d = entry.to_dict()
        assert d["title_id"] == "t1"
        assert d["title"] == "Test"
        assert d["progress"] == "Watching"
        assert d["progress_percentage"] == 50
        assert d["rating_given"] == 7
        assert d["notes"] == "Great movie"

        entry2 = WatchlistEntry.from_dict(d)
        assert entry2.title_id == "t1"
        assert entry2.title == "Test"
        assert entry2.progress == "Watching"
        assert entry2.progress_percentage == 50
        assert entry2.rating_given == 7
        assert entry2.notes == "Great movie"

    def test_is_watched(self):
        entry = WatchlistEntry(title_id="t1", title="Test", title_type="movie", year=2020)
        assert entry.is_watched is False
        entry.update_progress("Completed", 1.0)
        assert entry.is_watched is True

    def test_is_in_progress(self):
        entry = WatchlistEntry(title_id="t1", title="Test", title_type="movie", year=2020)
        assert entry.is_in_progress is False
        entry.update_progress("Watching", 0.5)
        assert entry.is_in_progress is True
