"""Comprehensive tests for Chronovision Autoresearch Adapter."""

import json
import pytest

from chronovision_adapter.models import Paper, FundingEvent, ResearchTrend
from chronovision_adapter.sources import ArxivSource, OpenReviewSource, BioRxivSource, MultiSourceSearch
from chronovision_adapter.funding import FundingTracker, FundingSignal
from chronovision_adapter.predictor import ImpactPredictor, PaperImpact
from chronovision_adapter.adapter import ChronovisionAdapter


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TestPaper:

    def test_create_paper(self):
        p = Paper("id1", "Test Paper", ["Author A"], "Abstract text", "arxiv", "2024-01-01")
        assert p.paper_id == "id1"
        assert p.source == "arxiv"

    def test_paper_to_dict(self):
        p = Paper("id1", "Test", ["A"], "Abs", "arxiv", "2024-01-01", keywords=["ml"])
        d = p.to_dict()
        assert d["paper_id"] == "id1"
        assert d["keywords"] == ["ml"]

    def test_paper_roundtrip(self):
        p = Paper("id1", "Test", ["A"], "Abs", "arxiv", "2024-01-01", citation_count=100)
        restored = Paper.from_dict(p.to_dict())
        assert restored.paper_id == p.paper_id
        assert restored.citation_count == 100

    def test_paper_json_roundtrip(self):
        p = Paper("id1", "Test", ["A"], "Abs", "arxiv", "2024-01-01")
        restored = Paper.from_json(p.to_json())
        assert restored.title == p.title


class TestFundingEvent:

    def test_create(self):
        e = FundingEvent("f1", "Acme", 1_000_000, "seed", ["Investor A"], "2024-01-01")
        assert e.amount_usd == 1_000_000

    def test_roundtrip(self):
        e = FundingEvent("f1", "Acme", 5_000_000, "series_a", ["Inv"], "2024-06-01", sector="AI")
        restored = FundingEvent.from_dict(e.to_dict())
        assert restored.company == "Acme"
        assert restored.sector == "AI"

    def test_json_roundtrip(self):
        e = FundingEvent("f1", "Co", 100, "seed", [], "2024-01-01")
        restored = FundingEvent.from_json(e.to_json())
        assert restored.event_id == "f1"


class TestResearchTrend:

    def test_create(self):
        t = ResearchTrend("AI", paper_count=5, momentum_score=0.8)
        assert t.topic == "AI"
        assert t.momentum_score == 0.8

    def test_roundtrip(self):
        t = ResearchTrend("Bio", paper_count=3, funding_total_usd=1e9)
        restored = ResearchTrend.from_dict(t.to_dict())
        assert restored.topic == "Bio"
        assert restored.funding_total_usd == 1e9


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

class TestArxivSource:

    def test_search_returns_papers(self):
        src = ArxivSource()
        results = src.search("transformer")
        assert len(results) >= 1
        assert all(isinstance(p, Paper) for p in results)

    def test_search_with_limit(self):
        src = ArxivSource()
        results = src.search("transformer", max_results=1)
        assert len(results) <= 1

    def test_get_paper_existing(self):
        src = ArxivSource()
        p = src.get_paper("arxiv:2301.00001")
        assert p is not None
        assert "Attention" in p.title

    def test_get_paper_missing(self):
        src = ArxivSource()
        assert src.get_paper("arxiv:nonexistent") is None

    def test_source_name(self):
        assert ArxivSource().source_name == "arxiv"


class TestOpenReviewSource:

    def test_search(self):
        src = OpenReviewSource()
        results = src.search("reasoning")
        assert len(results) >= 1

    def test_source_name(self):
        assert OpenReviewSource().source_name == "openreview"


class TestBioRxivSource:

    def test_search(self):
        src = BioRxivSource()
        results = src.search("protein")
        assert len(results) >= 1

    def test_source_name(self):
        assert BioRxivSource().source_name == "biorxiv"


