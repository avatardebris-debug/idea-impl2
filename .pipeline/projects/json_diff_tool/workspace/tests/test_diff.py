"""Unit tests for the JSON diff tool core functionality."""

import pytest
import json
import tempfile
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from json_diff_tool.loader import load_json
from json_diff_tool.diff import compare_json, DiffEntry
from json_diff_tool.formatter import format_diff


class TestLoadJson:
    """Tests for the load_json function."""
    
    def test_load_valid_json_file(self):
        """Test loading a valid JSON file."""
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump({"key": "value"}, f)
            result = load_json(path)
            assert result == {"key": "value"}
        finally:
            os.unlink(path)

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_json("/nonexistent/path/file.json")
        assert "nonexistent" in str(exc_info.value)

    def test_load_invalid_json_file(self):
        """Test loading a file with invalid JSON raises ValueError."""
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write("{invalid json}")
            with pytest.raises(ValueError) as exc_info:
                load_json(path)
            assert "Invalid JSON" in str(exc_info.value)
        finally:
            os.unlink(path)

    def test_load_empty_object(self):
        """Test loading a file with an empty JSON object."""
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump({}, f)
            result = load_json(path)
            assert result == {}
        finally:
            os.unlink(path)

    def test_load_array(self):
        """Test loading a file with a JSON array."""
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump([1, 2, 3], f)
            result = load_json(path)
            assert result == [1, 2, 3]
        finally:
            os.unlink(path)


class TestCompareJson:
    """Tests for the compare_json function."""
    
    def test_identical_objects(self):
        """Test that identical objects produce no diffs."""
        result = compare_json({"a": 1}, {"a": 1})
        assert len(result) == 0
    
    def test_identical_arrays(self):
        """Test that identical arrays produce no diffs."""
        result = compare_json([1, 2, 3], [1, 2, 3])
        assert len(result) == 0
    
    def test_added_key(self):
        """Test detecting an added key in an object."""
        result = compare_json({"a": 1}, {"a": 1, "b": 2})
        assert len(result) == 1
        assert result[0].action == DiffEntry.ADDED
        assert result[0].path == "b"
        assert result[0].new_value == 2
    
    def test_removed_key(self):
        """Test detecting a removed key in an object."""
        result = compare_json({"a": 1, "b": 2}, {"a": 1})
        assert len(result) == 1
        assert result[0].action == DiffEntry.REMOVED
        assert result[0].path == "b"
        assert result[0].old_value == 2
    
    def test_changed_value(self):
        """Test detecting a changed value."""
        result = compare_json({"a": 1}, {"a": 2})
        assert len(result) == 1
        assert result[0].action == DiffEntry.CHANGED
        assert result[0].path == "a"
        assert result[0].old_value == 1
        assert result[0].new_value == 2
    
    def test_nested_object_diff(self):
        """Test detecting differences in nested objects."""
        obj1 = {"a": {"b": 1, "c": 2}}
        obj2 = {"a": {"b": 1, "d": 3}}
        result = compare_json(obj1, obj2)
        assert len(result) == 2
        paths = {r.path for r in result}
        assert "a.c" in paths
        assert "a.d" in paths
    
    def test_array_added_element(self):
        """Test detecting an added element in an array."""
        result = compare_json([1, 2], [1, 2, 3])
        assert len(result) == 1
        assert result[0].action == DiffEntry.ADDED
        assert result[0].path == "[2]"
        assert result[0].new_value == 3
    
    def test_array_removed_element(self):
        """Test detecting a removed element in an array."""
        result = compare_json([1, 2, 3], [1, 2])
        assert len(result) == 1
        assert result[0].action == DiffEntry.REMOVED
        assert result[0].path == "[2]"
        assert result[0].old_value == 3
    
    def test_type_mismatch(self):
        """Test detecting a type mismatch between values."""
        result = compare_json({"a": 1}, {"a": "1"})
        assert len(result) == 1
        assert result[0].action == DiffEntry.CHANGED
        assert result[0].old_value == 1
        assert result[0].new_value == "1"
    
    def test_empty_vs_nonempty_object(self):
        """Test comparing empty object with non-empty object."""
        result = compare_json({}, {"a": 1})
        assert len(result) == 1
        assert result[0].action == DiffEntry.ADDED
        assert result[0].path == "a"
    
    def test_deeply_nested_structure(self):
        """Test comparing deeply nested structures."""
        obj1 = {"a": {"b": {"c": {"d": 1}}}}
        obj2 = {"a": {"b": {"c": {"d": 2}}}}
        result = compare_json(obj1, obj2)
        assert len(result) == 1
        assert result[0].path == "a.b.c.d"
        assert result[0].action == DiffEntry.CHANGED
    
    def test_multiple_differences(self):
        """Test detecting multiple differences in one comparison."""
        obj1 = {"a": 1, "b": 2, "c": 3}
        obj2 = {"a": 10, "b": 2, "d": 4}
        result = compare_json(obj1, obj2)
        assert len(result) == 3
        actions = {r.action for r in result}
        assert DiffEntry.CHANGED in actions
        assert DiffEntry.ADDED in actions
        assert DiffEntry.REMOVED in actions


class TestFormatDiff:
    """Tests for the format_diff function."""
    
    def test_format_added_entry(self):
        """Test formatting an added diff entry."""
        entry = DiffEntry("key", DiffEntry.ADDED, None, "value")
        result = format_diff([entry])
        assert "+ key: value" in result
    
    def test_format_removed_entry(self):
        """Test formatting a removed diff entry."""
        entry = DiffEntry("key", DiffEntry.REMOVED, "value", None)
        result = format_diff([entry])
        assert "- key: value" in result
    
    def test_format_changed_entry(self):
        """Test formatting a changed diff entry."""
        entry = DiffEntry("key", DiffEntry.CHANGED, "old", "new")
        result = format_diff([entry])
        assert "→ key: old → new" in result
    
    def test_format_multiple_entries(self):
        """Test formatting multiple diff entries."""
        entries = [
            DiffEntry("a", DiffEntry.ADDED, None, 1),
            DiffEntry("b", DiffEntry.REMOVED, 2, None),
            DiffEntry("c", DiffEntry.CHANGED, 3, 4)
        ]
        result = format_diff(entries)
        assert "+ a: 1" in result
        assert "- b: 2" in result
        assert "→ c: 3 → 4" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
