"""Tests for Results Store and persistence."""

import pytest
import json
import tempfile
from pathlib import Path

from drop_servicing_tool.results_store import ResultsStore, _get_results_dir


class TestGetResultsDir:
    """Tests for _get_results_dir function."""

    def test_default_results_dir(self, monkeypatch):
        """Test default results directory when no env var."""
        monkeypatch.delenv("DST_BULK_BASE_DIR", raising=False)
        results_dir = _get_results_dir()
        assert isinstance(results_dir, Path)

    def test_env_var_results_dir(self, monkeypatch):
        """Test results directory from env var."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("DST_BULK_BASE_DIR", tmpdir)
            results_dir = _get_results_dir()
            assert str(results_dir) == tmpdir


class TestResultsStore:
    """Tests for ResultsStore class."""

    def test_store_result_creates_directory(self, tmp_path):
        """Test that storing a result creates the queue directory."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"})

        results_dir = tmp_path / "queue_1"
        assert results_dir.exists()
        assert (results_dir / "results.json").exists()

    def test_store_result_saves_data(self, tmp_path):
        """Test that result data is saved correctly."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result(
            "queue_1",
            "task_1",
            {"output": "done", "value": 42},
            tokens_used=100,
            duration_seconds=1.5,
            status="completed",
            error=None,
            metadata={"key": "value"},
        )

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert "task_1" in data
        result = data["task_1"]
        assert result["task_id"] == "task_1"
        assert result["result_data"] == {"output": "done", "value": 42}
        assert result["tokens_used"] == 100
        assert result["duration_seconds"] == 1.5
        assert result["status"] == "completed"
        assert result["error"] is None
        assert result["metadata"] == {"key": "value"}

    def test_store_result_updates_existing(self, tmp_path):
        """Test that storing another result updates the file."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "first"})
        store.store_result("queue_1", "task_2", {"output": "second"})

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert len(data) == 2
        assert "task_1" in data
        assert "task_2" in data

    def test_store_result_updates_summary(self, tmp_path):
        """Test that storing a result updates the summary."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, status="completed")
        store.store_result("queue_1", "task_2", {"output": "failed"}, status="failed")

        summary_file = tmp_path / "queue_1" / "summary.json"
        assert summary_file.exists()

        summary = json.loads(summary_file.read_text(encoding="utf-8"))
        assert summary["total_tasks"] == 2
        assert summary["completed_tasks"] == 1
        assert summary["failed_tasks"] == 1

    def test_get_result(self, tmp_path):
        """Test retrieving a single result."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"})

        result = store.get_result("queue_1", "task_1")
        assert result["task_id"] == "task_1"
        assert result["result_data"] == {"output": "done"}

    def test_get_result_not_found(self, tmp_path):
        """Test getting result for non-existent task."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"})

        result = store.get_result("queue_1", "task_2")
        assert result is None

    def test_get_all_results(self, tmp_path):
        """Test retrieving all results for a queue."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "first"})
        store.store_result("queue_1", "task_2", {"output": "second"})

        results = store.get_all_results("queue_1")
        assert len(results) == 2
        assert results[0]["task_id"] == "task_1"
        assert results[1]["task_id"] == "task_2"

    def test_get_all_results_empty_queue(self, tmp_path):
        """Test getting results for empty queue."""
        store = ResultsStore(base_dir=tmp_path)

        results = store.get_all_results("queue_1")
        assert results == []

    def test_get_all_results_nonexistent_queue(self, tmp_path):
        """Test getting results for non-existent queue."""
        store = ResultsStore(base_dir=tmp_path)

        results = store.get_all_results("nonexistent")
        assert results == []

    def test_get_summary(self, tmp_path):
        """Test retrieving summary."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, status="completed")
        store.store_result("queue_1", "task_2", {"output": "failed"}, status="failed")

        summary = store.get_summary("queue_1")
        assert summary["queue_id"] == "queue_1"
        assert summary["total_tasks"] == 2
        assert summary["completed_tasks"] == 1
        assert summary["failed_tasks"] == 1

    def test_get_summary_nonexistent_queue(self, tmp_path):
        """Test getting summary for non-existent queue."""
        store = ResultsStore(base_dir=tmp_path)

        summary = store.get_summary("nonexistent")
        assert summary["queue_id"] == "nonexistent"
        assert summary["total_tasks"] == 0
        assert summary["completed_tasks"] == 0
        assert summary["failed_tasks"] == 0

    def test_get_summary_with_metadata(self, tmp_path):
        """Test summary includes metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, status="completed")

        summary = store.get_summary("queue_1")
        assert "total_tokens" in summary
        assert "total_duration" in summary
        assert "completed_at" in summary

    def test_update_summary(self, tmp_path):
        """Test updating summary manually."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, status="completed")

        # Manually update summary
        store._update_summary("queue_1")

        summary_file = tmp_path / "queue_1" / "summary.json"
        assert summary_file.exists()

        summary = json.loads(summary_file.read_text(encoding="utf-8"))
        assert summary["queue_id"] == "queue_1"

    def test_store_result_with_none_error(self, tmp_path):
        """Test storing result with None error."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, error=None)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["error"] is None

    def test_store_result_with_empty_result_data(self, tmp_path):
        """Test storing result with empty result data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {})

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == {}

    def test_store_result_with_zero_tokens(self, tmp_path):
        """Test storing result with zero tokens."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, tokens_used=0)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["tokens_used"] == 0

    def test_store_result_with_zero_duration(self, tmp_path):
        """Test storing result with zero duration."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, duration_seconds=0)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["duration_seconds"] == 0

    def test_store_result_with_complex_metadata(self, tmp_path):
        """Test storing result with complex metadata."""
        store = ResultsStore(base_dir=tmp_path)
        metadata = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "boolean": True,
            "null": None,
        }
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata=metadata)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] == metadata

    def test_store_result_creates_summary_if_missing(self, tmp_path):
        """Test that store_result creates summary if it doesn't exist."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"})

        summary_file = tmp_path / "queue_1" / "summary.json"
        assert summary_file.exists()

    def test_store_result_updates_existing_summary(self, tmp_path):
        """Test that store_result updates existing summary."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, status="completed")
        store.store_result("queue_1", "task_2", {"output": "done"}, status="completed")

        summary_file = tmp_path / "queue_1" / "summary.json"
        summary = json.loads(summary_file.read_text(encoding="utf-8"))

        assert summary["total_tasks"] == 2
        assert summary["completed_tasks"] == 2

    def test_store_result_with_custom_status(self, tmp_path):
        """Test storing result with custom status."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, status="custom_status")

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["status"] == "custom_status"

    def test_store_result_with_custom_error_message(self, tmp_path):
        """Test storing result with custom error message."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result(
            "queue_1",
            "task_1",
            {},
            status="failed",
            error="Custom error message with special chars: @#$%",
        )

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["error"] == "Custom error message with special chars: @#$%"

    def test_store_result_with_large_result_data(self, tmp_path):
        """Test storing result with large result data."""
        store = ResultsStore(base_dir=tmp_path)
        large_data = {"data": "x" * 10000}
        store.store_result("queue_1", "task_1", large_data)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"]["data"] == "x" * 10000

    def test_store_result_with_unicode(self, tmp_path):
        """Test storing result with unicode characters."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result(
            "queue_1",
            "task_1",
            {"message": "Hello 世界 🌍 مرحبا"},
        )

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"]["message"] == "Hello 世界 🌍 مرحبا"

    def test_store_result_with_special_characters_in_task_id(self, tmp_path):
        """Test storing result with special characters in task_id."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1-with_special.chars", {"output": "done"})

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert "task_1-with_special.chars" in data

    def test_store_result_with_empty_queue_id(self, tmp_path):
        """Test storing result with empty queue_id."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("", "task_1", {"output": "done"})

        results_file = tmp_path / "" / "results.json"
        assert results_file.exists()

    def test_store_result_with_empty_task_id(self, tmp_path):
        """Test storing result with empty task_id."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "", {"output": "done"})

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert "" in data

    def test_store_result_with_negative_tokens(self, tmp_path):
        """Test storing result with negative tokens (should be allowed)."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, tokens_used=-100)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["tokens_used"] == -100

    def test_store_result_with_negative_duration(self, tmp_path):
        """Test storing result with negative duration (should be allowed)."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, duration_seconds=-1.0)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["duration_seconds"] == -1.0

    def test_store_result_with_float_tokens(self, tmp_path):
        """Test storing result with float tokens."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, tokens_used=100.5)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["tokens_used"] == 100.5

    def test_store_result_with_float_duration(self, tmp_path):
        """Test storing result with float duration."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, duration_seconds=1.5)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["duration_seconds"] == 1.5

    def test_store_result_with_none_metadata(self, tmp_path):
        """Test storing result with None metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata=None)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] is None

    def test_store_result_with_empty_metadata(self, tmp_path):
        """Test storing result with empty metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata={})

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] == {}

    def test_store_result_with_list_metadata(self, tmp_path):
        """Test storing result with list metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata=[1, 2, 3])

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] == [1, 2, 3]

    def test_store_result_with_string_metadata(self, tmp_path):
        """Test storing result with string metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata="test")

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] == "test"

    def test_store_result_with_integer_metadata(self, tmp_path):
        """Test storing result with integer metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata=42)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] == 42

    def test_store_result_with_boolean_metadata(self, tmp_path):
        """Test storing result with boolean metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata=True)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] is True

    def test_store_result_with_none_result_data(self, tmp_path):
        """Test storing result with None result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", None)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] is None

    def test_store_result_with_string_result_data(self, tmp_path):
        """Test storing result with string result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", "just a string")

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == "just a string"

    def test_store_result_with_integer_result_data(self, tmp_path):
        """Test storing result with integer result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", 42)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == 42

    def test_store_result_with_boolean_result_data(self, tmp_path):
        """Test storing result with boolean result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", True)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] is True

    def test_store_result_with_float_result_data(self, tmp_path):
        """Test storing result with float result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", 3.14)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == 3.14

    def test_store_result_with_empty_string_result_data(self, tmp_path):
        """Test storing result with empty string result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", "")

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == ""

    def test_store_result_with_zero_result_data(self, tmp_path):
        """Test storing result with zero result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", 0)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == 0

    def test_store_result_with_false_result_data(self, tmp_path):
        """Test storing result with False result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", False)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] is False

    def test_store_result_with_none_status(self, tmp_path):
        """Test storing result with None status."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, status=None)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["status"] is None

    def test_store_result_with_empty_string_status(self, tmp_path):
        """Test storing result with empty string status."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, status="")

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["status"] == ""

    def test_store_result_with_none_duration(self, tmp_path):
        """Test storing result with None duration."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, duration_seconds=None)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["duration_seconds"] is None

    def test_store_result_with_none_tokens(self, tmp_path):
        """Test storing result with None tokens."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, tokens_used=None)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["tokens_used"] is None

    def test_store_result_with_none_error(self, tmp_path):
        """Test storing result with None error."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, error=None)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["error"] is None

    def test_store_result_with_empty_string_error(self, tmp_path):
        """Test storing result with empty string error."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, error="")

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["error"] == ""

    def test_store_result_with_none_metadata(self, tmp_path):
        """Test storing result with None metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata=None)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] is None

    def test_store_result_with_empty_string_metadata(self, tmp_path):
        """Test storing result with empty string metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata="")

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] == ""

    def test_store_result_with_integer_metadata(self, tmp_path):
        """Test storing result with integer metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata=42)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] == 42

    def test_store_result_with_boolean_metadata(self, tmp_path):
        """Test storing result with boolean metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata=True)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] is True

    def test_store_result_with_list_metadata(self, tmp_path):
        """Test storing result with list metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata=[1, 2, 3])

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] == [1, 2, 3]

    def test_store_result_with_dict_metadata(self, tmp_path):
        """Test storing result with dict metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata={"key": "value"})

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] == {"key": "value"}

    def test_store_result_with_nested_dict_metadata(self, tmp_path):
        """Test storing result with nested dict metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result(
            "queue_1",
            "task_1",
            {"output": "done"},
            metadata={"outer": {"inner": {"deep": "value"}}},
        )

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"] == {"outer": {"inner": {"deep": "value"}}}

    def test_store_result_with_unicode_metadata(self, tmp_path):
        """Test storing result with unicode metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result(
            "queue_1",
            "task_1",
            {"output": "done"},
            metadata={"message": "Hello 世界 🌍 مرحبا"},
        )

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"]["message"] == "Hello 世界 🌍 مرحبا"

    def test_store_result_with_special_characters_metadata(self, tmp_path):
        """Test storing result with special characters in metadata."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result(
            "queue_1",
            "task_1",
            {"output": "done"},
            metadata={"special": "@#$%^&*()_+-=[]{}|;':\",./<>?"},
        )

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"]["special"] == "@#$%^&*()_+-=[]{}|;':\",./<>?"

    def test_store_result_with_large_metadata(self, tmp_path):
        """Test storing result with large metadata."""
        store = ResultsStore(base_dir=tmp_path)
        large_metadata = {"data": "x" * 10000}
        store.store_result("queue_1", "task_1", {"output": "done"}, metadata=large_metadata)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["metadata"]["data"] == "x" * 10000

    def test_store_result_with_none_result_data(self, tmp_path):
        """Test storing result with None result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", None)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] is None

    def test_store_result_with_string_result_data(self, tmp_path):
        """Test storing result with string result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", "just a string")

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == "just a string"

    def test_store_result_with_integer_result_data(self, tmp_path):
        """Test storing result with integer result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", 42)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == 42

    def test_store_result_with_float_result_data(self, tmp_path):
        """Test storing result with float result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", 3.14)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == 3.14

    def test_store_result_with_boolean_result_data(self, tmp_path):
        """Test storing result with boolean result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", True)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] is True

    def test_store_result_with_list_result_data(self, tmp_path):
        """Test storing result with list result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", [1, 2, 3])

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == [1, 2, 3]

    def test_store_result_with_dict_result_data(self, tmp_path):
        """Test storing result with dict result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result("queue_1", "task_1", {"key": "value"})

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == {"key": "value"}

    def test_store_result_with_nested_dict_result_data(self, tmp_path):
        """Test storing result with nested dict result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result(
            "queue_1",
            "task_1",
            {"outer": {"inner": {"deep": "value"}}},
        )

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"] == {"outer": {"inner": {"deep": "value"}}}

    def test_store_result_with_unicode_result_data(self, tmp_path):
        """Test storing result with unicode result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result(
            "queue_1",
            "task_1",
            {"message": "Hello 世界 🌍 مرحبا"},
        )

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"]["message"] == "Hello 世界 🌍 مرحبا"

    def test_store_result_with_special_characters_result_data(self, tmp_path):
        """Test storing result with special characters in result_data."""
        store = ResultsStore(base_dir=tmp_path)
        store.store_result(
            "queue_1",
            "task_1",
            {"special": "@#$%^&*()_+-=[]{}|;':\",./<>?"},
        )

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"]["special"] == "@#$%^&*()_+-=[]{}|;':\",./<>?"

    def test_store_result_with_large_result_data(self, tmp_path):
        """Test storing result with large result_data."""
        store = ResultsStore(base_dir=tmp_path)
        large_data = {"data": "x" * 10000}
        store.store_result("queue_1", "task_1", large_data)

        results_file = tmp_path / "queue_1" / "results.json"
        data = json.loads(results_file.read_text(encoding="utf-8"))

        assert data["task_1"]["result_data"]["data"] == "x" * 10000
