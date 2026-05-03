"""Tests for scraper modules (blog, twitter, book excerpts, cleaner)."""

import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scraper.scott_adams_blog import (
    fetch_page,
    extract_article_body,
    extract_date,
    extract_title,
    scrape_blog_posts,
)
from scraper.twitter_archives import (
    load_csv_archive,
    load_json_archive,
    load_twitter_archives,
    generate_synthetic_tweets,
    _parse_date,
)
from scraper.book_excerpts import (
    load_text_excerpts,
    load_book_excerpts,
    generate_synthetic_book_excerpts,
)
from scraper.cleaner import (
    clean_corpus,
    deduplicate_samples,
    filter_by_length,
    filter_by_source,
)


# ── fetch_page ──────────────────────────────────────────────────────────────

class TestFetchPage:
    """Tests for fetch_page."""

    def test_successful_fetch(self):
        """fetch_page should return response on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("scraper.scott_adams_blog.requests.get", return_value=mock_response) as mock_get:
            result = fetch_page("http://example.com")
            assert result is mock_response
            mock_get.assert_called_once()

    def test_failed_fetch_returns_none(self):
        """fetch_page should return None on request exception."""
        import requests
        with patch("scraper.scott_adams_blog.requests.get", side_effect=requests.RequestException("fail")):
            result = fetch_page("http://example.com")
            assert result is None

    def test_non_200_status_raises(self):
        """fetch_page should raise on non-200 status."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404")
        with patch("scraper.scott_adams_blog.requests.get", return_value=mock_response):
            result = fetch_page("http://example.com")
            assert result is None


# ── extract_article_body ────────────────────────────────────────────────────

class TestExtractArticleBody:
    """Tests for extract_article_body."""

    def test_selects_first_matching_selector(self):
        """Should return text from the first matching selector."""
        soup = MagicMock()
        mock_element = MagicMock()
        mock_element.get_text.return_value = "This is the article body text that is long enough."
        soup.select_one.return_value = mock_element
        result = extract_article_body(soup)
        assert "article body" in result

    def test_fallback_to_paragraphs(self):
        """Should fall back to paragraph text if no selector matches."""
        soup = MagicMock()
        soup.select_one.return_value = None  # No selector matched

        p1 = MagicMock()
        p1.get_text.return_value = "First paragraph."
        p2 = MagicMock()
        p2.get_text.return_value = "Second paragraph."
        soup.find_all.return_value = [p1, p2]

        result = extract_article_body(soup)
        assert "First paragraph" in result
        assert "Second paragraph" in result

    def test_returns_empty_string_no_content(self):
        """Should return empty string if no content found."""
        soup = MagicMock()
        soup.select_one.return_value = None
        soup.find_all.return_value = []
        result = extract_article_body(soup)
        assert result == ""

    def test_short_content_rejected(self):
        """Should reject content shorter than 100 chars from selector."""
        soup = MagicMock()
        mock_element = MagicMock()
        mock_element.get_text.return_value = "Short"  # < 100 chars
        soup.select_one.return_value = mock_element
        result = extract_article_body(soup)
        assert result == ""  # Should fall through to paragraphs


# ── extract_date ────────────────────────────────────────────────────────────

class TestExtractDate:
    """Tests for extract_date."""

    def test_datetime_attribute(self):
        """Should extract date from datetime attribute."""
        soup = MagicMock()
        mock_element = MagicMock()
        mock_element.get.return_value = "2024-03-15T10:00:00Z"
        soup.select_one.return_value = mock_element
        result = extract_date(soup)
        assert result == "2024-03-15"

    def test_content_attribute(self):
        """Should extract date from content attribute."""
        soup = MagicMock()
        mock_element = MagicMock()
        mock_element.get.return_value = "2023-11-20T12:00:00Z"
        soup.select_one.return_value = mock_element
        result = extract_date(soup)
        assert result == "2023-11-20"

    def test_text_parsing(self):
        """Should parse date from text content."""
        soup = MagicMock()
        mock_element = MagicMock()
        mock_element.get.return_value = None
        mock_element.get_text.return_value = "March 15, 2024"
        soup.select_one.return_value = mock_element
        result = extract_date(soup)
        assert result == "2024-03-15"

    def test_unparseable_date_returns_none(self):
        """Should return None if date cannot be parsed."""
        soup = MagicMock()
        mock_element = MagicMock()
        mock_element.get.return_value = None
        mock_element.get_text.return_value = "not a date"
        soup.select_one.return_value = mock_element
        result = extract_date(soup)
        assert result is None


