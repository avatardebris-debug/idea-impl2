"""Tests for the Agency SOP Automator — Phase 1.

Tests cover:
- SOP loading and validation
- SOP execution with mock LLM
- Output formatting
- CLI entry point
- Edge cases (missing files, invalid inputs, etc.)
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure the workspace is on the path
_WORKSPACE = Path(__file__).resolve().parent
sys.path.insert(0, str(_WORKSPACE))

from agency_sop_automator.sop_loader import AgencySOP, SOPLoader
from agency_sop_automator.executor import SOPExecutor, MockLLMClient, execute_sop
from agency_sop_automator.prompts import fill_prompt, load_prompt_template, build_step_prompt
from agency_sop_automator.output_formatter import format_output
from agency_sop_automator.config import get_sops_dir, get_prompts_dir, get_output_dir
from agency_sop_automator.main import main


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def sample_sop_data() -> Dict[str, Any]:
    """Sample SOP definition as a dict."""
    return {
        "name": "test_sop",
        "description": "A test SOP",
        "inputs": [
            {"name": "input1", "type": "string", "required": True},
            {"name": "input2", "type": "number", "required": False},
        ],
        "steps": [
            {
                "name": "step1",
                "description": "First step",
                "prompt_template": "default_step",
                "output_key": "step1_output",
                "required_inputs": ["input1"],
            },
            {
                "name": "step2",
                "description": "Second step",
                "prompt_template": "default_step",
                "output_key": "step2_output",
                "required_inputs": ["input1", "step1_output"],
            },
        ],
        "output_format": "yaml",
    }


@pytest.fixture
def sample_sop(sample_sop_data) -> AgencySOP:
    """Create an AgencySOP from sample data."""
    return AgencySOP.from_dict(sample_sop_data)


@pytest.fixture
def sample_input_data() -> Dict[str, Any]:
    """Sample input data for the test SOP."""
    return {"input1": "test_value", "input2": 42}


@pytest.fixture
def temp_sops_dir(tmp_path: Path) -> Path:
    """Create a temporary SOPs directory with a test SOP."""
    sops_dir = tmp_path / "sops"
    sops_dir.mkdir()

    sop_data = {
        "name": "test_sop",
        "description": "A test SOP",
        "inputs": [
            {"name": "input1", "type": "string", "required": True},
        ],
        "steps": [
            {
                "name": "step1",
                "description": "First step",
                "prompt_template": "default_step",
                "output_key": "step1_output",
                "required_inputs": ["input1"],
            },
        ],
        "output_format": "yaml",
    }

    import yaml
    (sops_dir / "test_sop.yaml").write_text(yaml.dump(sop_data))
    return sops_dir


@pytest.fixture
def temp_prompts_dir(tmp_path: Path) -> Path:
    """Create a temporary prompts directory with a test template."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    template = "Hello {{name}}! You have {{count}} items."
    (prompts_dir / "greeting.md").write_text(template)
    return prompts_dir


# ── AgencySOP Tests ──────────────────────────────────────────────

class TestAgencySOP:
    """Tests for the AgencySOP model."""

    def test_from_dict(self, sample_sop_data):
        """Test creating an AgencySOP from a dict."""
        sop = AgencySOP.from_dict(sample_sop_data)
        assert sop.name == "test_sop"
        assert sop.description == "A test SOP"
        assert len(sop.inputs) == 2
        assert len(sop.steps) == 2
        assert sop.inputs[0].name == "input1"
        assert sop.inputs[0].required is True
        assert sop.steps[0].name == "step1"
        assert sop.steps[0].output_key == "step1_output"

    def test_to_sop(self, sample_sop):
        """Test converting AgencySOP to the shared SOP model."""
        shared_sop = sample_sop.to_sop()
        assert shared_sop.name == sample_sop.name
        assert shared_sop.description == sample_sop.description
        assert len(shared_sop.inputs) == len(sample_sop.inputs)
        assert len(shared_sop.steps) == len(sample_sop.steps)

    def test_default_output_format(self):
        """Test that output_format defaults to empty string."""
        sop = AgencySOP(name="test", description="test")
        assert sop.output_format == ""

    def test_default_metadata(self):
        """Test that metadata defaults to None."""
        sop = AgencySOP(name="test", description="test")
        assert sop.metadata is None


# ── SOPLoader Tests ──────────────────────────────────────────────

