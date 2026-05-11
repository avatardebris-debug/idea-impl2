"""Tests for bridge API (bridge.py) — integration tests."""

import os
import tempfile
import pytest
from sopdata_ingestion_bridge.bridge import SOPBridge, ingest
from sopdata_ingestion_bridge.models import SOPInputRow


# ── Fixtures ─────────────────────────────────────────────────────────────

VALID_CSV = """\
task_name,description,steps,assignee,deadline,priority
Task A,Description A,Step 1; Step 2,Alice,2025-01-01,high
Task B,Description B,Step 3; Step 4,Bob,2025-02-01,low
"""

CUSTOM_MAPPING_CSV = """\
title,desc,step,assigned_to,due_date,level
Task C,Description C,Step 5; Step 6,Charlie,2025-03-01,medium
"""

SAMPLE_DATA_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sample_data.csv",
)


def _write_temp_csv(content: str) -> str:
    """Write CSV content to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
    f.write(content)
    f.flush()
    path = f.name
    f.close()
    return path


class TestSOPBridgeIngest:
    def test_ingest_returns_sopinputrow_list(self):
        path = _write_temp_csv(VALID_CSV)
        try:
            bridge = SOPBridge()
            result = bridge.ingest(path)
            assert isinstance(result, list)
            assert all(isinstance(r, SOPInputRow) for r in result)
            assert len(result) == 2
        finally:
            os.unlink(path)

    def test_ingest_valid_csv_correct_data(self):
        path = _write_temp_csv(VALID_CSV)
        try:
            bridge = SOPBridge()
            result = bridge.ingest(path)
            assert result[0].task_name == "Task A"
            assert result[0].description == "Description A"
            assert result[0].priority == "high"
            assert result[1].task_name == "Task B"
            assert result[1].priority == "low"
        finally:
            os.unlink(path)

    def test_ingest_with_custom_mapping(self):
        path = _write_temp_csv(CUSTOM_MAPPING_CSV)
        try:
            custom = {
                "title": "task_name",
                "desc": "description",
                "step": "steps",
                "assigned_to": "assignee",
                "due_date": "deadline",
                "level": "priority",
            }
            bridge = SOPBridge()
            result = bridge.ingest(path, mapping=custom)
            assert len(result) == 1
            assert result[0].task_name == "Task C"
            assert result[0].description == "Description C"
            assert result[0].assignee == "Charlie"
            assert result[0].deadline == "2025-03-01"
            assert result[0].priority == "medium"
        finally:
            os.unlink(path)

    def test_ingest_missing_file_raises_file_not_found_error(self):
        bridge = SOPBridge()
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            bridge.ingest("/nonexistent/file.csv")

    def test_ingest_empty_csv_raises_value_error(self):
        path = _write_temp_csv("")
        try:
            bridge = SOPBridge()
            with pytest.raises(ValueError, match="CSV file is empty"):
                bridge.ingest(path)
        finally:
            os.unlink(path)

    def test_ingest_with_sample_data_csv(self):
        """Test using the actual sample_data.csv in the workspace."""
        if not os.path.exists(SAMPLE_DATA_CSV_PATH):
            pytest.skip("sample_data.csv not found")
        bridge = SOPBridge()
        result = bridge.ingest(SAMPLE_DATA_CSV_PATH)
        assert len(result) == 3
        assert all(isinstance(r, SOPInputRow) for r in result)
        assert result[0].task_name == "Set up CI pipeline"
        assert result[2].task_name == "Code review process"


class TestIngestConvenienceFunction:
    def test_ingest_function_works_identically_to_bridge(self):
        path = _write_temp_csv(VALID_CSV)
        try:
            result_func = ingest(path)
            result_bridge = SOPBridge().ingest(path)
            assert len(result_func) == len(result_bridge)
            assert result_func[0].task_name == result_bridge[0].task_name
            assert result_func[0].description == result_bridge[0].description
            assert result_func[1].task_name == result_bridge[1].task_name
        finally:
            os.unlink(path)

    def test_ingest_function_with_custom_mapping(self):
        path = _write_temp_csv(CUSTOM_MAPPING_CSV)
        try:
            custom = {
                "title": "task_name",
                "desc": "description",
                "step": "steps",
                "assigned_to": "assignee",
                "due_date": "deadline",
                "level": "priority",
            }
            result = ingest(path, mapping=custom)
            assert len(result) == 1
            assert result[0].task_name == "Task C"
        finally:
            os.unlink(path)

    def test_ingest_function_propagates_errors(self):
        with pytest.raises(FileNotFoundError):
            ingest("/nonexistent/file.csv")
