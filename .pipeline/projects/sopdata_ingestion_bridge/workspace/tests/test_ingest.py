"""Tests for CSV ingestion module (ingest.py)."""

import os
import tempfile
import pytest
from sopdata_ingestion_bridge.ingest import read_csv, read_csv_from_string


# ── Fixtures ────────────────────────────────────────────────────────────────

VALID_CSV = """\
name,description,steps,assignee,deadline,priority
Task A,Description A,Step 1; Step 2,Alice,2025-01-01,high
Task B,Description B,Step 3; Step 4,Bob,2025-02-01,low
"""

VALID_CSV_WITH_BOM = "\ufeffname,description,steps,assignee,deadline,priority\nTask A,Desc A,Step 1,Alice,2025-01-01,high\n"

EMPTY_CSV = ""

NO_HEADERS_CSV = "\n\n\n"  # only blank lines


# ── read_csv with file path ─────────────────────────────────────────────────

class TestReadCsvFilePath:
    def test_valid_csv_returns_correct_rows(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(VALID_CSV)
            f.flush()
            path = f.name
        try:
            rows = read_csv(path)
            assert len(rows) == 2
            assert rows[0]["name"] == "Task A"
            assert rows[0]["description"] == "Description A"
            assert rows[1]["name"] == "Task B"
            assert rows[1]["priority"] == "low"
        finally:
            os.unlink(path)

    def test_missing_file_raises_file_not_found_error(self):
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            read_csv("/nonexistent/path/to/file.csv")

    def test_empty_csv_raises_value_error(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(EMPTY_CSV)
            f.flush()
            path = f.name
        try:
            with pytest.raises(ValueError, match="CSV file is empty"):
                read_csv(path)
        finally:
            os.unlink(path)

    def test_no_headers_raises_value_error(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(NO_HEADERS_CSV)
            f.flush()
            path = f.name
        try:
            with pytest.raises(ValueError, match="CSV file has no valid headers"):
                read_csv(path)
        finally:
            os.unlink(path)

    def test_custom_encoding(self):
        csv_latin1 = "name,description\nTâche,Description"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="latin-1") as f:
            f.write(csv_latin1)
            f.flush()
            path = f.name
        try:
            rows = read_csv(path, encoding="latin-1")
            assert len(rows) == 1
            assert rows[0]["name"] == "Tâche"
        finally:
            os.unlink(path)

    def test_utf8_bom_handling(self):
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(VALID_CSV_WITH_BOM.encode("utf-8"))
            f.flush()
            path = f.name
        try:
            rows = read_csv(path)
            assert len(rows) == 1
            assert rows[0]["name"] == "Task A"
        finally:
            os.unlink(path)


# ── read_csv_from_string ────────────────────────────────────────────────────

class TestReadCsvFromString:
    def test_valid_csv_text(self):
        rows = read_csv_from_string(VALID_CSV)
        assert len(rows) == 2
        assert rows[0]["name"] == "Task A"
        assert rows[1]["name"] == "Task B"

    def test_single_row(self):
        csv_text = "col_a,col_b\nval1,val2\n"
        rows = read_csv_from_string(csv_text)
        assert len(rows) == 1
        assert rows[0]["col_a"] == "val1"
        assert rows[0]["col_b"] == "val2"

    def test_empty_csv_text_raises_value_error(self):
        with pytest.raises(ValueError, match="CSV file is empty"):
            read_csv_from_string("")

    def test_no_headers_csv_text_raises_value_error(self):
        with pytest.raises(ValueError, match="CSV file has no valid headers"):
            read_csv_from_string("\n\n")

    def test_headers_only_no_data_rows(self):
        csv_text = "a,b,c\n"
        rows = read_csv_from_string(csv_text)
        assert len(rows) == 0
