"""Tests for the PodcastSEO CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from podcastseo.cli import app
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def sample_srt(tmp_path: Path) -> Path:
    """Create a sample SRT file."""
    srt_content = """1
00:00:01,000 --> 00:00:04,000
Welcome to the Tech Talk podcast.

2
00:00:05,000 --> 00:00:08,000
Today we're discussing artificial intelligence and machine learning.

3
00:00:09,000 --> 00:00:12,000
Our guest is an expert in deep learning and neural networks.
"""
    path = tmp_path / "sample.srt"
    path.write_text(srt_content, encoding="utf-8")
    return path


@pytest.fixture
def sample_txt(tmp_path: Path) -> Path:
    """Create a sample TXT file."""
    txt_content = """Welcome to the Tech Talk podcast.
Today we're discussing artificial intelligence and machine learning.
Our guest is an expert in deep learning and neural networks.
"""
    path = tmp_path / "sample.txt"
    path.write_text(txt_content, encoding="utf-8")
    return path


class TestKeywordsCommand:
    """Tests for the 'keywords' CLI command."""

    def test_keywords_srt_file(self, sample_srt: Path) -> None:
        """Test extracting keywords from an SRT file."""
        result = runner.invoke(app, ["keywords", str(sample_srt), "--top", "5"])
        assert result.exit_code == 0
        # Keywords go to stdout as JSON; status messages go to stderr
        combined = result.stdout + result.stderr
        assert "Extracted" in combined
        # Parse JSON output from stdout
        keywords = json.loads(result.stdout)
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        for kw in keywords:
            assert "keyword" in kw
            assert "score" in kw
            assert "category" in kw
            assert "occurrences" in kw

    def test_keywords_txt_file(self, sample_txt: Path) -> None:
        """Test extracting keywords from a TXT file."""
        result = runner.invoke(app, ["keywords", str(sample_txt), "--top", "3"])
        assert result.exit_code == 0
        combined = result.stdout + result.stderr
        assert "Extracted" in combined
        keywords = json.loads(result.stdout)
        assert isinstance(keywords, list)
        assert len(keywords) <= 3

    def test_keywords_output_to_file(self, sample_srt: Path, tmp_path: Path) -> None:
        """Test writing keywords to an output file."""
        output_path = tmp_path / "keywords.json"
        result = runner.invoke(app, ["keywords", str(sample_srt), "--top", "5", "--output", str(output_path)])
        assert result.exit_code == 0
        assert output_path.exists()
        content = json.loads(output_path.read_text(encoding="utf-8"))
        assert isinstance(content, list)

    def test_keywords_nonexistent_file(self, tmp_path: Path) -> None:
        """Test error handling for nonexistent file."""
        result = runner.invoke(app, ["keywords", str(tmp_path / "nonexistent.srt")])
        assert result.exit_code != 0
        assert "Error" in result.stdout or "Error" in result.stderr

    def test_keywords_unsupported_format(self, tmp_path: Path) -> None:
        """Test error handling for unsupported file format."""
        unsupported = tmp_path / "file.pdf"
        unsupported.write_text("test", encoding="utf-8")
        result = runner.invoke(app, ["keywords", str(unsupported)])
        assert result.exit_code != 0
        combined = result.stdout + result.stderr
        assert "Unsupported" in combined or "Error" in combined


class TestNotesCommand:
    """Tests for the 'notes' CLI command."""

    def test_notes_markdown(self, sample_srt: Path) -> None:
        """Test generating markdown show notes."""
        result = runner.invoke(app, ["notes", str(sample_srt), "--format", "markdown"])
        assert result.exit_code == 0
        combined = result.stdout + result.stderr
        assert "Show notes" in combined or "generated" in combined.lower()

    def test_notes_html(self, sample_srt: Path) -> None:
        """Test generating HTML show notes."""
        result = runner.invoke(app, ["notes", str(sample_srt), "--format", "html"])
        assert result.exit_code == 0

    def test_notes_txt(self, sample_srt: Path) -> None:
        """Test generating plain text show notes."""
        result = runner.invoke(app, ["notes", str(sample_srt), "--format", "txt"])
        assert result.exit_code == 0

    def test_notes_output_to_file(self, sample_srt: Path, tmp_path: Path) -> None:
        """Test writing show notes to an output file."""
        output_path = tmp_path / "notes.md"
        result = runner.invoke(app, ["notes", str(sample_srt), "--format", "markdown", "--output", str(output_path)])
        assert result.exit_code == 0
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_notes_with_keywords_file(self, sample_srt: Path, tmp_path: Path) -> None:
        """Test generating show notes with a provided keywords file."""
        # First generate keywords
        kw_output = tmp_path / "keywords.json"
        runner.invoke(app, ["keywords", str(sample_srt), "--top", "5", "--output", str(kw_output)])
        
        # Then generate notes with keywords
        result = runner.invoke(app, [
            "notes", str(sample_srt), "--format", "markdown", "--keywords", str(kw_output)
        ])
        assert result.exit_code == 0

    def test_notes_nonexistent_file(self, tmp_path: Path) -> None:
        """Test error handling for nonexistent input file."""
        result = runner.invoke(app, ["notes", str(tmp_path / "nonexistent.srt")])
        assert result.exit_code != 0
        assert "Error" in result.stdout or "Error" in result.stderr

    def test_notes_invalid_format(self, sample_srt: Path) -> None:
        """Test error handling for invalid output format."""
        result = runner.invoke(app, ["notes", str(sample_srt), "--format", "xml"])
        # Should fail with invalid format
        assert result.exit_code != 0


class TestCLIIntegration:
    """Integration tests for the CLI."""

    def test_cli_help(self) -> None:
        """Test that CLI help works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "PodcastSEO" in result.stdout

    def test_keywords_help(self) -> None:
        """Test keywords command help."""
        result = runner.invoke(app, ["keywords", "--help"])
        assert result.exit_code == 0
        assert "extract keywords" in result.stdout.lower()

    def test_notes_help(self) -> None:
        """Test notes command help."""
        result = runner.invoke(app, ["notes", "--help"])
        assert result.exit_code == 0
        assert "show notes" in result.stdout.lower()
