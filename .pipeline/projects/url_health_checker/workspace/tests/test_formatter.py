"""Tests for url_health_checker.formatter module."""

import json
import unittest

from url_health_checker.formatter import format_results


class TestFormatResultsText(unittest.TestCase):
    """Tests for text output format."""

    def test_empty_results(self):
        result = format_results([], fmt="text")
        self.assertEqual(result, "No URLs to report.")

    def test_single_url(self):
        results = [
            {
                "url": "http://example.com",
                "status_code": 200,
                "response_time_ms": 42.5,
                "up": True,
            }
        ]
        output = format_results(results, fmt="text")
        self.assertIn("http://example.com", output)
        self.assertIn("200", output)
        self.assertIn("42.50", output)
        self.assertIn("True", output)

    def test_multiple_urls(self):
        results = [
            {
                "url": "http://a.com",
                "status_code": 200,
                "response_time_ms": 10.0,
                "up": True,
            },
            {
                "url": "http://b.com",
                "status_code": 404,
                "response_time_ms": 5.0,
                "up": False,
            },
        ]
        output = format_results(results, fmt="text")
        self.assertIn("http://a.com", output)
        self.assertIn("http://b.com", output)
        self.assertIn("200", output)
        self.assertIn("404", output)

    def test_none_values(self):
        results = [
            {
                "url": "http://broken.com",
                "status_code": None,
                "response_time_ms": None,
                "up": False,
            }
        ]
        output = format_results(results, fmt="text")
        self.assertIn("None", output)
        self.assertIn("False", output)


class TestFormatResultsJson(unittest.TestCase):
    """Tests for JSON output format."""

    def test_json_output(self):
        results = [
            {
                "url": "http://example.com",
                "status_code": 200,
                "response_time_ms": 42.5,
                "up": True,
            }
        ]
        output = format_results(results, fmt="json")
        parsed = json.loads(output)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["url"], "http://example.com")
        self.assertEqual(parsed[0]["status_code"], 200)
        self.assertTrue(parsed[0]["up"])

    def test_empty_json(self):
        output = format_results([], fmt="json")
        parsed = json.loads(output)
        self.assertEqual(parsed, [])

    def test_json_is_valid_json(self):
        results = [
            {
                "url": "http://example.com",
                "status_code": 200,
                "response_time_ms": 10.0,
                "up": True,
            }
        ]
        output = format_results(results, fmt="json")
        # Should not raise
        json.loads(output)


if __name__ == "__main__":
    unittest.main()
