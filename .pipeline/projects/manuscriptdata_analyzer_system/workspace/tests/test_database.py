"""Tests for the database layer."""

import os
import tempfile
import pytest
from manuscriptdata_analyzer.database import Database


@pytest.fixture
def db():
    """Create a temporary database for each test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_obj = Database(path)
    db_obj.connect()
    yield db_obj
    db_obj.close()
    os.unlink(path)


class TestTableCreation:
    def test_tables_exist(self, db):
        """All three tables should be created on connect."""
        cur = db._conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {r[0] for r in cur.fetchall()}
        assert "sales_data" in tables
        assert "demographics_data" in tables
        assert "content_metrics" in tables

    def test_indexes_exist(self, db):
        """Indexes should be created on commonly queried columns."""
        cur = db._conn.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
        indexes = {r[0] for r in cur.fetchall()}
        assert "idx_sales_book" in indexes
        assert "idx_demo_age" in indexes
        assert "idx_content_chapter" in indexes


class TestInsertRecords:
    def test_insert_sales(self, db):
        records = [
            {"date": "2024-01-01", "book_title": "Book A", "units_sold": 100, "revenue": 999.99, "platform": "Amazon"},
            {"date": "2024-01-02", "book_title": "Book B", "units_sold": 200, "revenue": 1999.99, "platform": "Kindle"},
        ]
        count = db.insert_records("sales_data", records)
        assert count == 2
        cur = db._conn.execute("SELECT COUNT(*) FROM sales_data")
        assert cur.fetchone()[0] == 2

    def test_insert_demographics(self, db):
        records = [
            {"age_group": "18-24", "gender": "Male", "country": "US", "rating": 4.5, "review_count": 100},
        ]
        count = db.insert_records("demographics_data", records)
        assert count == 1

    def test_insert_content_metrics(self, db):
        records = [
            {"chapter": 1, "word_count": 3000, "read_through_rate": 0.95, "completion_rate": 0.90},
        ]
        count = db.insert_records("content_metrics", records)
        assert count == 1

    def test_insert_empty(self, db):
        count = db.insert_records("sales_data", [])
        assert count == 0

    def test_insert_unknown_type(self, db):
        with pytest.raises(ValueError, match="Unknown data_type"):
            db.insert_records("unknown_type", [])


class TestQuerySalesSummary:
    def test_sales_summary(self, db):
        db.insert_records("sales_data", [
            {"date": "2024-01-01", "book_title": "A", "units_sold": 100, "revenue": 1000.0, "platform": "X"},
            {"date": "2024-01-02", "book_title": "B", "units_sold": 200, "revenue": 2000.0, "platform": "Y"},
        ])
        summary = db.get_sales_summary()
        assert summary is not None
        assert summary["total_units"] == 300
        assert summary["total_revenue"] == 3000.0
        assert summary["avg_revenue"] == 1500.0
        assert summary["record_count"] == 2
        assert "X" in summary["platform_breakdown"]
        assert "Y" in summary["platform_breakdown"]

    def test_sales_summary_empty(self, db):
        assert db.get_sales_summary() is None


class TestQueryDemographicsSummary:
    def test_demo_summary(self, db):
        db.insert_records("demographics_data", [
            {"age_group": "18-24", "gender": "Male", "country": "US", "rating": 4.0, "review_count": 100},
            {"age_group": "25-34", "gender": "Female", "country": "UK", "rating": 4.5, "review_count": 200},
        ])
        summary = db.get_demographics_summary()
        assert summary is not None
        assert summary["total_records"] == 2
        assert "18-24" in summary["age_breakdown"]
        assert "Male" in summary["gender_breakdown"]
        assert "US" in summary["country_breakdown"]

    def test_demo_summary_empty(self, db):
        assert db.get_demographics_summary() is None


class TestQueryContentMetricsSummary:
    def test_content_summary(self, db):
        db.insert_records("content_metrics", [
            {"chapter": 1, "word_count": 3000, "read_through_rate": 0.95, "completion_rate": 0.90},
            {"chapter": 2, "word_count": 4000, "read_through_rate": 0.85, "completion_rate": 0.80},
        ])
        summary = db.get_content_metrics_summary()
        assert summary is not None
        assert summary["total_chapters"] == 2
        assert summary["total_words"] == 7000
        assert summary["avg_words"] == 3500.0
        assert len(summary["chapter_details"]) == 2

    def test_content_summary_empty(self, db):
        assert db.get_content_metrics_summary() is None
