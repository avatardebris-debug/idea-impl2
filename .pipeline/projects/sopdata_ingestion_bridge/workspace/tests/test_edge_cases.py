"""Tests for edge cases across all modules."""

import os
import tempfile
import pytest
from sopdata_ingestion_bridge.ingest import read_csv, read_csv_from_string
from sopdata_ingestion_bridge.transform import transform
from sopdata_ingestion_bridge.models import SOPInputRow


# ── Fixtures ─────────────────────────────────────────────────────────────

CSV_WITH_BLANK_ROWS = """\
task_name,description,steps,assignee,deadline,priority
Task A,Desc A,Step 1,Alice,2025-01-01,high

Task B,Desc B,Step 2,Bob,2025-02-01,low

"""

CSV_WITH_EXTRA_COLUMNS = """\
task_name,description,steps,assignee,deadline,priority,extra_col,another_col
Task A,Desc A,Step 1,Alice,2025-01-01,high,extra_val,another_val
"""

CSV_WITH_FEWER_COLUMNS = """\
task_name,description,steps,assignee,deadline,priority
Task A,Desc A,Step 1
"""

CSV_WITH_SPECIAL_CHARACTERS = (
    'task_name,description,steps,assignee,deadline,priority\n'
    '"Task ""A""","Desc with ""quotes""",Step 1; Step 2,Alice,2025-01-01,high\n'
    '"Task B","Desc with,commas",Charlie,2025-02-01,low\n'
    '"Task C","Desc with\nnewlines",Step 3,DevOps,2025-03-01,medium\n'
)

CSV_WITH_UNICODE = """\
task_name,description,steps,assignee,deadline,priority
任务A,描述A,步骤1,张三,2025-01-01,高
Tâche,Description,Étape,Marie,2025-02-01,élevé
"""


class TestEdgeCasesIngest:
    def test_csv_with_blank_rows_skips_blanks(self):
        rows = read_csv_from_string(CSV_WITH_BLANK_ROWS)
        assert len(rows) == 2
        assert rows[0]["task_name"] == "Task A"
        assert rows[1]["task_name"] == "Task B"

    def test_csv_with_extra_columns_ignores_extra(self):
        rows = read_csv_from_string(CSV_WITH_EXTRA_COLUMNS)
        assert len(rows) == 1
        assert rows[0]["task_name"] == "Task A"
        assert rows[0]["priority"] == "high"

    def test_csv_with_fewer_columns_produces_empty_strings(self):
        rows = read_csv_from_string(CSV_WITH_FEWER_COLUMNS)
        assert len(rows) == 1
        assert rows[0]["task_name"] == "Task A"
        assert rows[0]["description"] == "Desc A"
        assert rows[0]["steps"] == "Step 1"
        assert rows[0]["assignee"] == ""
        assert rows[0]["deadline"] == ""
        assert rows[0]["priority"] == ""

    def test_csv_with_special_characters_preserved(self):
        rows = read_csv_from_string(CSV_WITH_SPECIAL_CHARACTERS)
        assert len(rows) == 3
        assert rows[0]["task_name"] == 'Task "A"'
        assert rows[0]["description"] == 'Desc with "quotes"'
        assert rows[1]["task_name"] == "Task B"
        assert rows[1]["description"] == "Desc with,commas"
        assert rows[2]["task_name"] == "Task C"
        assert "newlines" in rows[2]["description"]

    def test_csv_with_unicode_preserved(self):
        rows = read_csv_from_string(CSV_WITH_UNICODE)
        assert len(rows) == 2
        assert rows[0]["task_name"] == "任务A"
        assert rows[0]["assignee"] == "张三"
        assert rows[1]["task_name"] == "Tâche"
        assert rows[1]["assignee"] == "Marie"


class TestEdgeCasesTransform:
    def test_transform_with_empty_mapping_dict(self):
        rows = [{"task_name": "Task A", "description": "Desc A"}]
        result = transform(rows, mapping={})
        assert len(result) == 1
        assert result[0].task_name == ""
        assert result[0].description == ""
        assert result[0].steps == ""
        assert result[0].assignee == ""
        assert result[0].deadline == ""
        assert result[0].priority == ""

    def test_transform_with_blank_rows_in_input(self):
        rows = [{"task_name": "Task A"}, {}, {"task_name": "Task B"}]
        result = transform(rows)
        assert len(result) == 3
        assert result[0].task_name == "Task A"
        assert result[1].task_name == ""
        assert result[2].task_name == "Task B"

    def test_transform_with_special_characters_in_data(self):
        rows = [{"task_name": 'Task "A"', "description": "Desc with,commas"}]
        result = transform(rows)
        assert len(result) == 1
        assert result[0].task_name == 'Task "A"'
        assert result[0].description == "Desc with,commas"

    def test_transform_with_unicode_data(self):
        rows = [{"task_name": "任务A", "description": "描述A"}]
        result = transform(rows)
        assert len(result) == 1
        assert result[0].task_name == "任务A"
        assert result[0].description == "描述A"


class TestEdgeCasesModels:
    def test_sopinputrow_from_dict_with_special_chars(self):
        data = {"task_name": 'Task "A"', "description": "Desc with,commas"}
        row = SOPInputRow.from_dict(data)
        assert row.task_name == 'Task "A"'
        assert row.description == "Desc with,commas"

    def test_sopinputrow_to_dict_with_special_chars(self):
        row = SOPInputRow(task_name='Task "A"', description="Desc with,commas")
        d = row.to_dict()
        assert d["task_name"] == 'Task "A"'
        assert d["description"] == "Desc with,commas"

    def test_sopinputrow_from_dict_with_unicode(self):
        data = {"task_name": "任务A", "description": "描述A"}
        row = SOPInputRow.from_dict(data)
        assert row.task_name == "任务A"
        assert row.description == "描述A"
