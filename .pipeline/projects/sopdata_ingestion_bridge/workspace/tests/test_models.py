"""Tests for SOPInputRow model (models.py)."""

import pytest
from sopdata_ingestion_bridge.models import SOPInputRow


# ── Fixtures ─────────────────────────────────────────────────────────────

SAMPLE_DATA = {
    "task_name": "Setup CI",
    "description": "Configure CI pipeline",
    "steps": "1. Create workflow\n2. Push",
    "assignee": "DevOps",
    "deadline": "2025-01-15",
    "priority": "high",
}

SAMPLE_DATA_WITH_ALIASES = {
    "title": "Setup CI",
    "desc": "Configure CI pipeline",
    "step": "1. Create workflow\n2. Push",
    "assigned_to": "DevOps",
    "due_date": "2025-01-15",
    "level": "high",
}

SAMPLE_DATA_WITH_MISSING_COLUMNS = {
    "task_name": "Setup CI",
    # description, steps, assignee, deadline, priority are all missing
}


class TestSOPInputRowFromDict:
    def test_from_dict_with_default_mapping(self):
        row = SOPInputRow.from_dict(SAMPLE_DATA)
        assert row.task_name == "Setup CI"
        assert row.description == "Configure CI pipeline"
        assert row.steps == "1. Create workflow\n2. Push"
        assert row.assignee == "DevOps"
        assert row.deadline == "2025-01-15"
        assert row.priority == "high"
        assert row.raw == SAMPLE_DATA

    def test_from_dict_with_alias_mapping(self):
        row = SOPInputRow.from_dict(SAMPLE_DATA_WITH_ALIASES)
        assert row.task_name == "Setup CI"
        assert row.description == "Configure CI pipeline"
        assert row.steps == "1. Create workflow\n2. Push"
        assert row.assignee == "DevOps"
        assert row.deadline == "2025-01-15"
        assert row.priority == "high"

    def test_from_dict_with_custom_mapping(self):
        custom = {"task_name": "task_name", "description": "description"}
        row = SOPInputRow.from_dict(SAMPLE_DATA, mapping=custom)
        assert row.task_name == "Setup CI"
        assert row.description == "Configure CI pipeline"
        # Other fields should be empty since they're not in the custom mapping
        assert row.steps == ""
        assert row.assignee == ""
        assert row.deadline == ""
        assert row.priority == ""

    def test_from_dict_with_missing_columns(self):
        row = SOPInputRow.from_dict(SAMPLE_DATA_WITH_MISSING_COLUMNS)
        assert row.task_name == "Setup CI"
        assert row.description == ""
        assert row.steps == ""
        assert row.assignee == ""
        assert row.deadline == ""
        assert row.priority == ""

    def test_from_dict_with_empty_data(self):
        row = SOPInputRow.from_dict({})
        assert row.task_name == ""
        assert row.description == ""
        assert row.steps == ""
        assert row.assignee == ""
        assert row.deadline == ""
        assert row.priority == ""

    def test_from_dict_with_none_mapping_uses_default(self):
        row = SOPInputRow.from_dict(SAMPLE_DATA, mapping=None)
        assert row.task_name == "Setup CI"
        assert row.priority == "high"


class TestSOPInputRowToDict:
    def test_to_dict_round_trip(self):
        row = SOPInputRow.from_dict(SAMPLE_DATA)
        d = row.to_dict()
        assert d["task_name"] == "Setup CI"
        assert d["description"] == "Configure CI pipeline"
        assert d["steps"] == "1. Create workflow\n2. Push"
        assert d["assignee"] == "DevOps"
        assert d["deadline"] == "2025-01-15"
        assert d["priority"] == "high"

    def test_to_dict_excludes_raw(self):
        row = SOPInputRow.from_dict(SAMPLE_DATA)
        d = row.to_dict()
        assert "raw" not in d

    def test_to_dict_with_empty_row(self):
        row = SOPInputRow()
        d = row.to_dict()
        assert d == {
            "task_name": "",
            "description": "",
            "steps": "",
            "assignee": "",
            "deadline": "",
            "priority": "",
        }

    def test_to_dict_round_trip_preserves_data(self):
        row = SOPInputRow.from_dict(SAMPLE_DATA)
        d = row.to_dict()
        row2 = SOPInputRow.from_dict(d)
        assert row2.task_name == row.task_name
        assert row2.description == row.description
        assert row2.steps == row.steps
        assert row2.assignee == row.assignee
        assert row2.deadline == row.deadline
        assert row2.priority == row.priority


class TestSOPInputRowDefaults:
    def test_default_values(self):
        row = SOPInputRow()
        assert row.task_name == ""
        assert row.description == ""
        assert row.steps == ""
        assert row.assignee == ""
        assert row.deadline == ""
        assert row.priority == ""
        assert row.raw == {}
