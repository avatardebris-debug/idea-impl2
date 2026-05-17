"""Tests for preset schema definitions (Task 3)."""

import pytest

from vastai_init.presets.schema import (
    PRESET_OPTIONAL_FIELDS,
    PRESET_REQUIRED_FIELDS,
    PRESET_SCHEMA,
    get_field_default,
    get_schema_field,
    is_required_field,
)


# ── Schema constants ───────────────────────────────────────────────

class TestSchemaConstants:
    def test_required_fields_are_subset_of_schema(self):
        for field in PRESET_REQUIRED_FIELDS:
            assert field in PRESET_SCHEMA

    def test_optional_fields_are_subset_of_schema(self):
        for field in PRESET_OPTIONAL_FIELDS:
            assert field in PRESET_SCHEMA

    def test_required_fields_are_required_in_schema(self):
        for field in PRESET_REQUIRED_FIELDS:
            assert PRESET_SCHEMA[field]["required"] is True

    def test_optional_fields_are_not_required_in_schema(self):
        for field in PRESET_OPTIONAL_FIELDS:
            assert PRESET_SCHEMA[field]["required"] is False

    def test_required_fields_have_type_str(self):
        for field in PRESET_REQUIRED_FIELDS:
            assert PRESET_SCHEMA[field]["type"] is str

    def test_required_fields_have_no_default(self):
        for field in PRESET_REQUIRED_FIELDS:
            assert "default" not in PRESET_SCHEMA[field]

    def test_optional_fields_have_defaults(self):
        for field, info in PRESET_OPTIONAL_FIELDS.items():
            assert PRESET_SCHEMA[field].get("default") == info["default"]

    def test_optional_fields_have_descriptions(self):
        for field, info in PRESET_OPTIONAL_FIELDS.items():
            assert "description" in PRESET_SCHEMA[field]
            assert PRESET_SCHEMA[field]["description"] == info["description"]

    def test_all_required_fields_present(self):
        expected = ["name", "gpu_type", "price_cap", "storage", "image"]
        assert PRESET_REQUIRED_FIELDS == expected

    def test_all_optional_fields_present(self):
        expected = [
            "ssh_commands", "env_vars", "disk_size", "region", "min_vram",
            "uptime", "ssh_public_key", "docker_args", "ports", "labels",
            "timeout", "poll_interval", "count",
        ]
        assert set(PRESET_OPTIONAL_FIELDS.keys()) == set(expected)


# ── get_schema_field ──────────────────────────────────────────────

class TestGetSchemaField:
    def test_existing_required_field(self):
        field = get_schema_field("name")
        assert field is not None
        assert field["required"] is True
        assert field["type"] is str

    def test_existing_optional_field(self):
        field = get_schema_field("ssh_commands")
        assert field is not None
        assert field["required"] is False
        assert field["type"] is list

    def test_nonexistent_field(self):
        assert get_schema_field("nonexistent_field") is None

    def test_empty_string_field(self):
        assert get_schema_field("") is None


# ── is_required_field ─────────────────────────────────────────────

class TestIsRequiredField:
    def test_required_field(self):
        assert is_required_field("name") is True
        assert is_required_field("gpu_type") is True
        assert is_required_field("price_cap") is True
        assert is_required_field("storage") is True
        assert is_required_field("image") is True

    def test_optional_field(self):
        assert is_required_field("ssh_commands") is False
        assert is_required_field("env_vars") is False
        assert is_required_field("timeout") is False

    def test_nonexistent_field(self):
        assert is_required_field("nonexistent_field") is False

    def test_empty_string_field(self):
        assert is_required_field("") is False


# ── get_field_default ─────────────────────────────────────────────

class TestGetFieldDefault:
    def test_required_field_no_default(self):
        assert get_field_default("name") is None
        assert get_field_default("gpu_type") is None

    def test_optional_field_with_default(self):
        assert get_field_default("ssh_commands") == []
        assert get_field_default("env_vars") == {}
        assert get_field_default("docker_args") == {}
        assert get_field_default("ports") == []
        assert get_field_default("labels") == {}

    def test_optional_field_with_numeric_default(self):
        assert get_field_default("timeout") == 300
        assert get_field_default("poll_interval") == 10
        assert get_field_default("count") == 1

    def test_optional_field_with_none_default(self):
        assert get_field_default("disk_size") is None
        assert get_field_default("region") is None
        assert get_field_default("min_vram") is None
        assert get_field_default("uptime") is None
        assert get_field_default("ssh_public_key") is None

    def test_nonexistent_field(self):
        assert get_field_default("nonexistent_field") is None

    def test_empty_string_field(self):
        assert get_field_default("") is None


# ── Schema type constraints ───────────────────────────────────────

class TestSchemaTypeConstraints:
    def test_optional_field_types(self):
        assert PRESET_OPTIONAL_FIELDS["ssh_commands"]["type"] is list
        assert PRESET_OPTIONAL_FIELDS["env_vars"]["type"] is dict
        assert PRESET_OPTIONAL_FIELDS["disk_size"]["type"] == (int, str)
        assert PRESET_OPTIONAL_FIELDS["region"]["type"] is str
        assert PRESET_OPTIONAL_FIELDS["min_vram"]["type"] == (int, str)
        assert PRESET_OPTIONAL_FIELDS["uptime"]["type"] == (int, str)
        assert PRESET_OPTIONAL_FIELDS["ssh_public_key"]["type"] is str
        assert PRESET_OPTIONAL_FIELDS["docker_args"]["type"] is dict
        assert PRESET_OPTIONAL_FIELDS["ports"]["type"] is list
        assert PRESET_OPTIONAL_FIELDS["labels"]["type"] is dict
        assert PRESET_OPTIONAL_FIELDS["timeout"]["type"] is int
        assert PRESET_OPTIONAL_FIELDS["poll_interval"]["type"] is int
        assert PRESET_OPTIONAL_FIELDS["count"]["type"] is int

    def test_schema_contains_all_optional_fields(self):
        for field in PRESET_OPTIONAL_FIELDS:
            assert field in PRESET_SCHEMA

    def test_schema_contains_all_required_fields(self):
        for field in PRESET_REQUIRED_FIELDS:
            assert field in PRESET_SCHEMA
