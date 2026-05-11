"""Tests for transformation module (transform.py)."""

import pytest
from sopdata_ingestion_bridge.transform import transform, DEFAULT_MAPPING
from sopdata_ingestion_bridge.models import SOPInputRow


# ── Fixtures ─────────────────────────────────────────────────────────────

SAMPLE_ROWS = [
    {
        "task_name": "Task A",
        "description": "Desc A",
        "steps": "Step 1",
        "assignee": "Alice",
        "deadline": "2025-01-01",
        "priority": "high",
    },
    {
        "task_name": "Task B",
        "description": "Desc B",
        "steps": "Step 2",
        "assignee": "Bob",
        "deadline": "2025-02-01",
        "priority": "low",
    },
]

SAMPLE_ROWS_WITH_ALIASES = [
    {
        "title": "Task A",
        "desc": "Desc A",
        "step": "Step 1",
        "assigned_to": "Alice",
        "due_date": "2025-01-01",
        "level": "high",
    },
]

EMPTY_ROWS = []


class TestTransformDefaultMapping:
    def test_transform_returns_list_of_sopinputrow(self):
        result = transform(SAMPLE_ROWS)
        assert isinstance(result, list)
        assert all(isinstance(r, SOPInputRow) for r in result)

    def test_transform_with_default_mapping_maps_correctly(self):
        result = transform(SAMPLE_ROWS)
        assert len(result) == 2
        assert result[0].task_name == "Task A"
        assert result[0].description == "Desc A"
        assert result[0].steps == "Step 1"
        assert result[0].assignee == "Alice"
        assert result[0].deadline == "2025-01-01"
        assert result[0].priority == "high"

    def test_transform_with_alias_mapping(self):
        result = transform(SAMPLE_ROWS_WITH_ALIASES)
        assert len(result) == 1
        assert result[0].task_name == "Task A"
        assert result[0].description == "Desc A"
        assert result[0].steps == "Step 1"
        assert result[0].assignee == "Alice"
        assert result[0].deadline == "2025-01-01"
        assert result[0].priority == "high"

    def test_transform_with_custom_mapping(self):
        custom = {
            "title": "task_name",
            "desc": "description",
            "step": "steps",
            "assigned_to": "assignee",
            "due_date": "deadline",
            "level": "priority",
        }
        result = transform(SAMPLE_ROWS_WITH_ALIASES, mapping=custom)
        assert len(result) == 1
        assert result[0].task_name == "Task A"
        assert result[0].description == "Desc A"
        assert result[0].steps == "Step 1"
        assert result[0].assignee == "Alice"
        assert result[0].deadline == "2025-01-01"
        assert result[0].priority == "high"

    def test_transform_with_missing_columns_produces_empty_strings(self):
        partial_rows = [{"task_name": "Task A"}]
        result = transform(partial_rows)
        assert len(result) == 1
        assert result[0].task_name == "Task A"
        assert result[0].description == ""
        assert result[0].steps == ""
        assert result[0].assignee == ""
        assert result[0].deadline == ""
        assert result[0].priority == ""

    def test_transform_with_empty_input_returns_empty_list(self):
        result = transform(EMPTY_ROWS)
        assert result == []

    def test_transform_with_none_mapping_uses_default(self):
        result = transform(SAMPLE_ROWS, mapping=None)
        assert len(result) == 2
        assert result[0].task_name == "Task A"

    def test_transform_preserves_raw_data(self):
        result = transform(SAMPLE_ROWS)
        assert result[0].raw == SAMPLE_ROWS[0]
        assert result[1].raw == SAMPLE_ROWS[1]


class TestDefaultMapping:
    def test_default_mapping_contains_expected_keys(self):
        assert "task_name" in DEFAULT_MAPPING
        assert "description" in DEFAULT_MAPPING
        assert "steps" in DEFAULT_MAPPING
        assert "assignee" in DEFAULT_MAPPING
        assert "deadline" in DEFAULT_MAPPING
        assert "priority" in DEFAULT_MAPPING

    def test_default_mapping_contains_aliases(self):
        assert "title" in DEFAULT_MAPPING
        assert "desc" in DEFAULT_MAPPING
        assert "step" in DEFAULT_MAPPING
        assert "assigned_to" in DEFAULT_MAPPING
        assert "due_date" in DEFAULT_MAPPING
        assert "level" in DEFAULT_MAPPING
