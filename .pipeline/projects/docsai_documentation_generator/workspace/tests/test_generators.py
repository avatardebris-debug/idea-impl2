"""Tests for the DocsAI generators."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

# Add workspace to path
WORKSPACE = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE))

from docsai.generators.api_spec import ApiSpecGenerator
from docsai.generators.base import BaseGenerator


# Sample symbols for testing
SAMPLE_SYMBOLS = [
    {
        "name": "greet",
        "kind": "function",
        "params": [{"name": "name", "type": "str"}],
        "return_type": "str",
        "docstring": "Greet a person by name.",
        "line_number": 3,
    },
    {
        "name": "Calculator",
        "kind": "class",
        "params": [],
        "return_type": "",
        "docstring": "A simple calculator class.",
        "line_number": 15,
    },
]


class TestApiSpecGenerator:
    """Tests for the API spec generator."""

    @pytest.fixture
    def generator(self) -> ApiSpecGenerator:
        return ApiSpecGenerator()

    def test_generate_yaml_output(self, generator: ApiSpecGenerator):
        """Test that YAML output is generated correctly."""
        result = generator.generate(
            symbols=SAMPLE_SYMBOLS,
            output_format="yaml",
            project_name="test_project",
            language="python",
        )
        assert isinstance(result, str)
        # Parse the YAML to verify structure
        spec = yaml.safe_load(result)
        assert spec["project_name"] == "test_project"
        assert spec["language"] == "python"
        assert len(spec["symbols"]) == 2

    def test_generate_json_output(self, generator: ApiSpecGenerator):
        """Test that JSON output is generated correctly."""
        result = generator.generate(
            symbols=SAMPLE_SYMBOLS,
            output_format="json",
            project_name="test_project",
            language="python",
        )
        assert isinstance(result, str)
        # Parse the JSON to verify structure
        spec = json.loads(result)
        assert spec["project_name"] == "test_project"
        assert spec["language"] == "python"
        assert len(spec["symbols"]) == 2

    def test_metadata_file_count(self, generator: ApiSpecGenerator):
        """Test that metadata file count is computed correctly."""
        symbols_with_files = [
            {"name": "greet", "kind": "function", "params": [], "return_type": "", "docstring": "", "line_number": 1, "file": "a.py"},
            {"name": "Calculator", "kind": "class", "params": [], "return_type": "", "docstring": "", "line_number": 10, "file": "a.py"},
            {"name": "helper", "kind": "function", "params": [], "return_type": "", "docstring": "", "line_number": 20, "file": "b.py"},
        ]
        result = generator.generate(
            symbols=symbols_with_files,
            output_format="yaml",
            project_name="test_project",
            language="python",
        )
        spec = yaml.safe_load(result)
        assert spec["metadata"]["file_count"] == 2
        assert spec["metadata"]["total_symbols"] == 3

    def test_default_project_name(self, generator: ApiSpecGenerator):
        """Test that default project name is 'unknown'."""
        result = generator.generate(
            symbols=SAMPLE_SYMBOLS,
            output_format="yaml",
        )
        spec = yaml.safe_load(result)
        assert spec["project_name"] == "unknown"

    def test_default_language(self, generator: ApiSpecGenerator):
        """Test that default language is 'unknown'."""
        result = generator.generate(
            symbols=SAMPLE_SYMBOLS,
            output_format="yaml",
        )
        spec = yaml.safe_load(result)
        assert spec["language"] == "unknown"

    def test_empty_symbols(self, generator: ApiSpecGenerator):
        """Test that empty symbols list is handled correctly."""
        result = generator.generate(
            symbols=[],
            output_format="yaml",
            project_name="empty_project",
            language="python",
        )
        spec = yaml.safe_load(result)
        assert spec["project_name"] == "empty_project"
        assert spec["metadata"]["total_symbols"] == 0

    def test_yaml_output_is_valid_yaml(self, generator: ApiSpecGenerator):
        """Test that YAML output can be parsed back."""
        result = generator.generate(
            symbols=SAMPLE_SYMBOLS,
            output_format="yaml",
            project_name="test_project",
            language="python",
        )
        # Should not raise
        spec = yaml.safe_load(result)
        assert isinstance(spec, dict)

    def test_json_output_is_valid_json(self, generator: ApiSpecGenerator):
        """Test that JSON output can be parsed back."""
        result = generator.generate(
            symbols=SAMPLE_SYMBOLS,
            output_format="json",
            project_name="test_project",
            language="python",
        )
        # Should not raise
        spec = json.loads(result)
        assert isinstance(spec, dict)

    def test_symbols_preserved(self, generator: ApiSpecGenerator):
        """Test that symbols are preserved in output."""
        result = generator.generate(
            symbols=SAMPLE_SYMBOLS,
            output_format="yaml",
            project_name="test_project",
            language="python",
        )
        spec = yaml.safe_load(result)
        for i, sym in enumerate(spec["symbols"]):
            assert sym["name"] == SAMPLE_SYMBOLS[i]["name"]
            assert sym["kind"] == SAMPLE_SYMBOLS[i]["kind"]
            assert sym["params"] == SAMPLE_SYMBOLS[i]["params"]
            assert sym["return_type"] == SAMPLE_SYMBOLS[i]["return_type"]
            assert sym["docstring"] == SAMPLE_SYMBOLS[i]["docstring"]

    def test_inherits_from_base_generator(self):
        """Test that ApiSpecGenerator inherits from BaseGenerator."""
        gen = ApiSpecGenerator()
        assert isinstance(gen, BaseGenerator)
