"""Unit tests for the core schema inference engine."""

import json
from pathlib import Path

import pytest

from json_schema_profiler.inference import infer_schema

FIXTURES = Path(__file__).parent / "fixtures"


# ── Task 2: Core schema inference engine ──────────────────────────────────────


class TestSimpleObject:
    """Test (1): simple object type detection."""

    def test_flat_object_types(self):
        """A flat dict with string, int, float, bool fields should detect each type."""
        data = {"name": "Alice", "age": 30, "score": 95.5, "active": True}
        schema = infer_schema(data)
        assert schema["type"] == "object"
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["age"]["type"] == "integer"
        assert schema["properties"]["score"]["type"] == "number"
        assert schema["properties"]["active"]["type"] == "boolean"

    def test_required_fields_all_present(self):
        """All fields present in every object should be marked required."""
        data = {"name": "Alice", "age": 30}
        schema = infer_schema(data)
        assert set(schema["required"]) == {"name", "age"}

    def test_numeric_min_max(self):
        """Numeric fields should include min/max metadata."""
        data = {"age": 30}
        schema = infer_schema(data)
        assert schema["properties"]["age"]["minimum"] == 30
        assert schema["properties"]["age"]["maximum"] == 30

    def test_string_min_max_length(self):
        """String fields should include minLength/maxLength metadata."""
        data = {"name": "Alice"}
        schema = infer_schema(data)
        assert schema["properties"]["name"]["minLength"] == 5
        assert schema["properties"]["name"]["maxLength"] == 5

    def test_low_cardinality_enum(self):
        """String field with ≤10 unique values should be flagged as enum candidate."""
        data = {"status": "active"}
        schema = infer_schema(data)
        assert "enum" in schema["properties"]["status"]
        assert "active" in schema["properties"]["status"]["enum"]


class TestNestedObject:
    """Test (2): nested object recursive inference."""

    def test_nested_dict_inferred(self):
        """A dict field should be recursively inferred as an object."""
        data = {"address": {"city": "Springfield", "zip": "62704"}}
        schema = infer_schema(data)
        assert schema["properties"]["address"]["type"] == "object"
        assert "city" in schema["properties"]["address"]["properties"]
        assert "zip" in schema["properties"]["address"]["properties"]

    def test_nested_required_fields(self):
        """Required fields should propagate into nested objects."""
        data = {"address": {"city": "Springfield", "zip": "62704"}}
        schema = infer_schema(data)
        assert set(schema["properties"]["address"]["required"]) == {"city", "zip"}


class TestArrayOfObjects:
    """Test (3): array-of-objects item schema inference."""

    def test_array_items_schema(self):
        """An array of dicts should produce an items schema."""
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        schema = infer_schema(data)
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "object"
        assert "id" in schema["items"]["properties"]
        assert "name" in schema["items"]["properties"]

    def test_array_items_required(self):
        """Required fields should be inferred for array items."""
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        schema = infer_schema(data)
        assert set(schema["items"]["required"]) == {"id", "name"}


class TestMixedTypes:
    """Test (4): mixed-type field handling."""

    def test_mixed_types_list(self):
        """A field with mixed types should report a list of types."""
        data = [
            {"id": 1, "value": "hello"},
            {"id": 2, "value": 42},
        ]
        schema = infer_schema(data)
        value_type = schema["items"]["properties"]["value"]["type"]
        assert "string" in value_type
        assert "integer" in value_type

    def test_mixed_types_preserves_constraints(self):
        """Mixed-type fields should still preserve applicable constraints."""
        data = [
            {"count": 10},
            {"count": 30},
        ]
        schema = infer_schema(data)
        assert schema["items"]["properties"]["count"]["minimum"] == 10
        assert schema["items"]["properties"]["count"]["maximum"] == 30


class TestEmptyArray:
    """Test (5): empty array returns empty properties."""

    def test_empty_array(self):
        """An empty array should return a valid schema with empty items."""
        data = []
        schema = infer_schema(data)
        assert schema["type"] == "array"
        assert schema["items"] == {}


class TestLowCardinality:
    """Test (10): low-cardinality enum candidate detection."""

    def test_enum_candidate(self):
        """String field with ≤10 unique values should be flagged as enum."""
        data = {"status": "active"}
        schema = infer_schema(data)
        assert "enum" in schema["properties"]["status"]

    def test_enum_values_sorted(self):
        """Enum values should be sorted."""
        data = {"status": "active"}
        schema = infer_schema(data)
        assert schema["properties"]["status"]["enum"] == ["active"]


class TestLargeSample:
    """Test (11): large sample (100 objects, 5 fields) produces correct schema."""

    def test_large_sample_schema(self):
        """100 objects with 5 fields should produce a valid schema."""
        with open(FIXTURES / "large_sample.json") as f:
            data = json.load(f)
        schema = infer_schema(data)
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "object"
        props = schema["items"]["properties"]
        assert "name" in props
        assert "age" in props
        assert "score" in props
        assert "active" in props
        assert "nested" in props
        # Check nested inference
        assert props["nested"]["type"] == "object"
        assert "x" in props["nested"]["properties"]
        assert "y" in props["nested"]["properties"]


class TestOptionalFields:
    """Test (7): optional field detection (field missing in some objects)."""

    def test_optional_field_not_required(self):
        """A field missing in some objects should not be required."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob"},
        ]
        schema = infer_schema(data)
        assert "age" not in schema["required"]
        assert "name" in schema["required"]


class TestNullHandling:
    """Test null value handling."""

    def test_null_values_ignored_for_type(self):
        """Null values should not affect type detection."""
        data = {"value": None, "value2": "hello"}
        schema = infer_schema(data)
        assert schema["properties"]["value2"]["type"] == "string"


# ── Task 4: Test fixtures ─────────────────────────────────────────────────────


class TestFixtures:
    """Test (4): fixture files are valid JSON."""

    @pytest.mark.parametrize("filename", [
        "simple.json",
        "nested.json",
        "array_of_objects.json",
        "mixed_types.json",
        "empty_array.json",
        "low_cardinality.json",
        "large_sample.json",
    ])
    def test_fixture_is_valid_json(self, filename):
        """All fixture files should be valid JSON."""
        path = FIXTURES / filename
        with open(path) as f:
            data = json.load(f)
        assert data is not None


# ── Task 6: End-to-end validation ─────────────────────────────────────────────


class TestEndToEnd:
    """Test (6): end-to-end validation of inferred schemas."""

    def test_simple_schema_is_valid_json_schema(self):
        """The inferred schema should be a valid JSON Schema draft-07 structure."""
        data = {"name": "Alice", "age": 30}
        schema = infer_schema(data)
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        assert schema["type"] == "object"

    def test_array_schema_is_valid_json_schema(self):
        """An array schema should have items with type."""
        data = [{"name": "Alice"}]
        schema = infer_schema(data)
        assert schema["type"] == "array"
        assert "items" in schema
        assert "type" in schema["items"]
