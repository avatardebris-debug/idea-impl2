"""Tests for SOP Schema and Validation."""

import pytest
from pathlib import Path
import tempfile
import yaml

from drop_servicing_tool.sop_schema import (
    SOP, SOPInput, SOPStep, load_sop, validate_input, _coerce,
    SUPPORTED_INPUT_TYPES, Step
)


class TestSOPInput:
    """Tests for SOPInput model."""

    def test_valid_input_creation(self):
        """Test creating a valid SOPInput."""
        inp = SOPInput(name="test_field", type="string", required=True, description="A test field")
        assert inp.name == "test_field"
        assert inp.type == "string"
        assert inp.required is True
        assert inp.description == "A test field"

    def test_input_type_validation(self):
        """Test that invalid types are rejected."""
        with pytest.raises(ValueError, match="Unsupported input type"):
            SOPInput(name="test", type="invalid_type")

    def test_input_type_normalization(self):
        """Test that types are normalized to lowercase."""
        inp = SOPInput(name="test", type="STRING")
        assert inp.type == "string"

    def test_optional_input(self):
        """Test optional input field."""
        inp = SOPInput(name="optional_field", type="number", required=False)
        assert inp.required is False

    def test_all_supported_types(self):
        """Test all supported input types."""
        for type_name in SUPPORTED_INPUT_TYPES:
            inp = SOPInput(name=f"test_{type_name}", type=type_name)
            assert inp.type == type_name


class TestSOPStep:
    """Tests for SOPStep model."""

    def test_valid_step_creation(self):
        """Test creating a valid SOPStep."""
        step = SOPStep(
            name="test_step",
            description="Test step description",
            llm_required=True,
            output_key="test_output"
        )
        assert step.name == "test_step"
        assert step.description == "Test step description"
        assert step.llm_required is True
        assert step.output_key == "test_output"

    def test_step_default_output_key(self):
        """Test that output_key defaults to step name."""
        step = SOPStep(name="my_step", description="Test")
        assert step.output_key == "my_step"

    def test_step_default_prompt_template(self):
        """Test that prompt_template defaults to default_step."""
        step = SOPStep(name="test", description="Test")
        assert step.prompt_template == "default_step"


class TestSOP:
    """Tests for SOP model."""

    def test_valid_sop_creation(self):
        """Test creating a valid SOP."""
        sop = SOP(
            name="test_sop",
            description="Test SOP",
            inputs=[SOPInput(name="input1", type="string", required=True)],
            steps=[SOPStep(name="step1", description="Step 1")],
            output_format="JSON output"
        )
        assert sop.name == "test_sop"
        assert len(sop.inputs) == 1
        assert len(sop.steps) == 1
        assert sop.output_format == "JSON output"

    def test_sop_requires_steps(self):
        """Test that SOP must have at least one step."""
        with pytest.raises(ValueError, match="SOP must define at least one step"):
            SOP(name="test", description="Test", steps=[])

    def test_sop_step_name_uniqueness(self):
        """Test that step names must be unique."""
        with pytest.raises(ValueError, match="Step names must be unique"):
            SOP(
                name="test",
                description="Test",
                steps=[
                    SOPStep(name="step1", description="Step 1"),
                    SOPStep(name="step1", description="Step 2"),
                ]
            )

    def test_sop_metadata(self):
        """Test SOP with metadata."""
        sop = SOP(
            name="test",
            description="Test",
            steps=[SOPStep(name="step1", description="Step 1")],
            metadata={"version": "1.0", "author": "test"}
        )
        assert sop.metadata == {"version": "1.0", "author": "test"}


