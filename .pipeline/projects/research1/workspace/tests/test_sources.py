"""
tests/test_sources.py — unit tests for all source adapters.

All tests run fully offline using mocked HTTP responses.
No network calls, no API keys needed.
"""
from __future__ import annotations
import json
import sys
import pathlib
import unittest
from unittest.mock import patch, MagicMock
import io

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Shared mock HTTP response helper
# ---------------------------------------------------------------------------

def _mock_urlopen(content: str | bytes, status: int = 200):
    """Context manager mock for urllib.request.urlopen."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = content
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# arXiv tests
# ---------------------------------------------------------------------------

_ARXIV_ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2301.12345</id>
    <title>Quantum Error Correction: A Survey</title>
    <summary>We survey recent advances in quantum error correction including surface codes and magic state distillation.</summary>
    <published>2023-01-20T00:00:00Z</published>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2302.99999</id>
    <title>Fault Tolerant Quantum Computing</title>
    <summary>We present a fault-tolerant approach using concatenated codes.</summary>
    <published>2023-02-10T00:00:00Z</published>
    <author><name>Carol White</name></author>
  </entry>
</feed>"""


class TestArxivSource(unittest.TestCase):
    def test_returns_results(self):
        from research1.sources.arxiv import search
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(_ARXIV_ATOM)):
            results = search("quantum error correction", max_results=2)
        self.assertEqual(len(results), 2)

    def test_result_schema(self):
        from research1.sources.arxiv import search
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(_ARXIV_ATOM)):
            results = search("quantum", max_results=2)
        r = results[0]
        self.assertIn("title", r)
        self.assertIn("abstract", r)
        self.assertIn("url", r)
        self.assertIn("authors", r)
        self.assertIn("source", r)
        self.assertEqual(r["source"], "arxiv")

    def test_authors_parsed(self):
        from research1.sources.arxiv import search
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(_ARXIV_ATOM)):
            results = search("quantum", max_results=2)
        self.assertIn("Alice Smith", results[0]["authors"])
        self.assertIn("Bob Jones",   results[0]["authors"])

    def test_network_error_returns_empty(self):
        from research1.sources.arxiv import search
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            results = search("quantum")
        self.assertEqual(results, [])

    def test_malformed_xml_returns_empty(self):
        from research1.sources.arxiv import search
        with patch("urllib.request.urlopen", return_value=_mock_urlopen("<bad xml>")):
            results = search("quantum")
        self.assertEqual(results, [])


# ---------------------------------------------------------------------------
# PubMed tests
# ---------------------------------------------------------------------------

_PUBMED_SEARCH_JSON = json.dumps({
    "esearchresult": {"idlist": ["36123456", "36654321"]}
}).encode()

