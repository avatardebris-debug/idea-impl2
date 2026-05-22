"""Tests for CLI."""

import pytest
from typer.testing import CliRunner
from drop_servicing_tool.cli import app


class TestCLI:
    """Tests for CLI commands."""

    def test_list_sops_empty(self):
        """Test listing SOPs when none exist."""
        runner = CliRunner()
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        # Should show no SOPs found or similar message

    def test_create_sop(self, tmp_path):
        """Test creating a new SOP."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=str(tmp_path)):
            result = runner.invoke(app, ["create", "test_sop"])
            assert result.exit_code == 0
            # SOP file should be created

    def test_run_sop_with_mock(self, tmp_path):
        """Test running an SOP with mock LLM."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=str(tmp_path)):
            # Create a test SOP
            sop_content = """
name: test_sop
description: Test SOP
inputs:
  - name: topic
    type: string
    required: true
steps:
  - name: test_step
    description: Test step
    llm_required: false
output_format: Test output
"""
            (tmp_path / "sops" / "test_sop.yaml").parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / "sops" / "test_sop.yaml").write_text(sop_content, encoding="utf-8")

            # Run the SOP
            result = runner.invoke(
                app,
                [
                    "run",
                    "test_sop",
                    "--input",
                    '{"topic": "Test topic"}',
                    "--mock",
                ],
            )
            # Should execute without error
            assert result.exit_code == 0

    def test_run_sop_missing(self):
        """Test running a non-existent SOP."""
        runner = CliRunner()
        result = runner.invoke(app, ["run", "nonexistent", "--input", "{}"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_run_sop_invalid_input(self):
        """Test running SOP with invalid JSON input."""
        runner = CliRunner()
        result = runner.invoke(app, ["run", "test", "--input", "not json"])
        assert result.exit_code != 0
        assert "invalid json" in result.output.lower()

    def test_bulk_list_empty(self, tmp_path, monkeypatch):
        """Test listing bulk queues when none exist."""
        # Set environment variable to use isolated temp directory
        monkeypatch.setenv("DST_BULK_BASE_DIR", str(tmp_path))
        
        runner = CliRunner()
        result = runner.invoke(app, ["bulk", "list"])
        assert result.exit_code == 0
        assert "no bulk queues found" in result.output.lower()

    def test_export_csv_no_results(self, tmp_path):
        """Test exporting CSV when no results exist."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=str(tmp_path)):
            result = runner.invoke(app, ["export", "csv", "test_queue", "-o", "output.csv"])
            assert result.exit_code == 0
            assert "no results to export" in result.output.lower()

    def test_api_start(self):
        """Test API start command."""
        runner = CliRunner()
        result = runner.invoke(app, ["api", "start", "--help"])
        assert result.exit_code == 0
        assert "host" in result.output.lower()
        assert "port" in result.output.lower()