class TestLoadSOP:
    """Tests for load_sop function."""

    def test_load_valid_sop(self, tmp_path):
        """Test loading a valid SOP from YAML."""
        sop_data = {
            "name": "test_sop",
            "description": "Test SOP",
            "inputs": [
                {"name": "input1", "type": "string", "required": True}
            ],
            "steps": [
                {"name": "step1", "description": "Step 1"}
            ],
            "output_format": "JSON"
        }
        sop_path = tmp_path / "test_sop.yaml"
        sop_path.write_text(yaml.dump(sop_data), encoding="utf-8")

        sop = load_sop(sop_path)
        assert sop.name == "test_sop"
        assert len(sop.steps) == 1

    def test_load_sop_file_not_found(self):
        """Test loading non-existent SOP."""
        with pytest.raises(FileNotFoundError, match="SOP file not found"):
            load_sop("/nonexistent/path/sop.yaml")

    def test_load_sop_invalid_yaml(self, tmp_path):
        """Test loading malformed YAML."""
        sop_path = tmp_path / "invalid.yaml"
        sop_path.write_text("invalid: yaml: content: [", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid SOP"):
            load_sop(sop_path)

    def test_load_sop_invalid_structure(self, tmp_path):
        """Test loading SOP with invalid structure."""
        sop_path = tmp_path / "invalid.yaml"
        sop_path.write_text("not: a: sop: structure", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid SOP"):
            load_sop(sop_path)


class TestValidateInput:
    """Tests for validate_input function."""

    def test_validate_valid_input(self):
        """Test validating valid input data."""
        sop = SOP(
            name="test",
            description="Test",
            inputs=[
                SOPInput(name="name", type="string", required=True),
                SOPInput(name="age", type="number", required=False)
            ],
            steps=[SOPStep(name="step1", description="Step 1")]
        )
        input_data = {"name": "John", "age": 30}
        validated = validate_input(sop, input_data)
        assert validated == {"name": "John", "age": 30}

    def test_validate_missing_required_field(self):
        """Test validation fails for missing required field."""
        sop = SOP(
            name="test",
            description="Test",
            inputs=[
                SOPInput(name="name", type="string", required=True)
            ],
            steps=[SOPStep(name="step1", description="Step 1")]
        )
        with pytest.raises(ValueError, match="Required input field 'name' is missing"):
            validate_input(sop, {})

    def test_validate_optional_field_absent(self):
        """Test optional field can be absent."""
        sop = SOP(
            name="test",
            description="Test",
            inputs=[
                SOPInput(name="name", type="string", required=True),
                SOPInput(name="nickname", type="string", required=False)
            ],
            steps=[SOPStep(name="step1", description="Step 1")]
        )
        validated = validate_input(sop, {"name": "John"})
        assert "nickname" not in validated

    def test_validate_type_mismatch(self):
        """Test validation fails for type mismatch."""
        sop = SOP(
            name="test",
            description="Test",
            inputs=[
                SOPInput(name="age", type="number", required=True)
            ],
            steps=[SOPStep(name="step1", description="Step 1")]
        )
        with pytest.raises(ValueError, match="expected type 'number'"):
            validate_input(sop, {"age": "not a number"})


class TestCoerce:
    """Tests for _coerce function."""

    def test_coerce_string(self):
        """Test coercion to string."""
        assert _coerce("test", "string") == "test"

    def test_coerce_number_int(self):
        """Test coercion to number (int)."""
        assert _coerce(42, "number") == 42

    def test_coerce_number_float(self):
        """Test coercion to number (float)."""
        assert _coerce(3.14, "number") == 3.14

    def test_coerce_boolean_true(self):
        """Test coercion to boolean (True)."""
        assert _coerce(True, "boolean") is True

    def test_coerce_boolean_false(self):
        """Test coercion to boolean (False)."""
        assert _coerce(False, "boolean") is False

    def test_coerce_array(self):
        """Test coercion to array."""
        assert _coerce([1, 2, 3], "array") == [1, 2, 3]

    def test_coerce_object(self):
        """Test coercion to object."""
        assert _coerce({"key": "value"}, "object") == {"key": "value"}

    def test_coerce_type_mismatch(self):
        """Test coercion fails on type mismatch."""
        with pytest.raises(ValueError, match="expected type"):
            _coerce("not a number", "number")


class TestStepAlias:
    """Tests for Step alias."""

    def test_step_is_sopstep(self):
        """Test that Step is an alias for SOPStep."""
        assert Step is SOPStep
        step = Step(name="test", description="Test")
        assert isinstance(step, SOPStep)