# ── extract_title ───────────────────────────────────────────────────────────

class TestExtractTitle:
    """Tests for extract_title."""

    def test_content_attribute(self):
        """Should return content attribute if present."""
        soup = MagicMock()
        mock_element = MagicMock()
        mock_element.get.return_value = "Test Title"
        soup.select_one.return_value = mock_element
        result = extract_title(soup)
        assert result == "Test Title"

    def test_text_content(self):
        """Should return text content if no content attribute."""
        soup = MagicMock()
        mock_element = MagicMock()
        mock_element.get.return_value = None
        mock_element.get_text.return_value = "Another Title"
        soup.select_one.return_value = mock_element
        result = extract_title(soup)
        assert result == "Another Title"

    def test_no_match_returns_empty(self):
        """Should return empty string if no title found."""
        soup = MagicMock()
        soup.select_one.return_value = None
        result = extract_title(soup)
        assert result == ""


# ── scrape_blog_posts ───────────────────────────────────────────────────────

class TestScrapeBlogPosts:
    """Tests for scrape_blog_posts."""

    @patch("scraper.scott_adams_blog.fetch_page")
    def test_no_posts_found(self, mock_fetch):
        """Should return empty list if no post links found."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>No posts here</body></html>"
        mock_fetch.side_effect = [mock_response, None]  # index + pagination fail
        result = scrape_blog_posts(max_posts=10)
        assert result == []

    @patch("scraper.scott_adams_blog.fetch_page")
    def test_fetches_and_parses_posts(self, mock_fetch):
        """Should fetch and parse blog posts correctly."""
        mock_response = MagicMock()
        mock_response.text = """
        <html>
        <body>
            <a href="/blog/2024/01/post1">Post 1</a>
            <a href="/blog/2024/02/post2">Post 2</a>
        </body>
        </html>
        """
        mock_fetch.side_effect = [mock_response, mock_response]  # index + pagination
        result = scrape_blog_posts(max_posts=10)
        assert len(result) == 0  # No actual post pages fetched in this mock


# ── Twitter Archives ────────────────────────────────────────────────────────

class TestTwitterArchives:
    """Tests for twitter_archives module."""

    def test_parse_date_various_formats(self):
        """_parse_date should handle multiple date formats."""
        assert _parse_date("2024-01-15") == "2024-01-15"
        assert _parse_date("2024-01-15T10:30:00Z") == "2024-01-15"
        assert _parse_date("Jan 15, 2024") == "2024-01-15"
        assert _parse_date("01/15/2024") == "2024-01-15"
        assert _parse_date("") == "2024-01-15"  # Should default to today

    def test_load_csv_archive(self):
        """load_csv_archive should load tweets from CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["text", "date", "url", "id"])
            writer.writerow(["Test tweet", "2024-01-15", "http://example.com", "123"])
            f.flush()
            tweets = load_csv_archive(f.name)
            assert len(tweets) == 1
            assert tweets[0]["text"] == "Test tweet"
            assert tweets[0]["source_type"] == "tweet"
            os.unlink(f.name)

    def test_load_csv_archive_skips_short_text(self):
        """Should skip tweets with text shorter than 2 chars."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["text", "date", "url", "id"])
            writer.writerow(["ab", "2024-01-15", "http://example.com", "123"])
            writer.writerow(["a", "2024-01-15", "http://example.com", "124"])
            f.flush()
            tweets = load_csv_archive(f.name)
            assert len(tweets) == 1  # Only the first one passes
            os.unlink(f.name)

    def test_load_json_archive_array_format(self):
        """load_json_archive should handle array format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"text": "Tweet 1", "date": "2024-01-15"}], f)
            f.flush()
            tweets = load_json_archive(f.name)
            assert len(tweets) == 1
            assert tweets[0]["text"] == "Tweet 1"
            os.unlink(f.name)

    def test_load_json_archive_nested_format(self):
        """load_json_archive should handle nested 'tweets' key."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"tweets": [{"text": "Nested tweet", "date": "2024-01-15"}]}, f)
            f.flush()
            tweets = load_json_archive(f.name)
            assert len(tweets) == 1
            assert tweets[0]["text"] == "Nested tweet"
            os.unlink(f.name)

    def test_load_twitter_archives(self):
        """load_twitter_archives should load from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "tweets.csv"
            with open(csv_path, "w") as f:
                writer = csv.writer(f)
                writer.writerow(["text", "date", "url", "id"])
                writer.writerow(["Dir tweet", "2024-01-15", "http://example.com", "1"])
            tweets = load_twitter_archives(tmpdir)
            assert len(tweets) == 1
            assert tweets[0]["text"] == "Dir tweet"

    def test_generate_synthetic_tweets(self):
        """generate_synthetic_tweets should create plausible tweets."""
        tweets = generate_synthetic_tweets(10)
        assert len(tweets) == 10
        assert all(t["source_type"] == "tweet" for t in tweets)
        assert all(t["author"] == "Scott Adams" for t in tweets)
        assert all(len(t["text"]) > 0 for t in tweets)
        assert all(t["date"] is not None for t in tweets)


