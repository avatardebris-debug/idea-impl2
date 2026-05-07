"""Tests for CLI module."""

import io
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.url_health_checker.cli import main, _read_urls, _format_table


class TestReadUrls(unittest.TestCase):
    """Tests for _read_urls helper."""

    def test_reads_urls_from_file(self):
        """Should read URLs from a text file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("http://example.com\nhttp://test.org\n")
            f.flush()
            path = f.name
        try:
            urls = _read_urls(path)
            self.assertEqual(urls, ["http://example.com", "http://test.org"])
        finally:
            os.unlink(path)

    def test_skips_blank_lines(self):
        """Blank lines should be skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("http://example.com\n\nhttp://test.org\n\n")
            f.flush()
            path = f.name
        try:
            urls = _read_urls(path)
            self.assertEqual(urls, ["http://example.com", "http://test.org"])
        finally:
            os.unlink(path)

    def test_strips_whitespace(self):
        """Leading/trailing whitespace should be stripped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("  http://example.com  \n")
            f.flush()
            path = f.name
        try:
            urls = _read_urls(path)
            self.assertEqual(urls, ["http://example.com"])
        finally:
            os.unlink(path)


class TestFormatTable(unittest.TestCase):
    """Tests for _format_table helper."""

    def test_table_has_header(self):
        """Table should contain header row."""
        results = [
            {"url": "http://example.com", "status_code": 200, "response_time_ms": 50.0, "is_up": True},
        ]
        output = _format_table(results)
        self.assertIn("URL", output)
        self.assertIn("Status", output)
        self.assertIn("Time (ms)", output)

    def test_table_shows_up_down(self):
        """Table should show UP or DOWN."""
        results = [
            {"url": "http://up.com", "status_code": 200, "response_time_ms": 10.0, "is_up": True},
            {"url": "http://down.com", "status_code": 404, "response_time_ms": 20.0, "is_up": False},
        ]
        output = _format_table(results)
        self.assertIn("UP", output)
        self.assertIn("DOWN", output)

    def test_table_shows_n_a_for_none(self):
        """None values should show as N/A."""
        results = [
            {"url": "http://broken.com", "status_code": None, "response_time_ms": None, "is_up": False},
        ]
        output = _format_table(results)
        self.assertIn("N/A", output)


class TestMainCLI(unittest.TestCase):
    """Integration-style tests for the CLI main function."""

    def _write_urls(self, content: str) -> str:
        """Helper to create a temp file with URLs."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        f.write(content)
        f.flush()
        f.close()
        return f.name

    @patch("src.url_health_checker.cli.check_urls_concurrent")
    def test_main_prints_table(self, mock_concurrent):
        """main() should print a formatted table."""
        mock_concurrent.return_value = [
            {"url": "http://example.com", "status_code": 200, "response_time_ms": 50.0, "is_up": True},
        ]
        path = self._write_urls("http://example.com\n")
        try:
            captured = io.StringIO()
            with patch("sys.stdout", captured):
                main(["--input", path])
            output = captured.getvalue()
            self.assertIn("http://example.com", output)
            self.assertIn("200", output)
            self.assertIn("UP", output)
        finally:
            os.unlink(path)

    @patch("src.url_health_checker.cli.check_urls_concurrent")
    def test_main_passes_timeout(self, mock_concurrent):
        """--timeout flag should be passed through."""
        mock_concurrent.return_value = []
        path = self._write_urls("http://example.com\n")
        try:
            with patch("sys.stdout", io.StringIO()):
                main(["--input", path, "--timeout", "30"])
            # Verify the call was made with timeout=30
            call_kwargs = mock_concurrent.call_args
            self.assertEqual(call_kwargs[1]["timeout"], 30)
        finally:
            os.unlink(path)

    @patch("src.url_health_checker.cli.check_urls_concurrent")
    def test_main_passes_workers(self, mock_concurrent):
        """--workers flag should be passed through."""
        mock_concurrent.return_value = []
        path = self._write_urls("http://example.com\n")
        try:
            with patch("sys.stdout", io.StringIO()):
                main(["--input", path, "--workers", "10"])
            call_kwargs = mock_concurrent.call_args
            self.assertEqual(call_kwargs[1]["max_workers"], 10)
        finally:
            os.unlink(path)

    def test_main_exits_on_empty_file(self):
        """main() should exit with code 1 if no URLs found."""
        path = self._write_urls("")
        try:
            with self.assertRaises(SystemExit) as ctx:
                main(["--input", path])
            self.assertEqual(ctx.exception.code, 1)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
