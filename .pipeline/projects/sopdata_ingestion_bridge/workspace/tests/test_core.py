"""Tests for core utilities (core.py)."""

import pytest
from sopdata_ingestion_bridge.core import get_default_mapping, merge_mappings, DEFAULT_MAPPING


class TestGetDefaultMapping:
    def test_returns_dict(self):
        result = get_default_mapping()
        assert isinstance(result, dict)

    def test_returns_copy_not_shared_reference(self):
        m1 = get_default_mapping()
        m2 = get_default_mapping()
        m1["custom_key"] = "custom_value"
        assert "custom_key" not in m2

    def test_returns_copy_not_modified_default(self):
        m = get_default_mapping()
        m["task_name"] = "modified"
        assert DEFAULT_MAPPING["task_name"] == "task_name"

    def test_contains_expected_keys(self):
        m = get_default_mapping()
        assert "task_name" in m
        assert "description" in m
        assert "steps" in m
        assert "assignee" in m
        assert "deadline" in m
        assert "priority" in m

    def test_contains_aliases(self):
        m = get_default_mapping()
        assert "title" in m
        assert "desc" in m
        assert "step" in m
        assert "assigned_to" in m
        assert "due_date" in m
        assert "level" in m


class TestMergeMappings:
    def test_merge_with_none_custom_returns_default_copy(self):
        result = merge_mappings(DEFAULT_MAPPING, None)
        assert isinstance(result, dict)
        assert result == DEFAULT_MAPPING

    def test_merge_custom_overrides_defaults(self):
        custom = {"task_name": "custom_task_name"}
        result = merge_mappings(DEFAULT_MAPPING, custom)
        assert result["task_name"] == "custom_task_name"
        # Other keys should still be present
        assert "description" in result
        assert result["description"] == "description"

    def test_merge_adds_new_keys(self):
        custom = {"new_col": "new_field"}
        result = merge_mappings(DEFAULT_MAPPING, custom)
        assert "new_col" in result
        assert result["new_col"] == "new_field"
        assert "task_name" in result

    def test_merge_empty_custom_returns_default_copy(self):
        result = merge_mappings(DEFAULT_MAPPING, {})
        assert result == DEFAULT_MAPPING
        # Should be a copy, not the same object
        assert result is not DEFAULT_MAPPING

    def test_merge_multiple_custom_keys(self):
        custom = {
            "title": "task_name",
            "desc": "description",
            "custom_field": "custom_field",
        }
        result = merge_mappings(DEFAULT_MAPPING, custom)
        # Custom keys override by key, not by value
        assert result["task_name"] == "task_name"  # default preserved (key not in custom)
        assert result["title"] == "task_name"  # new key from custom
        assert result["description"] == "description"  # default preserved (key not in custom)
        assert result["desc"] == "description"  # new key from custom
        assert result["custom_field"] == "custom_field"
        assert result["steps"] == "steps"  # default value preserved

    def test_merge_does_not_modify_originals(self):
        default = get_default_mapping()
        custom = {"task_name": "custom"}
        default_copy = dict(default)
        custom_copy = dict(custom)
        merge_mappings(default, custom)
        assert default == default_copy
        assert custom == custom_copy