class TestSOPLoader:
    """Tests for the SOPLoader class."""

    def test_list_sops(self, temp_sops_dir):
        """Test listing available SOPs."""
        loader = SOPLoader(sops_dir=temp_sops_dir)
        sops = loader.list_sops()
        assert "test_sop" in sops

    def test_load_sop(self, temp_sops_dir):
        """Test loading a specific SOP."""
        loader = SOPLoader(sops_dir=temp_sops_dir)
        sop = loader.load_sop("test_sop")
        assert sop.name == "test_sop"
        assert len(sop.steps) == 1

    def test_load_sop_not_found(self, temp_sops_dir):
        """Test loading a non-existent SOP raises FileNotFoundError."""
        loader = SOPLoader(sops_dir=temp_sops_dir)
        with pytest.raises(FileNotFoundError, match="not found"):
            loader.load_sop("nonexistent")

    def test_load_sop_invalid_yaml(self, tmp_path: Path):
        """Test loading an invalid YAML file raises ValueError."""
        sops_dir = tmp_path / "sops"
        sops_dir.mkdir()
        (sops_dir / "invalid.yaml").write_text("not: valid: yaml: [[[")

        loader = SOPLoader(sops_dir=sops_dir)
        with pytest.raises(ValueError):
            loader.load_sop("invalid")

    def test_load_sop_invalid_structure(self, tmp_path: Path):
        """Test loading a YAML file with invalid structure raises ValueError."""
        sops_dir = tmp_path / "sops"
        sops_dir.mkdir()
        (sops_dir / "invalid.yaml").write_text("just a string")

        loader = SOPLoader(sops_dir=sops_dir)
        with pytest.raises(ValueError, match="does not contain a valid YAML mapping"):
            loader.load_sop("invalid")

    def test_get_sop_alias(self, temp_sops_dir):
        """Test that get_sop is an alias for load_sop."""
        loader = SOPLoader(sops_dir=temp_sops_dir)
        sop1 = loader.get_sop("test_sop")
        sop2 = loader.load_sop("test_sop")
        assert sop1.name == sop2.name

    def test_validate_input_valid(self, sample_sop, sample_input_data):
        """Test validating valid input data."""
        loader = SOPLoader()
        validated = loader.validate_input(sample_sop, sample_input_data)
        assert validated["input1"] == "test_value"
        assert validated["input2"] == 42

    def test_validate_input_missing_required(self, sample_sop):
        """Test validating input with missing required field."""
        loader = SOPLoader()
        with pytest.raises(ValueError, match="Missing required input"):
            loader.validate_input(sample_sop, {})

    def test_validate_input_wrong_type(self, sample_sop):
        """Test validating input with wrong type."""
        loader = SOPLoader()
        with pytest.raises(ValueError, match="Invalid type for input"):
            loader.validate_input(sample_sop, {"input1": 123})  # input1 should be string


# ── Executor Tests ───────────────────────────────────────────────

class TestSOPExecutor:
    """Tests for the SOPExecutor class."""

    def test_run_with_mock(self, sample_sop, sample_input_data):
        """Test running an SOP with mock LLM client."""
        executor = SOPExecutor(sample_sop, MockLLMClient())
        result = executor.run(sample_input_data)

        assert "step1_output" in result
        assert "step2_output" in result
        assert "_sop_name" in result
        assert "_execution_log" in result
        assert len(result["_execution_log"]) == 2

    def test_run_step_failure(self, sample_sop, sample_input_data):
        """Test that step failures are caught and reported."""
        class FailingLLMClient:
            def call(self, system_prompt: str, user_prompt: str) -> str:
                raise RuntimeError("Simulated failure")

        executor = SOPExecutor(sample_sop, FailingLLMClient())
        with pytest.raises(ValueError, match="Step 'step1'"):
            executor.run(sample_input_data)

    def test_get_step_outputs(self, sample_sop, sample_input_data):
        """Test retrieving step outputs."""
        executor = SOPExecutor(sample_sop, MockLLMClient())
        executor.run(sample_input_data)
        outputs = executor.get_step_outputs()
        assert len(outputs) == 2

    def test_get_execution_log(self, sample_sop, sample_input_data):
        """Test retrieving execution log."""
        executor = SOPExecutor(sample_sop, MockLLMClient())
        executor.run(sample_input_data)
        log = executor.get_execution_log()
        assert len(log) == 2
        assert log[0].step_name == "step1"
        assert log[1].step_name == "step2"

    def test_execute_sop_convenience(self, temp_sops_dir, sample_input_data):
        """Test the execute_sop convenience function."""
        # Temporarily override the sops dir
        old_sops_dir = os.environ.get("DST_SOPS_DIR")
        os.environ["DST_SOPS_DIR"] = str(temp_sops_dir)

        try:
            result = execute_sop("test_sop", sample_input_data, MockLLMClient())
            assert "step1_output" in result
        finally:
            if old_sops_dir:
                os.environ["DST_SOPS_DIR"] = old_sops_dir
            else:
                os.environ.pop("DST_SOPS_DIR", None)


