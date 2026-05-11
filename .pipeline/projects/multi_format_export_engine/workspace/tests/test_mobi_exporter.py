"""Tests for the MOBI exporter."""

import os
import shutil
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from multi_format_export_engine.exporters.mobi_exporter import MOBIExporter
from multi_format_export_engine.models import Manuscript


class TestMOBIExporter:
    """Tests for the MOBI exporter."""

    def test_export_creates_file(self):
        """Test that export creates a file."""
        m = Manuscript(title="Test Book")
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            result = exporter.export(m, output_path=output_path)
            assert os.path.exists(result)

    def test_export_returns_path(self):
        """Test that export returns the output path (or fallback path)."""
        m = Manuscript(title="Test Book")
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            result = exporter.export(m, output_path=output_path)
            # When calibre is not available, returns .epub fallback
            assert result.endswith(".epub")
            assert os.path.exists(result)

    @patch("subprocess.run")
    def test_export_with_calibre_calls_subprocess(self, mock_run):
        """Test that export calls subprocess when calibre is available."""
        mock_run.return_value = MagicMock(returncode=0)

        m = Manuscript(title="Test Book")
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            exporter.export(m, output_path=output_path)
            mock_run.assert_called_once()
            assert "ebook-convert" in mock_run.call_args[0][0]

    @patch("subprocess.run")
    def test_export_with_calibre_returns_path(self, mock_run):
        """Test that export returns the MOBI path when calibre succeeds."""
        mock_run.return_value = MagicMock(returncode=0)

        m = Manuscript(title="Test Book")
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            result = exporter.export(m, output_path=output_path)
            assert result == output_path
            assert result.endswith(".mobi")

    @patch("subprocess.run")
    def test_export_without_calibre_falls_back_to_epub(self, mock_run):
        """Test that export falls back to EPUB when calibre is not available."""
        mock_run.side_effect = FileNotFoundError()

        m = Manuscript(title="Test Book")
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            result = exporter.export(m, output_path=output_path)
            assert result.endswith(".epub")
            assert os.path.exists(result)

    @patch("subprocess.run")
    def test_export_without_calibre_does_not_call_subprocess(self, mock_run):
        """Test that export doesn't call subprocess when calibre is not available."""
        mock_run.side_effect = FileNotFoundError()

        m = Manuscript(title="Test Book")
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            exporter.export(m, output_path=output_path)
            mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_export_calibre_failure_falls_back(self, mock_run):
        """Test that export falls back when calibre fails."""
        mock_run.return_value = MagicMock(returncode=1)

        m = Manuscript(title="Test Book")
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            result = exporter.export(m, output_path=output_path)
            assert result.endswith(".epub")

    @patch("subprocess.run")
    def test_export_calibre_nonzero_exit_falls_back(self, mock_run):
        """Test that export falls back on non-zero exit code."""
        mock_run.return_value = MagicMock(returncode=1)

        m = Manuscript(title="Test Book")
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            result = exporter.export(m, output_path=output_path)
            assert result.endswith(".epub")

    def test_export_empty_manuscript(self):
        """Test export with empty manuscript."""
        m = Manuscript(title="Empty Book")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            result = exporter.export(m, output_path=output_path)
            assert os.path.exists(result)

    def test_export_with_author(self):
        """Test export with author metadata."""
        m = Manuscript(title="Test Book", author="Test Author")
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            result = exporter.export(m, output_path=output_path)
            assert os.path.exists(result)

    def test_export_with_metadata(self):
        """Test export with custom metadata."""
        m = Manuscript(title="Test Book", author="Test Author")
        m.metadata["genre"] = "fiction"
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            result = exporter.export(m, output_path=output_path)
            assert os.path.exists(result)

    def test_export_multi_chapter(self):
        """Test export with multiple chapters."""
        m = Manuscript(title="Test Book")
        ch1 = m.add_chapter_title("Chapter 1")
        ch1.add_paragraph("First")
        ch2 = m.add_chapter_title("Chapter 2")
        ch2.add_paragraph("Second")

        exporter = MOBIExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.mobi")
            result = exporter.export(m, output_path=output_path)
            assert os.path.exists(result)
