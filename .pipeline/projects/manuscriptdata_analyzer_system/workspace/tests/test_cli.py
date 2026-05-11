"""Tests for the CLI commands (import and summary)."""

import os
import tempfile
import pytest
from click.testing import CliRunner
from manuscriptdata_analyzer.cli import cli
from manuscriptdata_analyzer.database import Database


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


class TestImportCommand:
    def test_import_sales(self, runner, db_path):
        csv_path = os.path.join(FIXTURES_DIR, "sales.csv")
        result = runner.invoke(cli, ["import-data", csv_path, "--db", db_path])
        assert result.exit_code == 0
        assert "15 rows of sales_data" in result.output

    def test_import_demographics(self, runner, db_path):
        csv_path = os.path.join(FIXTURES_DIR, "demographics.csv")
        result = runner.invoke(cli, ["import-data", csv_path, "--db", db_path])
        assert result.exit_code == 0
        assert "15 rows of demographics_data" in result.output

    def test_import_content_metrics(self, runner, db_path):
        csv_path = os.path.join(FIXTURES_DIR, "content_metrics.csv")
        result = runner.invoke(cli, ["import-data", csv_path, "--db", db_path])
        assert result.exit_code == 0
        assert "15 rows of content_metrics" in result.output

    def test_import_unrecognised_csv(self, runner, db_path):
        fd, csv_path = tempfile.mkstemp(suffix=".csv")
        os.write(fd, b"Name,Age\nAlice,30\n")
        os.close(fd)
        result = runner.invoke(cli, ["import-data", csv_path, "--db", db_path])
        assert result.exit_code != 0
        assert "Unrecognised CSV format" in result.output


class TestSummaryCommand:
    def test_summary_with_sales(self, runner, db_path):
        # Import sales data
        sales_csv = os.path.join(FIXTURES_DIR, "sales.csv")
        runner.invoke(cli, ["import-data", sales_csv, "--db", db_path])

        result = runner.invoke(cli, ["summary", "--db", db_path])
        assert result.exit_code == 0
        assert "Total Units Sold" in result.output
        assert "Total Revenue" in result.output
        assert "Platform Breakdown" in result.output

    def test_summary_with_demographics(self, runner, db_path):
        demo_csv = os.path.join(FIXTURES_DIR, "demographics.csv")
        runner.invoke(cli, ["import-data", demo_csv, "--db", db_path])

        result = runner.invoke(cli, ["summary", "--db", db_path])
        assert result.exit_code == 0
        assert "Age Group Breakdown" in result.output
        assert "Gender Breakdown" in result.output
        assert "Country Breakdown" in result.output

    def test_summary_with_content_metrics(self, runner, db_path):
        content_csv = os.path.join(FIXTURES_DIR, "content_metrics.csv")
        runner.invoke(cli, ["import-data", content_csv, "--db", db_path])

        result = runner.invoke(cli, ["summary", "--db", db_path])
        assert result.exit_code == 0
        assert "Total Chapters" in result.output
        assert "Total Word Count" in result.output
        assert "Chapter Details" in result.output

    def test_summary_all_types(self, runner, db_path):
        """Import all three types and verify summary shows all sections."""
        for csv_name in ("sales.csv", "demographics.csv", "content_metrics.csv"):
            csv_path = os.path.join(FIXTURES_DIR, csv_name)
            runner.invoke(cli, ["import-data", csv_path, "--db", db_path])

        result = runner.invoke(cli, ["summary", "--db", db_path])
        assert result.exit_code == 0
        assert "Sales Data" in result.output
        assert "Demographics Data" in result.output
        assert "Content Metrics" in result.output

    def test_summary_empty(self, runner, db_path):
        result = runner.invoke(cli, ["summary", "--db", db_path])
        assert result.exit_code == 0
        # Should still print the header even with no data
        assert "ManuscriptData Analyzer — Summary Report" in result.output