# ── Prompt Tests ─────────────────────────────────────────────────

class TestPrompts:
    """Tests for the prompt system."""

    def test_fill_prompt(self):
        """Test filling placeholders in a template."""
        template = "Hello {{name}}! You have {{count}} items."
        context = {"name": "Alice", "count": 5}
        result = fill_prompt(template, context)
        assert result == "Hello Alice! You have 5 items."

    def test_fill_prompt_with_dict(self):
        """Test filling placeholders with dict values (should JSON-serialize)."""
        template = "Data: {{data}}"
        context = {"data": {"key": "value"}}
        result = fill_prompt(template, context)
        assert '"key": "value"' in result

    def test_load_prompt_template(self, temp_prompts_dir):
        """Test loading a prompt template."""
        template = load_prompt_template("greeting", temp_prompts_dir)
        assert "{{name}}" in template
        assert "{{count}}" in template

    def test_load_prompt_template_not_found(self, temp_prompts_dir):
        """Test loading a non-existent template raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_prompt_template("nonexistent", temp_prompts_dir)

    def test_build_step_prompt(self, sample_sop, sample_input_data):
        """Test building a step prompt."""
        prompt = build_step_prompt(
            sample_sop,
            step_index=0,
            input_data=sample_input_data,
            step_outputs=[],
        )
        assert "step1" in prompt
        assert "test_value" in prompt


# ── Output Formatter Tests ───────────────────────────────────────

class TestOutputFormatter:
    """Tests for the output formatter."""

    def test_format_yaml(self):
        """Test formatting as YAML."""
        data = {"key": "value", "nested": {"a": 1}}
        result = format_output(data, output_format="yaml")
        assert "key: value" in result

    def test_format_json(self):
        """Test formatting as JSON."""
        data = {"key": "value", "nested": {"a": 1}}
        result = format_output(data, output_format="json")
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_format_csv(self):
        """Test formatting as CSV."""
        data = {"key1": "value1", "key2": "value2"}
        result = format_output(data, output_format="csv")
        assert "key1" in result
        assert "value1" in result

    def test_format_text(self):
        """Test formatting as text."""
        data = {"key": "value", "_sop_name": "test"}
        result = format_output(data, output_format="text")
        assert "key: value" in result
        assert "test" in result

    def test_format_unsupported(self):
        """Test that unsupported format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported output format"):
            format_output({}, output_format="xml")

    def test_format_write_to_file(self, tmp_path: Path):
        """Test writing formatted output to a file."""
        data = {"key": "value"}
        output_path = str(tmp_path / "output.yaml")
        result = format_output(data, output_format="yaml", output_path=output_path)
        assert Path(output_path).exists()
        assert "key: value" in Path(output_path).read_text()


# ── CLI Tests ────────────────────────────────────────────────────

