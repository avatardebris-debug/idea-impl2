"""Tests for manuscriptdata_analyzer package."""

import csv
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from manuscriptdata_analyzer.database import Database
from manuscriptdata_analyzer.csv_parser import detect_and_parse
from manuscriptdata_analyzer.analytics import (
    TrendAnalyzer,
    BookComparator,
    ReportGenerator,
    run_full_analysis,
)


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db():
    """Create a temporary SQLite database with sample data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    db.connect()

    # Insert sample sales data
    sales = [
        {"date": "2024-01-01", "book_title": "Book A", "units_sold": 100, "revenue": 1000.0, "platform": "Amazon"},
        {"date": "2024-01-02", "book_title": "Book A", "units_sold": 120, "revenue": 1200.0, "platform": "Amazon"},
        {"date": "2024-01-03", "book_title": "Book A", "units_sold": 90, "revenue": 900.0, "platform": "Amazon"},
        {"date": "2024-01-04", "book_title": "Book A", "units_sold": 110, "revenue": 1100.0, "platform": "Amazon"},
        {"date": "2024-01-05", "book_title": "Book A", "units_sold": 130, "revenue": 1300.0, "platform": "Amazon"},
        {"date": "2024-01-01", "book_title": "Book B", "units_sold": 80, "revenue": 800.0, "platform": "Amazon"},
        {"date": "2024-01-02", "book_title": "Book B", "units_sold": 85, "revenue": 850.0, "platform": "Amazon"},
        {"date": "2024-01-03", "book_title": "Book B", "units_sold": 90, "revenue": 900.0, "platform": "Amazon"},
        {"date": "2024-01-04", "book_title": "Book B", "units_sold": 88, "revenue": 880.0, "platform": "Amazon"},
        {"date": "2024-01-05", "book_title": "Book B", "units_sold": 92, "revenue": 920.0, "platform": "Amazon"},
    ]
    db.insert_records("sales_data", sales)

    # Insert sample demographics data
    demographics = [
        {"age_group": "18-24", "gender": "F", "country": "US", "rating": 4.5, "review_count": 50},
        {"age_group": "25-34", "gender": "M", "country": "US", "rating": 4.0, "review_count": 75},
        {"age_group": "35-44", "gender": "F", "country": "UK", "rating": 3.5, "review_count": 30},
        {"age_group": "45-54", "gender": "M", "country": "CA", "rating": 4.2, "review_count": 40},
        {"age_group": "55+", "gender": "F", "country": "US", "rating": 3.8, "review_count": 25},
    ]
    db.insert_records("demographics_data", demographics)

    # Insert sample content metrics
    content = [
        {"chapter": 1, "word_count": 3000, "read_through_rate": 0.95, "completion_rate": 0.90},
        {"chapter": 2, "word_count": 3500, "read_through_rate": 0.90, "completion_rate": 0.85},
        {"chapter": 3, "word_count": 2800, "read_through_rate": 0.85, "completion_rate": 0.80},
        {"chapter": 4, "word_count": 4000, "read_through_rate": 0.80, "completion_rate": 0.75},
        {"chapter": 5, "word_count": 3200, "read_through_rate": 0.88, "completion_rate": 0.82},
    ]
    db.insert_records("content_metrics", content)

    yield db

    db.close()
    os.unlink(path)


@pytest.fixture
def sample_csv():
    """Create a temporary CSV file with sample data."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "book_title", "units_sold", "revenue", "platform"])
        writer.writerow(["2024-01-01", "Test Book", 50, 500.0, "Amazon"])
        writer.writerow(["2024-01-02", "Test Book", 60, 600.0, "Amazon"])
    yield path
    os.unlink(path)


# ── Database tests ──────────────────────────────────────────────────

class TestDatabase:
    def test_get_sales_summary(self, tmp_db):
        summary = tmp_db.get_sales_summary()
        assert summary is not None
        assert summary["record_count"] == 10
        assert summary["total_units"] == 985
        assert summary["total_revenue"] == 9850.0
        assert "platform_breakdown" in summary

    def test_get_demographics_summary(self, tmp_db):
        summary = tmp_db.get_demographics_summary()
        assert summary is not None
        assert summary["total_records"] == 5
        assert "age_breakdown" in summary
        assert "gender_breakdown" in summary
        assert "country_breakdown" in summary

    def test_get_content_metrics_summary(self, tmp_db):
        summary = tmp_db.get_content_metrics_summary()
        assert summary is not None
        assert summary["total_chapters"] == 5
        assert summary["total_words"] == 16500
        assert "chapter_details" in summary

    def test_get_unique_books(self, tmp_db):
        books = tmp_db.get_unique_books()
        assert set(books) == {"Book A", "Book B"}

    def test_get_book_sales_series(self, tmp_db):
        series = tmp_db.get_book_sales_series("Book A")
        assert len(series) == 5
        assert series[0]["date"] == "2024-01-01"
        assert series[0]["units_sold"] == 100

    def test_get_book_ranking(self, tmp_db):
        ranked = tmp_db.get_book_ranking("revenue")
        assert len(ranked) == 2
        assert ranked[0]["book_title"] == "Book A"
        assert ranked[0]["revenue"] == 5500.0

    def test_get_book_ranking_invalid_metric(self, tmp_db):
        with pytest.raises(ValueError):
            tmp_db.get_book_ranking("invalid")

    def test_get_book_engagement(self, tmp_db):
        # demographics_data doesn't have book_title, so returns empty
        engagement = tmp_db.get_book_engagement()
        assert engagement == []

    def test_insert_empty_records(self, tmp_db):
        count = tmp_db.insert_records("sales_data", [])
        assert count == 0

    def test_insert_invalid_data_type(self, tmp_db):
        with pytest.raises(ValueError):
            tmp_db.insert_records("invalid_type", [{"a": 1}])


