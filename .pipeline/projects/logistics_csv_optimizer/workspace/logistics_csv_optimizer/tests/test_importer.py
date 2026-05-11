"""Unit tests for the Importer module.

Tests CSV manifest loading, validation, and edge cases:
- Valid CSV loading
- Missing columns
- Empty files
- Invalid weight values
- Invalid priorities
- Missing origin/destination
- File-not-found errors
"""

import csv
import os
import tempfile
import pytest
from logistics_csv_optimizer.importer import Importer, REQUIRED_COLUMNS, VALID_PRIORITIES


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _write_csv(tmp_path, header, rows):
    """Helper to write a CSV file and return its path."""
    path = os.path.join(str(tmp_path), "manifest.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
    return path


# ── Valid CSV loading ─────────────────────────────────────────────────────────

class TestValidCSVLoading:
    """Tests for successfully loading valid CSV manifests."""

    def test_load_single_shipment(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "150.0", "express"]])
        result = Importer.load_manifest(path)
        assert len(result) == 1
        assert result[0]["origin"] == "New York"
        assert result[0]["destination"] == "Chicago"
        assert result[0]["weight"] == 150.0
        assert result[0]["priority"] == "express"

    def test_load_multiple_shipments(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [
                ["A", "B", "10.0", "standard"],
                ["C", "D", "20.0", "overnight"],
                ["E", "F", "30.0", "express"],
            ])
        result = Importer.load_manifest(path)
        assert len(result) == 3

    def test_load_with_optional_columns(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority", "length", "width", "height", "description"],
            [["NYC", "LAX", "50.0", "standard", "100", "50", "30", "Test cargo"]])
        result = Importer.load_manifest(path)
        assert len(result) == 1
        assert result[0]["length"] == 100.0
        assert result[0]["width"] == 50.0
        assert result[0]["height"] == 30.0
        assert result[0]["description"] == "Test cargo"

    def test_load_with_defaults_for_missing_optional(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "50.0", "standard"]])
        result = Importer.load_manifest(path)
        assert result[0]["length"] == 0.0
        assert result[0]["width"] == 0.0
        assert result[0]["height"] == 0.0
        assert result[0]["description"] == ""

    def test_case_insensitive_columns(self, tmp_path):
        path = _write_csv(tmp_path,
            ["Origin", "DESTINATION", "Weight", "Priority"],
            [["NYC", "LAX", "50.0", "standard"]])
        result = Importer.load_manifest(path)
        assert len(result) == 1
        assert result[0]["origin"] == "NYC"
        assert result[0]["priority"] == "standard"

    def test_all_valid_priorities(self, tmp_path):
        for priority in VALID_PRIORITIES:
            path = _write_csv(tmp_path,
                ["origin", "destination", "weight", "priority"],
                [["A", "B", "10.0", priority]])
            result = Importer.load_manifest(path)
            assert len(result) == 1
            assert result[0]["priority"] == priority


# ── Missing columns ───────────────────────────────────────────────────────────

class TestMissingColumns:
    """Tests for handling missing required columns."""

    def test_missing_origin_column(self, tmp_path):
        path = _write_csv(tmp_path,
            ["destination", "weight", "priority"],
            [["Chicago", "150.0", "express"]])
        with pytest.raises(ValueError, match="Missing required columns.*origin"):
            Importer.load_manifest(path)

    def test_missing_destination_column(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "weight", "priority"],
            [["New York", "150.0", "express"]])
        with pytest.raises(ValueError, match="Missing required columns.*destination"):
            Importer.load_manifest(path)

    def test_missing_weight_column(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "priority"],
            [["New York", "Chicago", "express"]])
        with pytest.raises(ValueError, match="Missing required columns.*weight"):
            Importer.load_manifest(path)

    def test_missing_priority_column(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight"],
            [["New York", "Chicago", "150.0"]])
        with pytest.raises(ValueError, match="Missing required columns.*priority"):
            Importer.load_manifest(path)

    def test_missing_multiple_columns(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin"],
            [["New York"]])
        with pytest.raises(ValueError, match="Missing required columns"):
            Importer.load_manifest(path)


