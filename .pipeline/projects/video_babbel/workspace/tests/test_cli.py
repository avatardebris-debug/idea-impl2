"""Tests for the VideoBabbel CLI (click-based command-line interface).

All CLI tests use Click's ``CliRunner`` to invoke commands without
starting a real subprocess.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Ensure the workspace root is on sys.path so imports work
_ws = Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_babbel.cli import cli, SUPPORTED_LANGUAGES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    """Return a Click CliRunner for invoking the CLI."""
    return CliRunner()


# ---------------------------------------------------------------------------
# CLI entry-point tests
# -----------------------------------------------------------------------------------

class TestCLIEntryPoint:
    """Tests for the CLI entry-point and help output."""

    def test_help(self, runner):
        """--help should exit with code 0 and show usage."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_default_language(self, runner):
        """Default target language should be Spanish."""
        result = runner.invoke(cli, ["--help"])
        assert "es" in result.output

    def test_version(self, runner):
        """--version should show the package version."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "VideoBabbel" in result.output


# ---------------------------------------------------------------------------
# CLI process command
# -----------------------------------------------------------------------------------

class TestProcessCommand:
    """Tests for the ``process`` sub-command."""

    @patch("video_babbel.cli.VideoBabbel")
    def test_process_default_params(self, mock_pipeline_cls, runner):
        """process with no extra flags should use defaults."""
        mock_instance = MagicMock()
        mock_instance.process.return_value = {
            "transcript": [{"text": "Hi", "start": 0.0, "end": 1.0}],
            "translation": "Hola",
            "summary": "Summary",
            "qa": "Answer",
        }
        mock_pipeline_cls.return_value = mock_instance

        result = runner.invoke(cli, ["process", "/fake/video.mp4"])
        assert result.exit_code == 0
        assert "Hola" in result.output

        # Verify the pipeline was instantiated with default params
        mock_pipeline_cls.assert_called_once_with(
            target_lang="es",
            whisper_model="base",
            max_sentences=5,
            backend="google",
        )

    @patch("video_babbel.cli.VideoBabbel")
    def test_process_custom_params(self, mock_pipeline_cls, runner):
        """process should honour all CLI flags."""
        mock_instance = MagicMock()
        mock_instance.process.return_value = {
            "transcript": [{"text": "Hi", "start": 0.0, "end": 1.0}],
            "translation": "Bonjour",
            "summary": "Summary",
            "qa": "Answer",
        }
        mock_pipeline_cls.return_value = mock_instance

        result = runner.invoke(
            cli,
            [
                "process",
                "/fake/video.mp4",
                "--target-lang",
                "fr",
                "--whisper-model",
                "small",
                "--max-sentences",
                "10",
                "--backend",
                "deepL",
            ],
        )
        assert result.exit_code == 0
        assert "Bonjour" in result.output

        mock_pipeline_cls.assert_called_once_with(
            target_lang="fr",
            whisper_model="small",
            max_sentences=10,
            backend="deepL",
        )

    @patch("video_babbel.cli.VideoBabbel")
    def test_process_output_json(self, mock_pipeline_cls, runner):
        """--output-json should produce valid JSON."""
        mock_instance = MagicMock()
        mock_instance.process.return_value = {
            "transcript": [{"text": "Hi", "start": 0.0, "end": 1.0}],
            "translation": "Hola",
            "summary": "Summary",
            "qa": "Answer",
        }
        mock_pipeline_cls.return_value = mock_instance

        result = runner.invoke(cli, ["process", "/fake/video.mp4", "--output-json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["translation"] == "Hola"

    @patch("video_babbel.cli.VideoBabbel")
    def test_process_output_file(self, mock_pipeline_cls, runner):
        """--output-file should write to a file."""
        mock_instance = MagicMock()
        mock_instance.process.return_value = {
            "transcript": [{"text": "Hi", "start": 0.0, "end": 1.0}],
            "translation": "Hola",
            "summary": "Summary",
            "qa": "Answer",
        }
        mock_pipeline_cls.return_value = mock_instance

        output_path = "/tmp/test_output.json"
        result = runner.invoke(
            cli,
            ["process", "/fake/video.mp4", "--output-file", output_path],
        )
        assert result.exit_code == 0
        assert Path(output_path).exists()
        data = json.loads(Path(output_path).read_text())
        assert data["translation"] == "Hola"

    @patch("video_babbel.cli.VideoBabbel")
    def test_process_error_handling(self, mock_pipeline_cls, runner):
        """process should handle pipeline errors gracefully."""
        from video_babbel.core import VideoBabbelError

        mock_instance = MagicMock()
        mock_instance.process.side_effect = VideoBabbelError("Pipeline failed")
        mock_pipeline_cls.return_value = mock_instance

        result = runner.invoke(cli, ["process", "/fake/video.mp4"])
        assert result.exit_code != 0
        assert "Pipeline failed" in result.output

    def test_process_no_video_path(self, runner):
        """process without a video path should show an error."""
        result = runner.invoke(cli, ["process"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output


# ---------------------------------------------------------------------------
# CLI list-languages command
# -----------------------------------------------------------------------------------

class TestListLanguagesCommand:
    """Tests for the ``list-languages`` sub-command."""

    def test_list_languages(self, runner):
        """list-languages should show available languages."""
        result = runner.invoke(cli, ["list-languages"])
        assert result.exit_code == 0
        assert "es" in result.output
        assert "fr" in result.output
        assert "de" in result.output

    def test_list_languages_json(self, runner):
        """list-languages --json should produce valid JSON."""
        result = runner.invoke(cli, ["list-languages", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert "es" in data
        assert "fr" in data


# ---------------------------------------------------------------------------
# CLI validate command
# -----------------------------------------------------------------------------------

class TestValidateCommand:
    """Tests for the ``validate`` sub-command."""

    @patch("video_babbel.cli.VideoBabbel")
    def test_validate_success(self, mock_pipeline_cls, runner):
        """validate should succeed when all checks pass."""
        mock_instance = MagicMock()
        mock_instance.process.return_value = {
            "transcript": [{"text": "Hi", "start": 0.0, "end": 1.0}],
            "translation": "Hola",
            "summary": "Summary",
            "qa": "Answer",
        }
        mock_pipeline_cls.return_value = mock_instance

        result = runner.invoke(cli, ["validate", "/fake/video.mp4"])
        assert result.exit_code == 0
        assert "All checks passed" in result.output

    @patch("video_babbel.cli.VideoBabbel")
    def test_validate_failure(self, mock_pipeline_cls, runner):
        """validate should fail when pipeline errors."""
        from video_babbel.core import VideoBabbelError

        mock_instance = MagicMock()
        mock_instance.process.side_effect = VideoBabbelError("Failed")
        mock_pipeline_cls.return_value = mock_instance

        result = runner.invoke(cli, ["validate", "/fake/video.mp4"])
        assert result.exit_code != 0
        assert "Failed" in result.output


# ---------------------------------------------------------------------------
# CLI error handling
# -----------------------------------------------------------------------------------

class TestCLIErrorHandling:
    """Tests for CLI-level error handling."""

    def test_invalid_subcommand(self, runner):
        """An invalid subcommand should show an error."""
        result = runner.invoke(cli, ["invalid-command"])
        assert result.exit_code != 0

    def test_invalid_backend(self, runner):
        """An invalid backend should show an error."""
        result = runner.invoke(cli, ["process", "/fake/video.mp4", "--backend", "invalid"])
        assert result.exit_code != 0

    def test_invalid_language(self, runner):
        """An invalid language code should show an error."""
        result = runner.invoke(cli, ["process", "/fake/video.mp4", "--target-lang", "xx"])
        assert result.exit_code != 0

    def test_invalid_max_sentences(self, runner):
        """An invalid max-sentences value should show an error."""
        result = runner.invoke(cli, ["process", "/fake/video.mp4", "--max-sentences", "-1"])
        assert result.exit_code != 0

    def test_invalid_whisper_model(self, runner):
        """An invalid whisper model should show an error."""
        result = runner.invoke(cli, ["process", "/fake/video.mp4", "--whisper-model", "invalid"])
        assert result.exit_code != 0
