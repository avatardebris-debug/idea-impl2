"""Tests for the CSV parser module."""

import os
import pytest
from manuscriptdata_analyzer.csv_parser import (
    detect_data_type,
    parse_csv,
    detect_and_parse,
    _normalise_header,
    _normalise_value,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


# ── Auto-detection ───────────────────────────────────────────────

class TestDetectDataType:
    def test_detect_sales(self):
        headers = ["Date", "Book Title", "Units Sold", "Revenue", "Platform"]
        assert detect_data_type(headers) == "sales_data"

    def test_detect_demographics(self):
        headers = ["Age Group", "Gender", "Country", "Rating", "Review Count"]
        assert detect_data_type(headers) == "demographics_data"

    def test_detect_content_metrics(self):
        headers = ["Chapter", "Word Count", "Read-Through Rate", "Completion Rate"]
        assert detect_data_type(headers) == "content_metrics"

    def test_detect_unrecognised(self):
        headers = ["Name", "Age", "City"]
        with pytest.raises(ValueError, match="Unrecognised CSV format"):
            detect_data_type(headers)


# ── Normalisation helpers ──────────────────────────────────────

class TestNormaliseValue:
    def test_string(self):
        assert _normalise_value("book_title", "The Great Adventure") == "The Great Adventure"

    def test_integer(self):
        assert _normalise_value("units_sold", "150") == 150

    def test_float_revenue(self):
        assert _normalise_value("revenue", "$1,499.99") == 1499.99

    def test_float_rating(self):
        assert _normalise_value("rating", "4.5") == 4.5

    def test_empty_string(self):
        assert _normalise_value("units_sold", "") is None


# ── Full CSV parsing ─────────────────────────────────────────

class TestParseCSV:
    def test_parse_sales(self):
        data_type, records = parse_csv(os.path.join(FIXTURES_DIR, "sales.csv"))
        assert data_type == "sales_data"
        assert len(records) == 15
        assert records[0]["book_title"] == "The Great Adventure"
        assert records[0]["units_sold"] == 150
        assert records[0]["revenue"] == 1499.99
        assert records[0]["platform"] == "Amazon"

    def test_parse_demographics(self):
        data_type, records = parse_csv(os.path.join(FIXTURES_DIR, "demographics.csv"))
        assert data_type == "demographics_data"
        assert len(records) == 15
        assert records[0]["age_group"] == "18-24"
        assert records[0]["gender"] == "Male"
        assert records[0]["rating"] == 4.5
        assert records[0]["review_count"] == 120

    def test_parse_content_metrics(self):
        data_type, records = parse_csv(os.path.join(FIXTURES_DIR, "content_metrics.csv"))
        assert data_type == "content_metrics"
        assert len(records) == 15
        assert records[0]["chapter"] == 1
        assert records[0]["word_count"] == 3200
        assert records[0]["read_through_rate"] == 0.95
        assert records[0]["completion_rate"] == 0.92

    def test_detect_and_parse_alias(self):
        """detect_and_parse is a thin wrapper around parse_csv."""
        data_type, records = detect_and_parse(os.path.join(FIXTURES_DIR, "sales.csv"))
        assert data_type == "sales_data"
        assert len(records) == 15