class TestMultiSourceSearch:

    def test_search_all(self):
        ms = MultiSourceSearch()
        results = ms.search_all("AI")
        assert len(results) >= 1
        sources = set(p.source for p in results)
        assert len(sources) >= 1  # at least one source returned results

    def test_source_names(self):
        ms = MultiSourceSearch()
        assert "arxiv" in ms.source_names
        assert "openreview" in ms.source_names
        assert "biorxiv" in ms.source_names

    def test_get_paper(self):
        ms = MultiSourceSearch()
        p = ms.get_paper("arxiv:2301.00001")
        assert p is not None

    def test_get_paper_missing(self):
        ms = MultiSourceSearch()
        assert ms.get_paper("nonexistent:999") is None


# ---------------------------------------------------------------------------
# Funding
# ---------------------------------------------------------------------------

class TestFundingTracker:

    def test_default_events_loaded(self):
        ft = FundingTracker()
        assert len(ft.events) >= 5

    def test_search_by_sector(self):
        ft = FundingTracker()
        ai_events = ft.search(sector="AI")
        assert len(ai_events) >= 1
        assert all("ai" in e.sector.lower() for e in ai_events)

    def test_search_by_min_amount(self):
        ft = FundingTracker()
        big = ft.search(min_amount=1_000_000_000)
        assert len(big) >= 1
        assert all(e.amount_usd >= 1_000_000_000 for e in big)

    def test_get_sector_signal(self):
        ft = FundingTracker()
        signal = ft.get_sector_signal("AI/ML")
        assert isinstance(signal, FundingSignal)
        assert signal.sector == "AI/ML"
        assert signal.event_count >= 1
        assert signal.total_funding_usd > 0

    def test_get_sector_signal_empty(self):
        ft = FundingTracker()
        signal = ft.get_sector_signal("nonexistent_sector")
        assert signal.event_count == 0
        assert signal.alert_level == "low"

    def test_get_all_sectors(self):
        ft = FundingTracker()
        sectors = ft.get_all_sectors()
        assert isinstance(sectors, list)
        assert len(sectors) >= 3

    def test_get_top_funded(self):
        ft = FundingTracker()
        top = ft.get_top_funded_sectors(top_n=3)
        assert len(top) <= 3
        assert all(isinstance(s, FundingSignal) for s in top)
        # Should be sorted by total funding
        for i in range(len(top) - 1):
            assert top[i].total_funding_usd >= top[i + 1].total_funding_usd

    def test_add_event(self):
        ft = FundingTracker()
        initial = len(ft.events)
        ft.add_event(FundingEvent("new1", "TestCo", 500, "seed", [], "2024-01-01"))
        assert len(ft.events) == initial + 1

    def test_signal_to_dict(self):
        ft = FundingTracker()
        signal = ft.get_sector_signal("AI/ML")
        d = signal.to_dict()
        assert "sector" in d
        assert "momentum" in d
        assert "alert_level" in d

    def test_momentum_ranges(self):
        ft = FundingTracker()
        signal = ft.get_sector_signal("AI/ML")
        assert 0.0 <= signal.momentum <= 1.0


# ---------------------------------------------------------------------------
# Predictor
# ---------------------------------------------------------------------------

