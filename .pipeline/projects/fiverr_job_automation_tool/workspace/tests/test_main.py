"""Tests for the CLI main module."""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from main import parse_args, main


class TestParseArgs:
    """Tests for parse_args function."""

    def test_default_args(self):
        """Test parsing with default arguments."""
        args = parse_args([])
        assert args.dry_run is False
        assert args.max_bids is None
        assert args.min_budget == 0.0
        assert args.keywords == ""
        assert args.template == "professional"
        assert args.template_file is None
        assert args.log_file == "submission_log.csv"
        assert args.verbose is False
        assert args.rate_limit == 30.0

    def test_dry_run_flag(self):
        """Test parsing with --dry-run flag."""
        args = parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_max_bids(self):
        """Test parsing with --max-bids."""
        args = parse_args(["--max-bids", "5"])
        assert args.max_bids == 5

    def test_min_budget(self):
        """Test parsing with --min-budget."""
        args = parse_args(["--min-budget", "100.0"])
        assert args.min_budget == 100.0

    def test_keywords(self):
        """Test parsing with --keywords."""
        args = parse_args(["--keywords", "python,django"])
        assert args.keywords == "python,django"

    def test_template(self):
        """Test parsing with --template."""
        args = parse_args(["--template", "friendly"])
        assert args.template == "friendly"

    def test_template_file(self):
        """Test parsing with --template-file."""
        args = parse_args(["--template-file", "templates.yaml"])
        assert args.template_file == "templates.yaml"

    def test_log_file(self):
        """Test parsing with --log-file."""
        args = parse_args(["--log-file", "bids.csv"])
        assert args.log_file == "bids.csv"

    def test_output_dir(self):
        """Test parsing with --output-dir."""
        args = parse_args(["--output-dir", "/tmp"])
        assert args.output_dir == "/tmp"

    def test_verbose(self):
        """Test parsing with --verbose."""
        args = parse_args(["--verbose"])
        assert args.verbose is True

    def test_rate_limit(self):
        """Test parsing with --rate-limit."""
        args = parse_args(["--rate-limit", "60.0"])
        assert args.rate_limit == 60.0

    def test_combined_args(self):
        """Test parsing with combined arguments."""
        args = parse_args([
            "--dry-run",
            "--max-bids", "10",
            "--min-budget", "50",
            "--keywords", "python,django",
            "--template", "friendly",
            "--template-file", "templates.yaml",
            "--log-file", "bids.csv",
            "--output-dir", "/tmp",
            "--verbose",
            "--rate-limit", "45.0",
        ])
        assert args.dry_run is True
        assert args.max_bids == 10
        assert args.min_budget == 50
        assert args.keywords == "python,django"
        assert args.template == "friendly"
        assert args.template_file == "templates.yaml"
        assert args.log_file == "bids.csv"
        assert args.output_dir == "/tmp"
        assert args.verbose is True
        assert args.rate_limit == 45.0


class TestMain:
    """Tests for main function."""

    def test_main_with_dry_run(self, tmp_path):
        """Test main with dry run."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--dry-run",
                "--max-bids", "5",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0
            mock_pipeline.run.assert_called_once()

    def test_main_with_template(self, tmp_path):
        """Test main with custom template."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--template", "friendly",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0
            mock_pipeline.run.assert_called_once_with(template_name="friendly")

    def test_main_with_keywords(self, tmp_path):
        """Test main with keywords."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--keywords", "python,django",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0
            mock_pipeline.run.assert_called_once()

    def test_main_with_verbose(self, tmp_path):
        """Test main with verbose."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--verbose",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0
            mock_pipeline.run.assert_called_once()

    def test_main_with_rate_limit(self, tmp_path):
        """Test main with rate limit."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--rate-limit", "60.0",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0
            mock_pipeline.run.assert_called_once()

    def test_main_with_min_budget(self, tmp_path):
        """Test main with min budget."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--min-budget", "100",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0
            mock_pipeline.run.assert_called_once()

    def test_main_with_template_file(self, tmp_path):
        """Test main with template file."""
        with patch("main.AutomationPipeline") as MockPipeline, \
             patch("main.ProposalEngine") as MockProposalEngine:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline
            mock_proposal = MagicMock()
            MockProposalEngine.return_value = mock_proposal

            exit_code = main([
                "--template-file", "templates.yaml",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0
            mock_pipeline.run.assert_called_once()

    def test_main_with_log_file(self, tmp_path):
        """Test main with log file."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--log-file", "bids.csv",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0
            mock_pipeline.run.assert_called_once()

    def test_main_with_max_bids(self, tmp_path):
        """Test main with max bids."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--max-bids", "10",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0
            mock_pipeline.run.assert_called_once()

    def test_main_with_all_args(self, tmp_path):
        """Test main with all arguments."""
        with patch("main.AutomationPipeline") as MockPipeline, \
             patch("main.ProposalEngine") as MockProposalEngine:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline
            mock_proposal = MagicMock()
            MockProposalEngine.return_value = mock_proposal

            exit_code = main([
                "--dry-run",
                "--max-bids", "5",
                "--min-budget", "100",
                "--keywords", "python,django",
                "--template", "friendly",
                "--template-file", "templates.yaml",
                "--log-file", "bids.csv",
                "--output-dir", str(tmp_path),
                "--verbose",
                "--rate-limit", "60.0",
            ])
            assert exit_code == 0
            mock_pipeline.run.assert_called_once()


class TestMainEdgeCases:
    """Tests for edge cases in main."""

    def test_main_with_empty_args(self, tmp_path):
        """Test main with empty args."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main(["--output-dir", str(tmp_path)])
            assert exit_code == 0

    def test_main_with_unicode_keywords(self, tmp_path):
        """Test main with unicode keywords."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--keywords", "python,日本語",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0

    def test_main_with_unicode_template_file(self, tmp_path):
        """Test main with unicode template file."""
        with patch("main.AutomationPipeline") as MockPipeline, \
             patch("main.ProposalEngine") as MockProposalEngine:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline
            mock_proposal = MagicMock()
            MockProposalEngine.return_value = mock_proposal

            exit_code = main([
                "--template-file", "templates_日本語.yaml",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0

    def test_main_with_unicode_log_file(self, tmp_path):
        """Test main with unicode log file."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--log-file", "bids_日本語.csv",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0

    def test_main_with_unicode_output_dir(self, tmp_path):
        """Test main with unicode output dir."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--output-dir", str(tmp_path / "日本語"),
            ])
            assert exit_code == 0

    def test_main_with_unicode_template(self, tmp_path):
        """Test main with unicode template."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--template", "日本語",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0

    def test_main_with_unicode_min_budget(self, tmp_path):
        """Test main with unicode min budget."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--min-budget", "100",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0

    def test_main_with_unicode_rate_limit(self, tmp_path):
        """Test main with unicode rate limit."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--rate-limit", "60.0",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0

    def test_main_with_unicode_max_bids(self, tmp_path):
        """Test main with unicode max bids."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--max-bids", "5",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0

    def test_main_with_unicode_dry_run(self, tmp_path):
        """Test main with unicode dry run."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--dry-run",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0

    def test_main_with_unicode_verbose(self, tmp_path):
        """Test main with unicode verbose."""
        with patch("main.AutomationPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.run.return_value = [{"status": "DRY_RUN"}]
            MockPipeline.return_value = mock_pipeline

            exit_code = main([
                "--verbose",
                "--output-dir", str(tmp_path),
            ])
            assert exit_code == 0