_PUBMED_FETCH_XML = """<?xml version="1.0" encoding="utf-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>36123456</PMID>
      <Article>
        <ArticleTitle>CRISPR-Cas9 clinical applications</ArticleTitle>
        <Abstract>
          <AbstractText>This article reviews CRISPR-Cas9 applications in human disease treatment.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author><LastName>Doe</LastName><ForeName>Jane</ForeName></Author>
        </AuthorList>
      </Article>
      <PubDate><Year>2023</Year><Month>Mar</Month></PubDate>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""


class TestPubMedSource(unittest.TestCase):
    def _mock_two_calls(self):
        """Mock two sequential urlopen calls: esearch then efetch."""
        call_count = [0]
        responses = [_mock_urlopen(_PUBMED_SEARCH_JSON), _mock_urlopen(_PUBMED_FETCH_XML)]
        def _side_effect(*args, **kwargs):
            r = responses[call_count[0]]
            call_count[0] += 1
            return r
        return _side_effect

    def test_returns_results(self):
        from research1.sources.pubmed import search
        with patch("urllib.request.urlopen", side_effect=self._mock_two_calls()):
            results = search("CRISPR", max_results=2)
        self.assertEqual(len(results), 1)

    def test_result_schema(self):
        from research1.sources.pubmed import search
        with patch("urllib.request.urlopen", side_effect=self._mock_two_calls()):
            results = search("CRISPR", max_results=2)
        r = results[0]
        self.assertEqual(r["source"], "pubmed")
        self.assertIn("pubmed.ncbi", r["url"])
        self.assertEqual(r["title"], "CRISPR-Cas9 clinical applications")

    def test_empty_pmids_returns_empty(self):
        from research1.sources.pubmed import search
        empty = json.dumps({"esearchresult": {"idlist": []}}).encode()
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(empty)):
            results = search("CRISPR")
        self.assertEqual(results, [])

    def test_network_error_returns_empty(self):
        from research1.sources.pubmed import search
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("x")):
            results = search("CRISPR")
        self.assertEqual(results, [])


# ---------------------------------------------------------------------------
# Wikipedia tests
# ---------------------------------------------------------------------------

_WIKI_SEARCH_JSON = json.dumps({
    "query": {"search": [
        {"title": "Quantum computing", "snippet": "Quantum computing uses quantum mechanics."},
        {"title": "Qubit",             "snippet": "A qubit is the basic unit of quantum information."},
    ]}
}).encode()

_WIKI_SUMMARY_JSON = json.dumps({
    "extract": "Quantum computing is a type of computation that uses quantum phenomena.",
    "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Quantum_computing"}},
}).encode()


class TestWikipediaSource(unittest.TestCase):
    def _mock_calls(self):
        call_count = [0]
        responses = [_mock_urlopen(_WIKI_SEARCH_JSON),
                     _mock_urlopen(_WIKI_SUMMARY_JSON),
                     _mock_urlopen(_WIKI_SUMMARY_JSON)]
        def _se(*args, **kwargs):
            r = responses[min(call_count[0], len(responses)-1)]
            call_count[0] += 1
            return r
        return _se

    def test_returns_results(self):
        from research1.sources.wikipedia import search
        with patch("urllib.request.urlopen", side_effect=self._mock_calls()):
            results = search("quantum computing", max_results=2)
        self.assertGreater(len(results), 0)

    def test_source_is_wikipedia(self):
        from research1.sources.wikipedia import search
        with patch("urllib.request.urlopen", side_effect=self._mock_calls()):
            results = search("quantum computing", max_results=1)
        self.assertEqual(results[0]["source"], "wikipedia")

    def test_network_error_returns_empty(self):
        from research1.sources.wikipedia import search
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("x")):
            results = search("quantum")
        self.assertEqual(results, [])


# ---------------------------------------------------------------------------
# Web source tests
# ---------------------------------------------------------------------------

_DDG_JSON = json.dumps({
    "Abstract": "Climate change refers to long-term shifts in global temperatures.",
    "AbstractURL": "https://www.noaa.gov/climate",
    "AbstractSource": "NOAA",
    "Heading": "Climate change",
    "RelatedTopics": [
        {"FirstURL": "https://www.epa.gov/climate", "Text": "EPA climate resources."},
        {"FirstURL": "https://example.com/random",  "Text": "Random site."},
    ],
}).encode()


class TestWebSource(unittest.TestCase):
    def test_returns_abstract_result(self):
        from research1.sources.web import search
        mock_noaa = _mock_urlopen(b"page text from NOAA")
        call_count = [0]
        mocks = [_mock_urlopen(_DDG_JSON), mock_noaa, _mock_urlopen(b"epa page text")]
        def _se(*a, **kw):
            r = mocks[min(call_count[0], len(mocks)-1)]
            call_count[0] += 1
            return r
        with patch("urllib.request.urlopen", side_effect=_se):
            results = search("climate change", max_results=3)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["title"], "Climate change")

    def test_network_error_returns_empty(self):
        from research1.sources.web import search
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("x")):
            results = search("climate")
        self.assertEqual(results, [])

    def test_credibility_filter(self):
        from research1.sources.web import _is_credible
        self.assertTrue(_is_credible("https://www.nih.gov/health"))
        self.assertTrue(_is_credible("https://nature.com/articles/s12345"))
        self.assertTrue(_is_credible("https://mit.edu/research"))
        self.assertFalse(_is_credible("https://random-blog.com/post"))


if __name__ == "__main__":
    unittest.main()