class TestCLI:
    """Tests for the CLI entry point."""

    def test_list_sops(self, temp_sops_dir):
        """Test listing SOPs via CLI."""
        old_sops_dir = os.environ.get("DST_SOPS_DIR")
        os.environ["DST_SOPS_DIR"] = str(temp_sops_dir)

        try:
            result = main(["--list-sops"])
            assert result == 0
        finally:
            if old_sops_dir:
                os.environ["DST_SOPS_DIR"] = old_sops_dir
            else:
                os.environ.pop("DST_SOPS_DIR", None)

    def test_run_with_input_json(self, temp_sops_dir):
        """Test running SOP with JSON input via CLI."""
        old_sops_dir = os.environ.get("DST_SOPS_DIR")
        os.environ["DST_SOPS_DIR"] = str(temp_sops_dir)

        try:
            result = main([
                "--sop", "test_sop",
                "--input", '{"input1": "test_value"}',
                "--no-mock",
            ])
            assert result == 0
        finally:
            if old_sops_dir:
                os.environ["DST_SOPS_DIR"] = old_sops_dir
            else:
                os.environ.pop("DST_SOPS_DIR", None)

    def test_run_with_input_file(self, temp_sops_dir, tmp_path: Path):
        """Test running SOP with input file via CLI."""
        input_file = tmp_path / "input.json"
        input_file.write_text('{"input1": "test_value"}')

        old_sops_dir = os.environ.get("DST_SOPS_DIR")
        os.environ["DST_SOPS_DIR"] = str(temp_sops_dir)

        try:
            result = main([
                "--sop", "test_sop",
                "--input-file", str(input_file),
                "--no-mock",
            ])
            assert result == 0
        finally:
            if old_sops_dir:
                os.environ["DST_SOPS_DIR"] = old_sops_dir
            else:
                os.environ.pop("DST_SOPS_DIR", None)

    def test_run_missing_required_input(self, temp_sops_dir):
        """Test running SOP with missing required input."""
        old_sops_dir = os.environ.get("DST_SOPS_DIR")
        os.environ["DST_SOPS_DIR"] = str(temp_sops_dir)

        try:
            result = main([
                "--sop", "test_sop",
                "--input", '{}',
                "--no-mock",
            ])
            assert result == 1  # Should fail
        finally:
            if old_sops_dir:
                os.environ["DST_SOPS_DIR"] = old_sops_dir
            else:
                os.environ.pop("DST_SOPS_DIR", None)

    def test_run_invalid_json(self):
        """Test running SOP with invalid JSON input."""
        result = main([
            "--sop", "test_sop",
            "--input", "not valid json",
        ])
        assert result == 1

    def test_run_no_input(self):
        """Test running SOP without providing input."""
        result = main(["--sop", "test_sop"])
        assert result == 2  # argparse error


# ── Config Tests ─────────────────────────────────────────────────

class TestConfig:
    """Tests for the config module."""

    def test_get_sops_dir_default(self):
        """Test getting default SOPs directory."""
        # Should return the default path
        sops_dir = get_sops_dir()
        assert sops_dir.exists() or sops_dir.parent.exists()

    def test_get_sops_dir_env_override(self):
        """Test overriding SOPs directory via env var."""
        old = os.environ.get("DST_SOPS_DIR")
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["DST_SOPS_DIR"] = tmpdir
            assert get_sops_dir() == Path(tmpdir)
        if old:
            os.environ["DST_SOPS_DIR"] = old
        else:
            os.environ.pop("DST_SOPS_DIR", None)

    def test_get_prompts_dir_default(self):
        """Test getting default prompts directory."""
        prompts_dir = get_prompts_dir()
        assert prompts_dir.exists() or prompts_dir.parent.exists()

    def test_get_output_dir_default(self):
        """Test getting default output directory."""
        output_dir = get_output_dir()
        assert output_dir.exists() or output_dir.parent.exists()


# ── Edge Cases ───────────────────────────────────────────────────

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_sops_directory(self, tmp_path: Path):
        """Test listing SOPs from an empty directory."""
        sops_dir = tmp_path / "sops"
        sops_dir.mkdir()
        loader = SOPLoader(sops_dir=sops_dir)
        assert loader.list_sops() == []

    def test_sop_with_no_steps(self, sample_sop_data):
        """Test SOP with no steps."""
        sample_sop_data["steps"] = []
        sop = AgencySOP.from_dict(sample_sop_data)
        assert len(sop.steps) == 0

    def test_sop_with_no_inputs(self, sample_sop_data):
        """Test SOP with no inputs."""
        sample_sop_data["inputs"] = []
        sop = AgencySOP.from_dict(sample_sop_data)
        assert len(sop.inputs) == 0

    def test_executor_with_no_llm_client(self, sample_sop, sample_input_data):
        """Test executor uses MockLLMClient when no client provided."""
        executor = SOPExecutor(sample_sop)
        result = executor.run(sample_input_data)
        assert "step1_output" in result

    def test_format_output_with_nested_data(self):
        """Test formatting nested data structures."""
        data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        result = format_output(data, output_format="json")
        parsed = json.loads(result)
        assert parsed["level1"]["level2"]["level3"] == "value"

    def test_format_csv_with_nested_data(self):
        """Test CSV formatting flattens nested data."""
        data = {
            "key1": "value1",
            "nested": {
                "key2": "value2"
            }
        }
        result = format_output(data, output_format="csv")
        assert "key1" in result
        assert "nested.key2" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