# ── CSV Ingestor tests ──────────────────────────────────────────────

class TestCSVIngestor:
    def test_detect_sales(self, sample_csv):
        data_type, records = detect_and_parse(sample_csv)
        assert data_type == "sales_data"
        assert len(records) == 2
        assert records[0]["book_title"] == "Test Book"

    def test_detect_demographics(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["age_group", "gender", "country", "rating", "review_count"])
            writer.writerow(["18-24", "F", "US", 4.5, 50])
        data_type, records = detect_and_parse(path)
        assert data_type == "demographics_data"
        assert len(records) == 1
        os.unlink(path)

    def test_detect_content_metrics(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["chapter", "word_count", "read_through_rate", "completion_rate"])
            writer.writerow([1, 3000, 0.95, 0.90])
        data_type, records = detect_and_parse(path)
        assert data_type == "content_metrics"
        assert len(records) == 1
        os.unlink(path)

    def test_detect_unknown_type(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["col_a", "col_b"])
            writer.writerow([1, 2])
        with pytest.raises(ValueError):
            detect_and_parse(path)
        os.unlink(path)


# ── Analytics tests ─────────────────────────────────────────────────

class TestTrendAnalyzer:
    def test_analyze_book(self, tmp_db):
        analyzer = TrendAnalyzer(tmp_db)
        trends = analyzer.analyze_book("Book A", window=3)
        assert trends["book_title"] == "Book A"
        assert "daily_sales" in trends
        assert "rolling_avg" in trends
        assert "spikes" in trends
        assert "drops" in trends

    def test_analyze_all_books(self, tmp_db):
        analyzer = TrendAnalyzer(tmp_db)
        trends = analyzer.analyze_all_books(window=3)
        assert len(trends) == 2
        titles = {t["book_title"] for t in trends}
        assert titles == {"Book A", "Book B"}


class TestBookComparator:
    def test_get_book_rankings_revenue(self, tmp_db):
        comparator = BookComparator(tmp_db)
        ranked = comparator.get_book_rankings("revenue")
        assert len(ranked) == 2
        assert ranked[0]["book_title"] == "Book A"

    def test_get_book_rankings_units(self, tmp_db):
        comparator = BookComparator(tmp_db)
        ranked = comparator.get_book_rankings("units_sold")
        assert len(ranked) == 2
        assert ranked[0]["book_title"] == "Book A"

    def test_compare_books(self, tmp_db):
        comparator = BookComparator(tmp_db)
        comparison = comparator.compare_books(("Book A", "Book B"))
        assert "Book A" in comparison
        assert "Book B" in comparison
        assert "Revenue" in comparison


class TestReportGenerator:
    def test_export_csv(self, tmp_db):
        generator = ReportGenerator(tmp_db)
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        generator.export_csv(path, "sales")
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
            assert "date" in content
            assert "book_title" in content
        os.unlink(path)

    def test_export_demographics(self, tmp_db):
        generator = ReportGenerator(tmp_db)
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        generator.export_csv(path, "demographics")
        assert os.path.exists(path)
        os.unlink(path)

    def test_export_content_metrics(self, tmp_db):
        generator = ReportGenerator(tmp_db)
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        generator.export_csv(path, "content_metrics")
        assert os.path.exists(path)
        os.unlink(path)


class TestRunFullAnalysis:
    def test_run_full_analysis(self, tmp_db):
        report = run_full_analysis(tmp_db)
        assert isinstance(report, str)
        assert "Trend Analysis" in report
        assert "Book Rankings" in report
        assert "Demographics" in report
        assert "Content Metrics" in report


# ── CLI tests ───────────────────────────────────────────────────────

class TestCLI:
    def test_import_data_command(self, sample_csv):
        from click.testing import CliRunner
        from manuscriptdata_analyzer.cli import cli

        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            runner = CliRunner()
            result = runner.invoke(cli, ["import-data", sample_csv, "--db", db_path])
            assert result.exit_code == 0
            assert "Imported" in result.output
        finally:
            os.unlink(db_path)

    def test_summary_command(self, tmp_db):
        from click.testing import CliRunner
        from manuscriptdata_analyzer.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["summary", "--db", tmp_db.db_path])
        assert result.exit_code == 0
        assert "ManuscriptData Analyzer" in result.output
        assert "Sales Data" in result.output
        assert "Demographics Data" in result.output
        assert "Content Metrics" in result.output

    def test_analyze_command(self, tmp_db):
        from click.testing import CliRunner
        from manuscriptdata_analyzer.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--db", tmp_db.db_path])
        assert result.exit_code == 0
        assert "Trend Analysis" in result.output

    def test_rankings_command(self, tmp_db):
        from click.testing import CliRunner
        from manuscriptdata_analyzer.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["rankings", "--db", tmp_db.db_path])
        assert result.exit_code == 0
        assert "Book A" in result.output

    def test_compare_command(self, tmp_db):
        from click.testing import CliRunner
        from manuscriptdata_analyzer.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["compare", "--db", tmp_db.db_path])
        assert result.exit_code == 0
        assert "Book A" in result.output

    def test_export_command(self, tmp_db):
        from click.testing import CliRunner
        from manuscriptdata_analyzer.cli import cli

        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        try:
            runner = CliRunner()
            result = runner.invoke(cli, ["export", path, "--db", tmp_db.db_path])
            assert result.exit_code == 0
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_trends_command(self, tmp_db):
        from click.testing import CliRunner
        from manuscriptdata_analyzer.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["trends", "--db", tmp_db.db_path])
        assert result.exit_code == 0
        assert "Book A" in result.output
