"""Tests for url_health_checker.loader module."""

import os
import tempfile
import textwrap
import unittest

from url_health_checker.loader import load_urls


class TestLoadUrls(unittest.TestCase):
    """Tests for the load_urls function."""

    def _write_temp_file(self, content: str) -> str:
        """Write content to a temp file and return its path."""
        fd, path = tempfile.mkstemp(suffix=".txt", text=True)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    # --- Valid URL parsing ---

    def test_load_single_http_url(self):
        path = self._write_temp_file("http://example.com\n")
        try:
            result = load_urls(path)
            self.assertEqual(result, ["http://example.com"])
        finally:
            os.unlink(path)

    def test_load_single_https_url(self):
        path = self._write_temp_file("https://example.com/path\n")
        try:
            result = load_urls(path)
            self.assertEqual(result, ["https://example.com/path"])
        finally:
            os.unlink(path)

    def test_load_multiple_urls(self):
        content = "http://a.com\nhttps://b.com\nhttp://c.com/d\n"
        path = self._write_temp_file(content)
        try:
            result = load_urls(path)
            self.assertEqual(len(result), 3)
            self.assertIn("http://a.com", result)
            self.assertIn("https://b.com", result)
            self.assertIn("http://c.com/d", result)
        finally:
            os.unlink(path)

    # --- Comment skipping ---

    def test_skips_comment_lines(self):
        content = "# This is a comment\nhttp://example.com\n# Another comment\n"
        path = self._write_temp_file(content)
        try:
            result = load_urls(path)
            self.assertEqual(result, ["http://example.com"])
        finally:
            os.unlink(path)

    def test_skips_comment_with_leading_whitespace(self):
        content = "  # indented comment\nhttp://example.com\n"
        path = self._write_temp_file(content)
        try:
            result = load_urls(path)
            self.assertEqual(result, ["http://example.com"])
        finally:
            os.unlink(path)

    # --- Blank-line skipping ---

    def test_skips_blank_lines(self):
        content = "\nhttp://example.com\n\nhttps://other.com\n\n"
        path = self._write_temp_file(content)
        try:
            result = load_urls(path)
            self.assertEqual(len(result), 2)
            self.assertIn("http://example.com", result)
            self.assertIn("https://other.com", result)
        finally:
            os.unlink(path)

    def test_all_blank_file(self):
        content = "\n\n\n"
        path = self._write_temp_file(content)
        try:
            result = load_urls(path)
            self.assertEqual(result, [])
        finally:
            os.unlink(path)

    # --- Error handling ---

    def test_raises_value_error_for_missing_scheme(self):
        content = "ftp://example.com\n"
        path = self._write_temp_file(content)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_urls(path)
            self.assertIn("invalid URL", str(ctx.exception))
        finally:
            os.unlink(path)

    def test_raises_value_error_for_no_host(self):
        content = "http:///path\n"
        path = self._write_temp_file(content)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_urls(path)
            self.assertIn("missing a host", str(ctx.exception))
        finally:
            os.unlink(path)

    def test_raises_value_error_for_invalid_line(self):
        content = "not a url\n"
        path = self._write_temp_file(content)
        try:
            with self.assertRaises(ValueError) as ctx:
                load_urls(path)
            self.assertIn("invalid URL", str(ctx.exception))
        finally:
            os.unlink(path)

    def test_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_urls("/nonexistent/path.txt")


if __name__ == "__main__":
    unittest.main()