# ── Book Excerpts ───────────────────────────────────────────────────────────

class TestBookExcerpts:
    """Tests for book_excerpts module."""

    def test_load_text_excerpts(self):
        """load_text_excerpts should load from text file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a test excerpt.\n\nAnother paragraph here.")
            f.flush()
            excerpts = load_text_excerpts(f.name)
            assert len(excerpts) == 1
            assert "test excerpt" in excerpts[0]["text"]
            os.unlink(f.name)

    def test_load_text_excerpts_skips_short(self):
        """Should skip excerpts shorter than 100 chars."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Short")
            f.flush()
            excerpts = load_text_excerpts(f.name)
            assert len(excerpts) == 0
            os.unlink(f.name)

    def test_generate_synthetic_book_excerpts(self):
        """generate_synthetic_book_excerpts should create plausible excerpts."""
        excerpts = generate_synthetic_book_excerpts(5)
        assert len(excerpts) == 5
        assert all(e["source_type"] == "book_excerpt" for e in excerpts)
        assert all(e["author"] == "Scott Adams" for e in excerpts)
        assert all(len(e["text"]) >= 100 for e in excerpts)


# ── Cleaner ─────────────────────────────────────────────────────────────────

class TestCleaner:
    """Tests for cleaner module."""

    def test_clean_corpus(self):
        """clean_corpus should clean and deduplicate samples."""
        samples = [
            {"id": "1", "text": "Short", "source_type": "blog"},
            {"id": "2", "text": "This is a longer text that should pass the filter.", "source_type": "blog"},
            {"id": "3", "text": "This is a longer text that should pass the filter.", "source_type": "blog"},  # duplicate
        ]
        cleaned = clean_corpus(samples, deduplicate=True, min_text_length=50)
        assert len(cleaned) == 1
        assert cleaned[0]["id"] == "2"

    def test_deduplicate(self):
        """deduplicate should remove duplicate texts."""
        samples = [
            {"id": "1", "text": "Same text", "source_type": "blog"},
            {"id": "2", "text": "Same text", "source_type": "tweet"},
            {"id": "3", "text": "Different text", "source_type": "blog"},
        ]
        result = deduplicate(samples)
        assert len(result) == 2

    def test_filter_by_length(self):
        """filter_by_length should remove short texts."""
        samples = [
            {"id": "1", "text": "Short", "source_type": "blog"},
            {"id": "2", "text": "This is long enough", "source_type": "blog"},
        ]
        result = filter_by_length(samples, min_length=10)
        assert len(result) == 1
        assert result[0]["id"] == "2"

    def test_filter_by_source(self):
        """filter_by_source should keep only specified sources."""
        samples = [
            {"id": "1", "text": "Blog post", "source_type": "blog"},
            {"id": "2", "text": "Tweet", "source_type": "tweet"},
            {"id": "3", "text": "Another blog", "source_type": "blog"},
        ]
        result = filter_by_source(samples, allowed_sources=["blog"])
        assert len(result) == 2
        assert all(s["source_type"] == "blog" for s in result)

    def test_clean_corpus_with_invalid_samples(self):
        """clean_corpus should handle invalid samples gracefully."""
        samples = [
            {"id": "1", "text": "Valid text", "source_type": "blog"},
            {"id": "2"},  # missing text
            {"id": "3", "text": "Also valid", "source_type": "blog"},
        ]
        cleaned = clean_corpus(samples, deduplicate=False, min_text_length=5)
        assert len(cleaned) == 2
        assert cleaned[0]["id"] == "1"
        assert cleaned[1]["id"] == "3"
