"""Tests for URLChecker."""

import unittest
from unittest.mock import MagicMock, patch

from src.url_health_checker.checker import URLChecker


class TestURLChecker(unittest.TestCase):
    """Unit tests for the URLChecker class."""

    def setUp(self) -> None:
        self.checker = URLChecker(timeout=5)

    # -- happy path: 2xx status codes ----------------------------------

    @patch("src.url_health_checker.checker.requests.Session")
    def test_check_200_returns_up(self, mock_session_cls):
        """A 200 response should mark the URL as up."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.123
        mock_session_cls.return_value.head.return_value = mock_response

        result = self.checker.check("http://example.com")

        self.assertEqual(result["url"], "http://example.com")
        self.assertEqual(result["status_code"], 200)
        self.assertAlmostEqual(result["response_time_ms"], 123.0, places=1)
        self.assertTrue(result["is_up"])

    @patch("src.url_health_checker.checker.requests.Session")
    def test_check_201_returns_up(self, mock_session_cls):
        """A 201 response should mark the URL as up."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.elapsed.total_seconds.return_value = 0.0
        mock_session_cls.return_value.head.return_value = mock_response

        result = self.checker.check("http://example.com")
        self.assertTrue(result["is_up"])

    @patch("src.url_health_checker.checker.requests.Session")
    def test_check_299_returns_up(self, mock_session_cls):
        """A 299 response should mark the URL as up."""
        mock_response = MagicMock()
        mock_response.status_code = 299
        mock_response.elapsed.total_seconds.return_value = 0.0
        mock_session_cls.return_value.head.return_value = mock_response

        result = self.checker.check("http://example.com")
        self.assertTrue(result["is_up"])

    # -- error path: 4xx / 5xx ----------------------------------------

    @patch("src.url_health_checker.checker.requests.Session")
    def test_check_404_returns_down(self, mock_session_cls):
        """A 404 response should mark the URL as down."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.elapsed.total_seconds.return_value = 0.0
        mock_session_cls.return_value.head.return_value = mock_response

        result = self.checker.check("http://example.com")
        self.assertFalse(result["is_up"])
        self.assertEqual(result["status_code"], 404)

    @patch("src.url_health_checker.checker.requests.Session")
    def test_check_500_returns_down(self, mock_session_cls):
        """A 500 response should mark the URL as down."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.elapsed.total_seconds.return_value = 0.0
        mock_session_cls.return_value.head.return_value = mock_response

        result = self.checker.check("http://example.com")
        self.assertFalse(result["is_up"])

    # -- exception handling -------------------------------------------

    @patch("src.url_health_checker.checker.requests.Session")
    def test_check_timeout_returns_down(self, mock_session_cls):
        """A timeout should mark the URL as down with None values."""
        import requests as req
        mock_session_cls.return_value.head.side_effect = req.exceptions.Timeout("timed out")

        result = self.checker.check("http://example.com")
        self.assertFalse(result["is_up"])
        self.assertIsNone(result["status_code"])
        self.assertIsNone(result["response_time_ms"])

    @patch("src.url_health_checker.checker.requests.Session")
    def test_check_connection_error_returns_down(self, mock_session_cls):
        """A connection error should mark the URL as down."""
        import requests as req
        mock_session_cls.return_value.head.side_effect = req.exceptions.ConnectionError("no host")

        result = self.checker.check("http://example.com")
        self.assertFalse(result["is_up"])
        self.assertIsNone(result["status_code"])

    @patch("src.url_health_checker.checker.requests.Session")
    def test_check_generic_exception_returns_down(self, mock_session_cls):
        """Any other exception should mark the URL as down."""
        mock_session_cls.return_value.head.side_effect = ValueError("boom")

        result = self.checker.check("http://example.com")
        self.assertFalse(result["is_up"])
        self.assertIsNone(result["status_code"])

    # -- default timeout ----------------------------------------------

    def test_default_timeout(self):
        """Default timeout should be 10 seconds."""
        checker = URLChecker()
        self.assertEqual(checker.timeout, 10)


if __name__ == "__main__":
    unittest.main()
