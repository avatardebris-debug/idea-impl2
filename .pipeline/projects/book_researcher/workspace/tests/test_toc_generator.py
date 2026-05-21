"""Tests for the toc_generator module."""

import pytest
from book_researcher.toc_generator import generate_toc, _generate_chapters
from book_researcher.models import NicheProfile, TableOfContents, TOCChapter


class TestGenerateChapters:
    """Tests for _generate_chapters."""

    def test_generate_chapters_returns_list(self):
        """_generate_chapters should return a list of TOCChapter."""
        niches = [
            NicheProfile(topic="A", score=1.0, gap_count=5, representative_gaps=[]),
            NicheProfile(topic="B", score=0.5, gap_count=3, representative_gaps=[]),
        ]
        result = _generate_chapters(niches)
        assert isinstance(result, list)
        assert all(isinstance(c, TOCChapter) for c in result)

    def test_generate_chapters_empty_input(self):
        """Empty niches should return empty list."""
        result = _generate_chapters([])
        assert result == []

    def test_generate_chapters_respects_max_chapters(self):
        """Should not exceed max_chapters."""
        niches = [
            NicheProfile(topic=f"Topic {i}", score=float(i), gap_count=1, representative_gaps=[])
            for i in range(20)
        ]
        result = _generate_chapters(niches, max_chapters=5)
        assert len(result) <= 5

    def test_generate_chapters_ordered_by_score(self):
        """Chapters should be ordered by niche score descending."""
        niches = [
            NicheProfile(topic="Low", score=0.1, gap_count=1, representative_gaps=[]),
            NicheProfile(topic="High", score=0.9, gap_count=1, representative_gaps=[]),
            NicheProfile(topic="Mid", score=0.5, gap_count=1, representative_gaps=[]),
        ]
        result = _generate_chapters(niches)
        scores = [c.score for c in result]
        assert scores == sorted(scores, reverse=True)


class TestGenerateToc:
    """Tests for generate_toc."""

    def test_generate_toc_returns_toc(self):
        """generate_toc should return a TableOfContents."""
        niches = [
            NicheProfile(topic="A", score=1.0, gap_count=5, representative_gaps=[]),
        ]
        result = generate_toc(niches)
        assert isinstance(result, TableOfContents)
        assert hasattr(result, "title")
        assert hasattr(result, "chapters")

    def test_generate_toc_empty_input(self):
        """Empty niches should return TOC with no chapters."""
        result = generate_toc([])
        assert isinstance(result, TableOfContents)
        assert len(result.chapters) == 0

    def test_generate_toc_chapters_match_niches(self):
        """Number of chapters should match number of niches (up to max)."""
        niches = [
            NicheProfile(topic=f"Topic {i}", score=float(i), gap_count=1, representative_gaps=[])
            for i in range(3)
        ]
        result = generate_toc(niches)
        assert len(result.chapters) == 3
