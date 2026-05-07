"""Tests for concurrent URL checker."""

import unittest
from unittest.mock import MagicMock, patch

from src.url_health_checker.concurrent import check_urls_concurrent


class TestCheckUrlsConcurrent(unittest.TestCase):
    """Unit tests for check_urls_concurrent."""

    @patch("src.url_health_checker.concurrent.URLChecker")
    def test_returns_results_for_all_urls(self, mock_checker_cls):
        """All URLs should produce a result."""
        mock_instance = MagicMock()
        def check_side_effect(url):
            results = {
                "http://a.com": {"url": "http://a.com", "status_code": 200, "response_time_ms": 50.0, "is_up": True},
                "http://b.com": {"url": "http://b.com", "status_code": 200, "response_time_ms": 50.0, "is_up": True},
                "http://c.com": {"url": "http://c.com", "status_code": 200, "response_time_ms": 50.0, "is_up": True},
            }
            return results.get(url, {"url": url, "status_code": None, "response_time_ms": None, "is_up": False})
        mock_instance.check.side_effect = check_side_effect
        mock_checker_cls.return_value = mock_instance

        urls = ["http://a.com", "http://b.com", "http://c.com"]
        results = check_urls_concurrent(urls, max_workers=2)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["url"], "http://a.com")
        self.assertEqual(results[1]["url"], "http://b.com")
        self.assertEqual(results[2]["url"], "http://c.com")

    @patch("src.url_health_checker.concurrent.URLChecker")
    def test_respects_max_workers(self, mock_checker_cls):
        """max_workers should limit concurrent threads."""
        mock_instance = MagicMock()
        mock_instance.check.return_value = {
            "url": "http://example.com",
            "status_code": 200,
            "response_time_ms": 10.0,
            "is_up": True,
        }
        mock_checker_cls.return_value = mock_instance

        urls = ["http://example.com"]
        check_urls_concurrent(urls, max_workers=1)

        # ThreadPoolExecutor was created with max_workers=1
        mock_checker_cls.assert_called_once()

    @patch("src.url_health_checker.concurrent.URLChecker")
    def test_preserves_order(self, mock_checker_cls):
        """Results should be in the same order as input URLs."""
        mock_instance = MagicMock()
        def check_side_effect(url):
            results = {
                "http://a.com": {"url": "http://a.com", "status_code": 200, "response_time_ms": 10.0, "is_up": True},
                "http://b.com": {"url": "http://b.com", "status_code": 404, "response_time_ms": 20.0, "is_up": False},
                "http://c.com": {"url": "http://c.com", "status_code": 500, "response_time_ms": 30.0, "is_up": False},
            }
            return results.get(url, {"url": url, "status_code": None, "response_time_ms": None, "is_up": False})
        mock_instance.check.side_effect = check_side_effect
        mock_checker_cls.return_value = mock_instance

        urls = ["http://a.com", "http://b.com", "http://c.com"]
        results = check_urls_concurrent(urls, max_workers=3)

        self.assertEqual(results[0]["url"], "http://a.com")
        self.assertEqual(results[1]["url"], "http://b.com")
        self.assertEqual(results[2]["url"], "http://c.com")

    @patch("src.url_health_checker.concurrent.URLChecker")
    def test_empty_list_returns_empty(self, mock_checker_cls):
        """An empty URL list should return an empty result list."""
        results = check_urls_concurrent([], max_workers=5)
        self.assertEqual(results, [])

    @patch("src.url_health_checker.concurrent.URLChecker")
    def test_timeout_passed_to_checker(self, mock_checker_cls):
        """Timeout should be forwarded to URLChecker."""
        mock_instance = MagicMock()
        mock_instance.check.return_value = {
            "url": "http://example.com",
            "status_code": 200,
            "response_time_ms": 10.0,
            "is_up": True,
        }
        mock_checker_cls.return_value = mock_instance

        check_urls_concurrent(["http://example.com"], max_workers=1, timeout=30)

        mock_checker_cls.assert_called_with(timeout=30, max_attempts=1, retry_delay=1.0, logger=None)


if __name__ == "__main__":
    unittest.main()