# ── Empty files ───────────────────────────────────────────────────────────────

class TestEmptyFiles:
    """Tests for handling empty or whitespace-only files."""

    def test_empty_file(self, tmp_path):
        path = os.path.join(str(tmp_path), "empty.csv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("")
        result = Importer.load_manifest(path)
        assert result == []

    def test_whitespace_only_file(self, tmp_path):
        path = os.path.join(str(tmp_path), "whitespace.csv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("   \n  \n  \n")
        result = Importer.load_manifest(path)
        assert result == []

    def test_header_only_file(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [])
        result = Importer.load_manifest(path)
        assert result == []


# ── Invalid weight values ─────────────────────────────────────────────────────

class TestInvalidWeight:
    """Tests for invalid weight values."""

    def test_non_numeric_weight(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "abc", "standard"]])
        with pytest.raises(ValueError, match="weight.*must be a number"):
            Importer.load_manifest(path)

    def test_negative_weight(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "-10.0", "standard"]])
        with pytest.raises(ValueError, match="weight.*must be positive"):
            Importer.load_manifest(path)

    def test_zero_weight(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "0", "standard"]])
        with pytest.raises(ValueError, match="weight.*must be positive"):
            Importer.load_manifest(path)

    def test_empty_weight_field(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "", "standard"]])
        with pytest.raises(ValueError, match="weight.*is empty"):
            Importer.load_manifest(path)


# ── Invalid priorities ────────────────────────────────────────────────────────

class TestInvalidPriority:
    """Tests for invalid priority values."""

    def test_invalid_priority_string(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "10.0", "superfast"]])
        with pytest.raises(ValueError, match="priority.*must be one of"):
            Importer.load_manifest(path)

    def test_empty_priority(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "10.0", ""]])
        with pytest.raises(ValueError, match="priority.*must be one of"):
            Importer.load_manifest(path)

    def test_uppercase_priority_normalized(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "10.0", "STANDARD"]])
        result = Importer.load_manifest(path)
        assert result[0]["priority"] == "standard"


# ── Missing origin/destination ─────────────────────────────────────────────────

class TestMissingOriginDestination:
    """Tests for missing origin or destination fields."""

    def test_empty_origin(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["", "LAX", "10.0", "standard"]])
        with pytest.raises(ValueError, match="origin.*is empty"):
            Importer.load_manifest(path)

    def test_empty_destination(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "", "10.0", "standard"]])
        with pytest.raises(ValueError, match="destination.*is empty"):
            Importer.load_manifest(path)

    def test_whitespace_origin(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["   ", "LAX", "10.0", "standard"]])
        with pytest.raises(ValueError, match="origin.*is empty"):
            Importer.load_manifest(path)

    def test_whitespace_destination(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "   ", "10.0", "standard"]])
        with pytest.raises(ValueError, match="destination.*is empty"):
            Importer.load_manifest(path)


# ── File-not-found errors ─────────────────────────────────────────────────────

class TestFileNotFound:
    """Tests for file-not-found errors."""

    def test_nonexistent_file(self):
        with pytest.raises(FileNotFoundError, match="Manifest file not found"):
            Importer.load_manifest("/nonexistent/path/to/manifest.csv")

    def test_nonexistent_file_with_spaces(self):
        with pytest.raises(FileNotFoundError):
            Importer.load_manifest("/tmp/does_not_exist_12345.csv")


# ── Row-level validation ──────────────────────────────────────────────────────

class TestRowValidation:
    """Tests for row-level validation (error messages include row numbers)."""

    def test_error_includes_row_number(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "abc", "standard"]])
        with pytest.raises(ValueError, match="Row 2.*weight.*must be a number"):
            Importer.load_manifest(path)

    def test_valid_float_weight(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "10.5", "standard"]])
        result = Importer.load_manifest(path)
        assert result[0]["weight"] == 10.5

    def test_integer_weight(self, tmp_path):
        path = _write_csv(tmp_path,
            ["origin", "destination", "weight", "priority"],
            [["NYC", "LAX", "10", "standard"]])
        result = Importer.load_manifest(path)
        assert result[0]["weight"] == 10.0
