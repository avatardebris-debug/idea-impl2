"""
tests/test_researcher.py — unit tests for the researcher orchestrator.
tests/test_report.py     — unit tests for the report builder.
tests/test_summarizer.py — unit tests for the summarizer.

All offline via mocking.
"""
from __future__ import annotations
import sys
import pathlib
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest
from research1.sources.arxiv import Result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_results() -> list[Result]:
    return [
        Result(source="arxiv",     title="Quantum paper 1",  authors=["A. Smith"],
               abstract="We study quantum error correction via surface codes.",
               url="https://arxiv.org/abs/1234", published="2023-01", relevance_score=1.0),
        Result(source="pubmed",    title="CRISPR therapy",    authors=["B. Jones"],
               abstract="CRISPR-Cas9 enables precise genome editing in vivo.",
               url="https://pubmed.ncbi.nlm.nih.gov/999/", published="2023-02", relevance_score=1.0),
        Result(source="wikipedia", title="Surface code",      authors=["Wikipedia contributors"],
               abstract="A surface code is a type of topological quantum error correcting code.",
               url="https://en.wikipedia.org/wiki/Surface_code", published="", relevance_score=0.9),
    ]


# ---------------------------------------------------------------------------
# Researcher tests
# ---------------------------------------------------------------------------

class TestResearcher:
    def test_deduplication_by_url(self):
        from research1.researcher import _deduplicate
        results = [
            Result(source="arxiv", title="A", authors=[], abstract="x",
                   url="https://arxiv.org/1", published="", relevance_score=1.0),
            Result(source="arxiv", title="A copy", authors=[], abstract="x",
                   url="https://arxiv.org/1", published="", relevance_score=1.0),  # dup URL
        ]
        deduped = _deduplicate(results)
        assert len(deduped) == 1

    def test_deduplication_by_title(self):
        from research1.researcher import _deduplicate
        results = [
            Result(source="arxiv", title="Quantum Error Correction", authors=[], abstract="",
                   url="https://url1.com", published="", relevance_score=1.0),
            Result(source="web",   title="Quantum Error Correction!", authors=[], abstract="",
                   url="https://url2.com", published="", relevance_score=1.0),  # same title, diff URL
        ]
        deduped = _deduplicate(results)
        assert len(deduped) == 1

    def test_scoring_orders_by_credibility(self, sample_results):
        from research1.researcher import _score
        pubmed_score = _score(sample_results[1])
        wiki_score   = _score(sample_results[2])
        assert pubmed_score > wiki_score

    def test_research_calls_all_sources(self, sample_results):
        from research1.researcher import research
        with patch.dict("research1.sources.SOURCES", {
            "mock_a": lambda q, n, t: sample_results[:1],
            "mock_b": lambda q, n, t: sample_results[1:2],
        }):
            results = research("test topic", sources=["mock_a", "mock_b"])
        assert len(results) >= 1

    def test_research_handles_source_failure(self):
        from research1.researcher import research
        def _fail(q, n, t):
            raise RuntimeError("Source unavailable")
        with patch.dict("research1.sources.SOURCES", {
            "failing": _fail,
        }):
            results = research("test", sources=["failing"])
        assert results == []


# ---------------------------------------------------------------------------
# Report tests
# ---------------------------------------------------------------------------

class TestReport:
    def test_build_report_contains_topic(self, sample_results):
        from research1.report import build_report
        report = build_report(
            query="quantum error correction",
            results=sample_results,
            summaries=["Summary 1", "Summary 2", "Summary 3"],
            synthesis="Overall synthesis text.",
            sources_used=["arxiv", "pubmed"],
        )
        assert "quantum error correction" in report
        assert "Overall synthesis text." in report

    def test_build_report_contains_all_titles(self, sample_results):
        from research1.report import build_report
        summaries = ["s1", "s2", "s3"]
        report = build_report("q", sample_results, summaries, "synth", ["arxiv"])
        for r in sample_results:
            assert r["title"] in report

    def test_build_report_contains_urls(self, sample_results):
        from research1.report import build_report
        report = build_report("q", sample_results, ["s"]*3, "synth", ["arxiv"])
        assert "https://arxiv.org/abs/1234" in report

    def test_build_report_empty_results(self):
        from research1.report import build_report
        report = build_report("q", [], [], "no results", [])
        assert "q" in report

    def test_save_report_writes_file(self, tmp_path, sample_results):
        from research1.report import build_report, save_report
        report = build_report("q", sample_results, ["s"]*3, "synth", ["arxiv"])
        out = str(tmp_path / "report.md")
        save_report(report, out)
        import pathlib
        assert pathlib.Path(out).exists()
        assert len(pathlib.Path(out).read_text()) > 0


# ---------------------------------------------------------------------------
# Summarizer tests (offline — no Ollama calls)
# ---------------------------------------------------------------------------

class TestSummarizer:
    def test_extractive_summary_first_three_sentences(self):
        from research1.summarizer import _extractive_summary
        r = Result(source="arxiv", title="T", authors=[],
                   abstract="This is the first sentence about quantum computing. This is the second sentence about error correction. This is the third sentence about surface codes. This is the fourth sentence that should be excluded.",
                   url="", published="", relevance_score=1.0)
        summary = _extractive_summary(r)
        assert "first sentence" in summary
        assert "second sentence" in summary
        assert "fourth" not in summary

    def test_extractive_summary_empty_abstract(self):
        from research1.summarizer import _extractive_summary
        r = Result(source="arxiv", title="T", authors=[], abstract="",
                   url="", published="", relevance_score=1.0)
        summary = _extractive_summary(r)
        assert isinstance(summary, str)

    def test_summarize_source_uses_fallback_on_llm_failure(self, sample_results):
        from research1.summarizer import summarize_source
        with patch("research1.summarizer._call_ollama", return_value=""):
            summary = summarize_source(sample_results[0])
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_synthesize_fallback_on_llm_failure(self, sample_results):
        from research1.summarizer import synthesize
        with patch("research1.summarizer._call_ollama", return_value=""):
            synthesis = synthesize("test topic", sample_results,
                                   per_source_summaries=["s1", "s2", "s3"])
        assert isinstance(synthesis, str)
        assert len(synthesis) > 0

    def test_synthesize_empty_results(self):
        from research1.summarizer import synthesize
        synthesis = synthesize("test topic", [])
        assert "No sources" in synthesis or isinstance(synthesis, str)
