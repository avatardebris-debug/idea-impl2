"""Tests for services module."""

import json
import os
import tempfile
import pytest
from movieseries_tracker.search import StreamingSearchService
from movieseries_tracker.models import Title, StreamingService


class TestStreamingSearchService:
    def test_search_by_query(self):
        svc = StreamingSearchService()
        results = svc.search(query="Inception")
        assert len(results) > 0
        titles = [t.title for t in results]
        assert "Inception" in titles

    def test_search_by_type_movie(self):
        svc = StreamingSearchService()
        results = svc.search(query="", title_type="movie")
        assert len(results) > 0
        for r in results:
            assert r.type == "movie"

    def test_search_by_type_series(self):
        svc = StreamingSearchService()
        results = svc.search(query="", title_type="series")
        assert len(results) > 0
        for r in results:
            assert r.type == "series"

    def test_search_by_platform(self):
        svc = StreamingSearchService()
        results = svc.search(query="", platform="netflix")
        assert len(results) > 0
        for r in results:
            assert r.is_available_on("netflix") is True

    def test_search_by_availability_free(self):
        svc = StreamingSearchService()
        results = svc.search(query="", availability="free")
        assert len(results) > 0
        for r in results:
            assert r.is_free_available is True

    def test_search_no_results(self):
        svc = StreamingSearchService()
        results = svc.search(query="xyznonexistent12345")
        assert len(results) == 0

    def test_search_combined_filters(self):
        svc = StreamingSearchService()
        results = svc.search(query="", title_type="movie", availability="free")
        assert len(results) > 0
        for r in results:
            assert r.type == "movie"
            assert r.is_free_available is True

    def test_get_all_titles(self):
        svc = StreamingSearchService()
        all_titles = svc.get_all_titles()
        assert len(all_titles) > 0
        for t in all_titles:
            assert isinstance(t, Title)

    def test_get_title_by_id(self):
        svc = StreamingSearchService()
        all_titles = svc.get_all_titles()
        if all_titles:
            first_id = all_titles[0].id
            title = svc.get_title_by_id(first_id)
            assert title is not None
            assert title.id == first_id

    def test_get_title_by_id_not_found(self):
        svc = StreamingSearchService()
        title = svc.get_title_by_id("nonexistent_id")
        assert title is None

    def test_search_case_insensitive(self):
        svc = StreamingSearchService()
        results1 = svc.search(query="inception")
        results2 = svc.search(query="INCEPTION")
        assert len(results1) == len(results2)
        assert len(results1) > 0

    def test_search_partial_match(self):
        svc = StreamingSearchService()
        results = svc.search(query="stranger")
        assert len(results) > 0
        titles = [t.title for t in results]
        assert any("Stranger" in t for t in titles)

    def test_search_empty_query_returns_all(self):
        svc = StreamingSearchService()
        results = svc.search(query="")
        all_titles = svc.get_all_titles()
        assert len(results) == len(all_titles)

    def test_search_with_notes(self):
        svc = StreamingSearchService()
        results = svc.search(query="office")
        assert len(results) > 0
        titles = [t.title for t in results]
        assert "The Office" in titles

    def test_database_has_required_fields(self):
        svc = StreamingSearchService()
        all_titles = svc.get_all_titles()
        assert len(all_titles) > 0
        for t in all_titles:
            assert t.id is not None
            assert t.title is not None
            assert t.type in ("movie", "series")
            assert t.year > 0
            assert t.rating > 0
            assert len(t.genres) > 0
            assert len(t.streaming_services) > 0

    def test_streaming_service_types(self):
        svc = StreamingSearchService()
        all_titles = svc.get_all_titles()
        types_found = set()
        for t in all_titles:
            for ss in t.streaming_services:
                types_found.add(ss.type)
        assert "paid" in types_found
        assert "free" in types_found

    def test_database_persistence(self):
        """Test that the database file exists and is valid JSON."""
        svc = StreamingSearchService()
        db_path = svc._get_db_path()
        assert os.path.exists(db_path)
        with open(db_path, "r") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0
