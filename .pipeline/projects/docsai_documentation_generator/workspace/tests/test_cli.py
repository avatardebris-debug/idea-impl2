"""Tests for the DocsAI CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


# Use the workspace directory as the project root
WORKSPACE = Path(__file__).parent.parent


@pytest.fixture
def sample_project_dir() -> Path:
    """Return the path to the sample project directory."""
    return WORKSPACE / "tests" / "sample_project"


class TestCLI:
    """Test the CLI entry point and subcommands."""

    def test_cli_help(self):
        """Test that the CLI help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "docsai.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=WORKSPACE,
        )
        assert result.returncode == 0
        assert "AI-powered technical documentation assistant" in result.stdout

    def test_spec_subcommand_help(self):
        """Test that the spec subcommand help works."""
        result = subprocess.run(
            [sys.executable, "-m", "docsai.cli", "spec", "--help"],
            capture_output=True,
            text=True,
            cwd=WORKSPACE,
        )
        assert result.returncode == 0
        assert "Generate API specification" in result.stdout

    @patch("docsai.cli.spec.load_config")
    def test_spec_command_with_config(self, mock_load_config, sample_project_dir):
        """Test the spec command with a mocked config."""
        mock_load_config.return_value = {
            "output_format": "yaml",
            "languages": ["python"],
            "output_path": str(sample_project_dir / "output.yaml"),
        }

        result = subprocess.run(
            [
                sys.executable, "-m", "docsai.cli", "spec",
                "--input-dir", str(sample_project_dir),
                "--output-format", "yaml",
                "--output-path", str(sample_project_dir / "output.yaml"),
            ],
            capture_output=True,
            text=True,
            cwd=WORKSPACE,
        )
        assert result.returncode == 0
        output_path = sample_project_dir / "output.yaml"
        assert output_path.exists()
        output_path.unlink()  # Cleanup

    @patch("docsai.cli.spec.load_config")
    def test_spec_command_json_output(self, mock_load_config, sample_project_dir):
        """Test the spec command with JSON output."""
        mock_load_config.return_value = {
            "output_format": "json",
            "languages": ["python"],
            "output_path": str(sample_project_dir / "output.json"),
        }

        result = subprocess.run(
            [
                sys.executable, "-m", "docsai.cli", "spec",
                "--input-dir", str(sample_project_dir),
                "--output-format", "json",
                "--output-path", str(sample_project_dir / "output.json"),
            ],
            capture_output=True,
            text=True,
            cwd=WORKSPACE,
        )
        assert result.returncode == 0
        output_path = sample_project_dir / "output.json"
        assert output_path.exists()
        # Verify it's valid JSON
        with open(output_path) as f:
            data = json.load(f)
        assert "symbols" in data
        output_path.unlink()  # Cleanup

    @patch("docsai.cli.spec.load_config")
    def test_spec_command_invalid_language(self, mock_load_config, sample_project_dir):
        """Test the spec command with an unsupported language."""
        mock_load_config.return_value = {
            "output_format": "yaml",
            "languages": ["rust"],
            "output_path": str(sample_project_dir / "output.yaml"),
        }

        result = subprocess.run(
            [
                sys.executable, "-m", "docsai.cli", "spec",
                "--input-dir", str(sample_project_dir),
                "--output-format", "yaml",
                "--output-path", str(sample_project_dir / "output.yaml"),
            ],
            capture_output=True,
            text=True,
            cwd=WORKSPACE,
        )
        assert result.returncode != 0
        assert "Unsupported language" in result.stderr

    def test_readme_subcommand_help(self):
        """Test that the readme subcommand help works."""
        result = subprocess.run(
            [sys.executable, "-m", "docsai.cli", "readme", "--help"],
            capture_output=True,
            text=True,
            cwd=WORKSPACE,
        )
        assert result.returncode == 0
        assert "Generate README documentation" in result.stdout
