"""Tests for the pipeline module."""

import pytest
from book_researcher.pipeline import BookResearcherPipeline, run_pipeline
from book_researcher.models import Gap, NicheProfile, TableOfContents


class TestBookResearcherPipeline:
    """Tests for BookResearcherPipeline."""

    def test_pipeline_run_returns_toc(self):
        """run() should return a TableOfContents."""
        pipeline = BookResearcherPipeline()
        # Use sample reviews (no external dependencies)
        result = pipeline.run(book_titles=["test_book"])
        assert isinstance(result, TableOfContents)

    def test_pipeline_run_with_empty_reviews(self):
        """Pipeline should handle empty reviews gracefully."""
        pipeline = BookResearcherPipeline()
        # With no matching reviews, should still return a TOC (possibly empty)
        result = pipeline.run(book_titles=["nonexistent_book_xyz"])
        assert isinstance(result, TableOfContents)

    def test_pipeline_run_returns_list_of_tocs(self):
        """run() should return a list of TableOfContents."""
        pipeline = BookResearcherPipeline()
        result = pipeline.run(book_titles=["test_book"])
        assert isinstance(result, list)
        assert all(isinstance(t, TableOfContents) for t in result)


class TestRunPipeline:
    """Tests for run_pipeline convenience function."""

    def test_run_pipeline_returns_list(self):
        """run_pipeline should return a list."""
        result = run_pipeline(book_titles=["test_book"])
        assert isinstance(result, list)

    def test_run_pipeline_empty_input(self):
        """Empty book_titles should return empty list."""
        result = run_pipeline(book_titles=[])
        assert result == []