class TestImpactPredictor:

    def test_predict_single(self):
        p = Paper("test1", "Novel Transformer Architecture", ["A"],
                  "A novel approach that outperforms all previous methods.",
                  "arxiv", "2024-01-01", citation_count=5000,
                  keywords=["transformer"])
        pred = ImpactPredictor()
        impact = pred.predict(p)
        assert isinstance(impact, PaperImpact)
        assert 0 <= impact.impact_score <= 100
        assert impact.paper_id == "test1"

    def test_predict_batch(self):
        papers = [
            Paper("p1", "Paper A", ["A"], "Abstract A", "arxiv", "2024-01-01", citation_count=100),
            Paper("p2", "Paper B", ["B"], "Abstract B", "arxiv", "2024-01-01", citation_count=5000),
        ]
        pred = ImpactPredictor()
        impacts = pred.predict_batch(papers)
        assert len(impacts) == 2

    def test_rank_papers(self):
        papers = [
            Paper("low", "Incremental work", ["A"], "Small improvement.", "arxiv", "2024-01-01", citation_count=10),
            Paper("high", "Novel breakthrough method", ["B"], "State-of-the-art outperforms all.", "arxiv", "2024-01-01", citation_count=10000),
        ]
        pred = ImpactPredictor()
        ranked = pred.rank_papers(papers)
        assert ranked[0].impact_score >= ranked[1].impact_score

    def test_categorize_breakthrough(self):
        p = Paper("b1", "A Novel Framework", ["A"], "Our novel method outperforms state-of-the-art.", "arxiv", "2024-01-01")
        pred = ImpactPredictor()
        impact = pred.predict(p)
        assert impact.category == "breakthrough"

    def test_categorize_survey(self):
        p = Paper("s1", "A Comprehensive Survey of ML", ["A"], "This survey reviews and provides an overview of recent work.", "arxiv", "2024-01-01")
        pred = ImpactPredictor()
        impact = pred.predict(p)
        assert impact.category == "survey"

    def test_detect_trends(self):
        papers = [
            Paper("p1", "A", ["A"], "", "arxiv", "2024-01-01", categories=["cs.AI"], citation_count=100),
            Paper("p2", "B", ["B"], "", "arxiv", "2024-01-01", categories=["cs.AI"], citation_count=200),
            Paper("p3", "C", ["C"], "", "arxiv", "2024-01-01", categories=["cs.LG"], citation_count=50),
        ]
        pred = ImpactPredictor()
        trends = pred.detect_trends(papers)
        assert len(trends) >= 1
        assert all(isinstance(t, ResearchTrend) for t in trends)

    def test_impact_to_dict(self):
        p = Paper("t1", "Test", ["A"], "Abstract", "arxiv", "2024-01-01")
        pred = ImpactPredictor()
        impact = pred.predict(p)
        d = impact.to_dict()
        assert "impact_score" in d
        assert "category" in d
        assert "reasoning" in d


# ---------------------------------------------------------------------------
# Adapter (Integration)
# ---------------------------------------------------------------------------

class TestChronovisionAdapter:

    def test_create_adapter(self):
        adapter = ChronovisionAdapter()
        assert adapter is not None

    def test_research_query(self):
        adapter = ChronovisionAdapter()
        result = adapter.research("transformer")
        assert "papers" in result
        assert "impacts" in result
        assert "trends" in result
        assert "funding_signals" in result
        assert "summary" in result
        assert len(result["papers"]) >= 1

    def test_predict_paper_impact(self):
        adapter = ChronovisionAdapter()
        p = Paper("t1", "Test", ["A"], "Abstract", "arxiv", "2024-01-01", citation_count=100)
        impact = adapter.predict_paper_impact(p)
        assert isinstance(impact, PaperImpact)

    def test_get_funding_signal(self):
        adapter = ChronovisionAdapter()
        signal = adapter.get_funding_signal("AI/ML")
        assert isinstance(signal, FundingSignal)
        assert signal.event_count >= 1

    def test_get_paper(self):
        adapter = ChronovisionAdapter()
        p = adapter.get_paper("arxiv:2301.00001")
        assert p is not None

    def test_dashboard(self):
        adapter = ChronovisionAdapter()
        dash = adapter.dashboard()
        assert "total_papers_tracked" in dash
        assert "total_funding_events" in dash
        assert "sectors" in dash
        assert "top_papers" in dash
        assert "sources" in dash

    def test_to_json(self):
        adapter = ChronovisionAdapter()
        result = adapter.research("AI")
        json_str = adapter.to_json(result)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert "query" in parsed

    def test_full_pipeline(self):
        """End-to-end: research -> predict -> fund -> dashboard."""
        adapter = ChronovisionAdapter()

        # Research
        result = adapter.research("scaling laws")
        assert len(result["papers"]) >= 1
        assert len(result["impacts"]) >= 1

        # Top paper should have a category
        top = result["impacts"][0]
        assert top["category"] in ("breakthrough", "incremental", "survey", "application")

        # Funding
        signal = adapter.get_funding_signal("AI/ML")
        assert signal.total_funding_usd > 0

        # Dashboard
        dash = adapter.dashboard()
        assert dash["total_papers_tracked"] >= 1
        assert dash["total_funding_events"] >= 1
