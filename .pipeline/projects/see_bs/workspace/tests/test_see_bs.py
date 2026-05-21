"""Tests for see_bs — models, filters, engine, and integration."""

import pytest
from datetime import datetime

from see_bs.models import NewsArticle
from see_bs.filters import (
    filter_scott_alexander_rule,
    filter_gellman_amnesia,
    filter_reporter_identity,
    filter_incentive_alignment,
    ALL_FILTERS,
)
from see_bs.engine import ScoreEngine, AnalysisResult, FilterBreakdown
from see_bs import filter_news


# ---- helpers ----

def _make_article(**overrides):
    """Build a minimal NewsArticle with defaults, then override."""
    defaults = dict(
        title="Test Title",
        content="Test content here.",
        source="Test Outlet",
        author="Test Author",
        date=datetime(2025, 1, 1),
        outlet_bias="center",
        claim_type="factual",
        evidence_level="moderate",
        author_track_record="reliable",
        incentives=[],
    )
    defaults.update(overrides)
    return NewsArticle(**defaults)


# ---- NewsArticle model tests ----

class TestNewsArticle:
    def test_minimal_creation(self):
        a = _make_article()
        assert a.title == "Test Title"
        assert a.bs_score is None

    def test_to_dict_roundtrip(self):
        a = _make_article(title="RoundTrip", incentives=["a", "b"])
        d = a.to_dict()
        b = NewsArticle.from_dict(d)
        assert b.title == "RoundTrip"
        assert b.incentives == ["a", "b"]

    def test_from_dict_missing_field_raises(self):
        d = {"title": "x", "content": "y"}  # missing required fields
        with pytest.raises(TypeError):
            NewsArticle.from_dict(d)


# ---- Filter tests ----

class TestScottAlexanderRule:
    def test_absolutist_language(self):
        a = _make_article(content="Everyone knows this. No one disputes it. Obviously true.")
        r = filter_scott_alexander_rule(a)
        assert r["score"] > 0

    def test_moderate_language(self):
        a = _make_article(content="Some evidence suggests this may be true, though others disagree.")
        r = filter_scott_alexander_rule(a)
        # No absolutist words → score is 10 (not 0)
        assert r["score"] == 10


class TestGellmanAmnesia:
    def test_no_opposing_viewpoint(self):
        a = _make_article(content="This is the only perspective. Critics are wrong.")
        r = filter_gellman_amnesia(a)
        assert r["score"] > 0

    def test_has_opposing_viewpoint(self):
        a = _make_article(content="Proponents say X. Critics argue Y. The truth may lie in between.")
        r = filter_gellman_amnesia(a)
        assert r["score"] == 15


class TestReporterIdentity:
    def test_extreme_bias(self):
        a = _make_article(outlet_bias="extreme", author_track_record="unreliable")
        r = filter_reporter_identity(a)
        assert r["score"] > 0

    def test_center_bias_reliable(self):
        a = _make_article(outlet_bias="center", author_track_record="reliable")
        r = filter_reporter_identity(a)
        assert r["score"] == 25  # 50 - 10 (center) - 15 (reliable)


class TestIncentiveAlignment:
    def test_conflict_of_interest(self):
        a = _make_article(incentives=["selling course", "donor pressure"])
        r = filter_incentive_alignment(a)
        assert r["score"] > 0

    def test_no_conflict(self):
        a = _make_article(incentives=[])
        r = filter_incentive_alignment(a)
        assert r["score"] == 10


class TestAllFilters:
    def test_all_filters_registered(self):
        assert len(ALL_FILTERS) == 4

    def test_each_filter_callable(self):
        a = _make_article()
        for f in ALL_FILTERS:
            r = f(a)
            assert isinstance(r, dict)
            assert "score" in r
            assert "explanation" in r


# ---- Engine tests ----

class TestScoreEngine:
    def test_analyze_returns_analysis_result(self):
        a = _make_article()
        result = ScoreEngine.analyze(a)
        assert isinstance(result, AnalysisResult)
        assert isinstance(result.bs_score, float)
        assert 0 <= result.bs_score <= 100
        assert isinstance(result.breakdown, list)
        assert isinstance(result.summary, str)

    def test_high_bs_article(self):
        a = _make_article(
            title="Everyone Knows It!",
            content="Obviously true. No one disputes. Undoubtedly certain.",
            outlet_bias="extreme",
            author_track_record="unreliable",
            incentives=["selling course"],
        )
        result = ScoreEngine.analyze(a)
        assert result.bs_score > 50

    def test_low_bs_article(self):
        a = _make_article(
            title="Moderate Findings",
            content="Some evidence supports X. Critics note Y. More research needed.",
            outlet_bias="center",
            author_track_record="reliable",
            incentives=[],
        )
        result = ScoreEngine.analyze(a)
        assert result.bs_score < 30

    def test_strong_verdict_high(self):
        a = _make_article(
            title="Absolutely Certain",
            content="No doubt. Obviously true. Critics are lying.",
            outlet_bias="extreme",
            incentives=["conspiracy course"],
        )
        result = ScoreEngine.analyze(a)
        assert "High BS" in result.summary

    def test_strong_verdict_low(self):
        a = _make_article(
            title="Balanced Report",
            content="Both sides present valid points. Evidence is mixed.",
            outlet_bias="center",
            incentives=[],
        )
        result = ScoreEngine.analyze(a)
        assert "Very low BS" in result.summary

    def test_breakdown_has_four_entries(self):
        a = _make_article()
        result = ScoreEngine.analyze(a)
        assert len(result.breakdown) == 4


class TestFilterBreakdown:
    def test_creation(self):
        fb = FilterBreakdown(name="test", score=50.0, explanation="test")
        assert fb.name == "test"
        assert fb.score == 50.0


# ---- Integration tests ----

class TestFilterNews:
    def test_top_level_api(self):
        a = _make_article()
        result = filter_news(a)
        assert isinstance(result, AnalysisResult)
        assert isinstance(result.bs_score, float)

    def test_high_bs_integration(self):
        a = _make_article(
            title="Shocking Truth!",
            content="Everyone knows this. No one disputes. Obviously.",
            outlet_bias="extreme",
            incentives=["outrage clicks"],
        )
        result = filter_news(a)
        assert result.bs_score > 50
        assert "High BS" in result.summary

    def test_low_bs_integration(self):
        a = _make_article(
            title="Study Shows Mixed Results",
            content="Some evidence for X. Critics note Y. More research needed.",
            outlet_bias="center",
            incentives=[],
        )
        result = filter_news(a)
        assert result.bs_score < 30


# ---- Error handling tests ----

class TestErrorHandling:
    def test_none_article_raises(self):
        with pytest.raises((ValueError, TypeError, AttributeError)):
            ScoreEngine.analyze(None)  # type: ignore

    def test_empty_content(self):
        a = _make_article(content="")
        result = ScoreEngine.analyze(a)
        assert isinstance(result, AnalysisResult)

    def test_empty_title(self):
        a = _make_article(title="")
        result = ScoreEngine.analyze(a)
        assert isinstance(result, AnalysisResult)
