"""Tests for CLI."""

import json
from pathlib import Path
from typer.testing import CliRunner

from podcastseo.cli import app

runner = CliRunner()


class TestCLIKeywords:
    """Tests for the keywords CLI command."""

    def test_keywords_basic(self, srt_file):
        result = runner.invoke(app, ["keywords", srt_file])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_keywords_top_option(self, srt_file):
        result = runner.invoke(app, ["keywords", srt_file, "--top", "5"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 5

    def test_keywords_output_file(self, srt_file, tmp_path):
        out = tmp_path / "output.json"
        result = runner.invoke(app, ["keywords", srt_file, "--output", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert isinstance(data, list)

    def test_keywords_vtt_file(self, vtt_file):
        result = runner.invoke(app, ["keywords", vtt_file])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_keywords_txt_file(self, txt_file):
        result = runner.invoke(app, ["keywords", txt_file])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_keywords_nonexistent_file(self):
        result = runner.invoke(app, ["keywords", "/nonexistent/file.srt"])
        assert result.exit_code == 1

    def test_keywords_unsupported_format(self, tmp_path):
        f = tmp_path / "test.pdf"
        f.write_text("test")
        result = runner.invoke(app, ["keywords", str(f)])
        assert result.exit_code == 1

    def test_keywords_empty_file(self, empty_file):
        result = runner.invoke(app, ["keywords", empty_file])
        assert result.exit_code == 0

    def test_keywords_json_structure(self, srt_file):
        result = runner.invoke(app, ["keywords", srt_file, "--top", "3"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        for item in data:
            assert "keyword" in item
            assert "score" in item
            assert "category" in item
            assert "occurrences" in item
