"""tests for unweb — all offline, no network or LLM calls."""
from __future__ import annotations
import json
import sys
import pathlib
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest


_ARTICLE = """
EPA Administrator Michael Greene announced new regulations on Monday,
drawing sharp criticism from ExxonMobil CEO Darren Woods.
Former EPA official Janet Bauer, who joined ExxonMobil's lobbying arm in 2021,
called the rules "unworkable."
The American Petroleum Institute, funded largely by major oil companies including ExxonMobil,
Shell, and BP, issued a statement opposing the regulations.
Senator Rick Morales, who received $2 million in campaign donations from fossil fuel companies,
has scheduled hearings to challenge the EPA's authority.
The Environmental Defense Fund praised the rules as "long overdue."
"""

_SAMPLE_GRAPH = {
    "story_summary": "EPA issues new climate rules opposed by fossil fuel industry.",
    "people": [
        {"name": "Michael Greene", "role": "EPA Administrator", "org": "EPA",
         "connections": ["ExxonMobil"], "notes": ""},
        {"name": "Darren Woods", "role": "CEO", "org": "ExxonMobil",
         "connections": [], "notes": ""},
    ],
    "orgs": [
        {"name": "EPA", "type": "government", "parent": "", "funders": [], "notes": ""},
        {"name": "ExxonMobil", "type": "corporation", "parent": "",
         "funders": [], "notes": ""},
        {"name": "American Petroleum Institute", "type": "lobbying",
         "parent": "", "funders": ["ExxonMobil", "Shell", "BP"], "notes": ""},
    ],
    "connections": [
        {"from": "Janet Bauer", "relation": "employs", "to": "ExxonMobil",
         "evidence": "joined ExxonMobil's lobbying arm in 2021"},
        {"from": "Rick Morales", "relation": "donated_to",
         "to": "fossil fuel companies", "evidence": "$2M in donations"},
    ],
    "red_flags": [
        "Former EPA official now lobbying for ExxonMobil — revolving door",
        "Senator received $2M from fossil fuel companies while scheduling oversight hearings",
    ],
    "metadata": {
        "model": "qwen3:6b", "source_url": "https://example.com",
        "text_length": len(_ARTICLE), "extracted_at": "2024-01-01T00:00:00Z",
        "n_people": 2, "n_orgs": 3, "n_connections": 2,
    },
}


# ─────────────────────────────────────────────
# Fetcher tests
# ─────────────────────────────────────────────

class TestFetcher:
    def test_extract_text_strips_html(self):
        from unweb.fetcher import _extract_text
        html = "<html><body><article><p>Hello World</p></article></body></html>"
        text = _extract_text(html)
        assert "Hello World" in text
        assert "<" not in text

    def test_extract_text_removes_scripts(self):
        from unweb.fetcher import _extract_text
        html = "<html><script>alert(1)</script><p>Clean text</p></html>"
        text = _extract_text(html)
        assert "alert" not in text
        assert "Clean text" in text

    def test_extract_text_prefers_article_block(self):
        from unweb.fetcher import _extract_text
        html = ("<html><nav>MENU</nav>"
                "<article><p>Article content here</p></article>"
                "<footer>FOOTER</footer></html>")
        text = _extract_text(html)
        assert "Article content here" in text

    def test_fetch_url_network_error(self):
        from unweb.fetcher import fetch_url
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            with pytest.raises(RuntimeError, match="Could not fetch"):
                fetch_url("https://example.com/article")

    def test_fetch_url_calls_urlopen(self):
        from unweb.fetcher import fetch_url
        mock_resp = type("R", (), {
            "read": lambda s, n=None: b"<article>Article text</article>",
            "__enter__": lambda s: s,
            "__exit__": lambda s, *a: False,
        })()
        with patch("urllib.request.urlopen", return_value=mock_resp):
            text = fetch_url("https://example.com")
        assert "Article text" in text


# ─────────────────────────────────────────────
# Extractor tests
# ─────────────────────────────────────────────

class TestExtractor:
    def test_fallback_finds_proper_nouns(self):
        from unweb.extractor import _fallback_extract
        result = _fallback_extract(_ARTICLE)
        names = [p["name"] for p in result["people"]] + [o["name"] for o in result["orgs"]]
        # Should find at least some capitalized names
        assert len(names) > 0

    def test_fallback_schema(self):
        from unweb.extractor import _fallback_extract
        result = _fallback_extract(_ARTICLE)
        for key in ["story_summary","people","orgs","connections","red_flags"]:
            assert key in result

    def test_extract_uses_fallback_on_llm_failure(self):
        from unweb.extractor import extract_connections
        with patch("unweb.extractor._call_ollama", return_value="not json"):
            result = extract_connections(_ARTICLE)
        assert "metadata" in result
        assert "people" in result

    def test_extract_result_schema(self):
        from unweb.extractor import extract_connections
        mock_response = json.dumps({
            "story_summary": "Test story.",
            "people": [{"name": "A B", "role": "CEO", "org": "Corp",
                        "connections": [], "notes": ""}],
            "orgs": [],
            "connections": [],
            "red_flags": [],
        })
        with patch("unweb.extractor._call_ollama", return_value=mock_response):
            result = extract_connections(_ARTICLE)
        assert result["people"][0]["name"] == "A B"
        assert "metadata" in result

    def test_metadata_counts(self):
        from unweb.extractor import extract_connections
        mock_response = json.dumps({
            "story_summary": "s",
            "people": [{"name": "X Y", "role": "", "org": "", "connections": [], "notes": ""}],
            "orgs": [{"name": "Org", "type": "ngo", "parent": "", "funders": [], "notes": ""}],
            "connections": [],
            "red_flags": [],
        })
        with patch("unweb.extractor._call_ollama", return_value=mock_response):
            result = extract_connections("text")
        assert result["metadata"]["n_people"] == 1
        assert result["metadata"]["n_orgs"] == 1

    def test_parse_json_extracts_from_preamble(self):
        from unweb.extractor import _parse_json
        text = 'Here is the result: {"key": "value", "num": 42} done.'
        assert _parse_json(text) == {"key": "value", "num": 42}


# ─────────────────────────────────────────────
# Reporter tests
# ─────────────────────────────────────────────

class TestReporter:
    def test_report_contains_summary(self):
        from unweb.reporter import build_report
        report = build_report(_SAMPLE_GRAPH, source="https://example.com")
        assert "EPA issues new climate rules" in report

    def test_report_contains_all_people(self):
        from unweb.reporter import build_report
        report = build_report(_SAMPLE_GRAPH)
        assert "Michael Greene" in report
        assert "Darren Woods" in report

    def test_report_contains_orgs(self):
        from unweb.reporter import build_report
        report = build_report(_SAMPLE_GRAPH)
        assert "American Petroleum Institute" in report
        assert "ExxonMobil" in report

    def test_report_contains_red_flags(self):
        from unweb.reporter import build_report
        report = build_report(_SAMPLE_GRAPH)
        assert "revolving door" in report or "Red Flags" in report

    def test_report_contains_connections(self):
        from unweb.reporter import build_report
        report = build_report(_SAMPLE_GRAPH)
        assert "employs" in report or "donated_to" in report or "Connection" in report

    def test_save_report(self, tmp_path):
        from unweb.reporter import build_report, save_report
        report = build_report(_SAMPLE_GRAPH)
        out = str(tmp_path / "report.md")
        save_report(report, out)
        assert pathlib.Path(out).exists()
        assert len(pathlib.Path(out).read_text(encoding="utf-8")) > 100
