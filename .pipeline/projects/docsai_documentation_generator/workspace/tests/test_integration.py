"""Integration tests for DocsAI end-to-end workflows."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

# Add workspace to path
WORKSPACE = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE))

from docsai.parsers import get_parser
from docsai.generators.api_spec import ApiSpecGenerator
from docsai.generators.readme_generator import ReadmeGenerator


SAMPLE_PYTHON = WORKSPACE / "tests" / "sample_project" / "sample_python.py"
SAMPLE_TYPESCRIPT = WORKSPACE / "tests" / "sample_project" / "sample_typescript.ts"


class TestPythonEndToEnd:
    """End-to-end tests for Python documentation generation."""

    def test_parse_and_generate_yaml(self):
        """Test parsing Python and generating YAML spec."""
        parser = get_parser("python")
        symbols = parser.parse(str(SAMPLE_PYTHON))
        assert len(symbols) > 0

        generator = ApiSpecGenerator()
        result = generator.generate(
            symbols=symbols,
            output_format="yaml",
            project_name="sample_project",
            language="python",
        )
        spec = yaml.safe_load(result)
        assert spec["project_name"] == "sample_project"
        assert spec["language"] == "python"
        assert len(spec["symbols"]) > 0

    def test_parse_and_generate_json(self):
        """Test parsing Python and generating JSON spec."""
        parser = get_parser("python")
        symbols = parser.parse(str(SAMPLE_PYTHON))
        assert len(symbols) > 0

        generator = ApiSpecGenerator()
        result = generator.generate(
            symbols=symbols,
            output_format="json",
            project_name="sample_project",
            language="python",
        )
        spec = json.loads(result)
        assert spec["project_name"] == "sample_project"
        assert spec["language"] == "python"
        assert len(spec["symbols"]) > 0

    def test_parse_and_generate_readme(self):
        """Test parsing Python and generating README."""
        parser = get_parser("python")
        symbols = parser.parse(str(SAMPLE_PYTHON))
        assert len(symbols) > 0

        generator = ReadmeGenerator()
        result = generator.generate(
            symbols=symbols,
            output_format="markdown",
            project_name="sample_project",
            language="python",
        )
        assert isinstance(result, str)
        assert "sample_project" in result
        assert "Python" in result

    def test_full_pipeline_python(self):
        """Test the full documentation pipeline for Python."""
        parser = get_parser("python")
        symbols = parser.parse(str(SAMPLE_PYTHON))

        # Generate both YAML and JSON specs
        yaml_gen = ApiSpecGenerator()
        yaml_spec = yaml_gen.generate(
            symbols=symbols,
            output_format="yaml",
            project_name="sample_project",
            language="python",
        )

        json_gen = ApiSpecGenerator()
        json_spec = json_gen.generate(
            symbols=symbols,
            output_format="json",
            project_name="sample_project",
            language="python",
        )

        # Parse both and verify consistency
        yaml_data = yaml.safe_load(yaml_spec)
        json_data = json.loads(json_spec)

        assert yaml_data["project_name"] == json_data["project_name"]
        assert yaml_data["language"] == json_data["language"]
        assert len(yaml_data["symbols"]) == len(json_data["symbols"])


class TestTypeScriptEndToEnd:
    """End-to-end tests for TypeScript documentation generation."""

    def test_parse_and_generate_yaml(self):
        """Test parsing TypeScript and generating YAML spec."""
        parser = get_parser("typescript")
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        assert len(symbols) > 0

        generator = ApiSpecGenerator()
        result = generator.generate(
            symbols=symbols,
            output_format="yaml",
            project_name="sample_project",
            language="typescript",
        )
        spec = yaml.safe_load(result)
        assert spec["project_name"] == "sample_project"
        assert spec["language"] == "typescript"
        assert len(spec["symbols"]) > 0

    def test_parse_and_generate_json(self):
        """Test parsing TypeScript and generating JSON spec."""
        parser = get_parser("typescript")
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        assert len(symbols) > 0

        generator = ApiSpecGenerator()
        result = generator.generate(
            symbols=symbols,
            output_format="json",
            project_name="sample_project",
            language="typescript",
        )
        spec = json.loads(result)
        assert spec["project_name"] == "sample_project"
        assert spec["language"] == "typescript"
        assert len(spec["symbols"]) > 0

    def test_parse_and_generate_readme(self):
        """Test parsing TypeScript and generating README."""
        parser = get_parser("typescript")
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        assert len(symbols) > 0

        generator = ReadmeGenerator()
        result = generator.generate(
            symbols=symbols,
            output_format="markdown",
            project_name="sample_project",
            language="typescript",
        )
        assert isinstance(result, str)
        assert "sample_project" in result
        assert "TypeScript" in result

    def test_full_pipeline_typescript(self):
        """Test the full documentation pipeline for TypeScript."""
        parser = get_parser("typescript")
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))

        # Generate both YAML and JSON specs
        yaml_gen = ApiSpecGenerator()
        yaml_spec = yaml_gen.generate(
            symbols=symbols,
            output_format="yaml",
            project_name="sample_project",
            language="typescript",
        )

        json_gen = ApiSpecGenerator()
        json_spec = json_gen.generate(
            symbols=symbols,
            output_format="json",
            project_name="sample_project",
            language="typescript",
        )

        # Parse both and verify consistency
        yaml_data = yaml.safe_load(yaml_spec)
        json_data = json.loads(json_spec)

        assert yaml_data["project_name"] == json_data["project_name"]
        assert yaml_data["language"] == json_data["language"]
        assert len(yaml_data["symbols"]) == len(json_data["symbols"])


class TestMixedLanguagePipeline:
    """Test documentation generation for mixed language projects."""

    def test_parse_python_and_typescript(self):
        """Test parsing both Python and TypeScript files."""
        python_parser = get_parser("python")
        python_symbols = python_parser.parse(str(SAMPLE_PYTHON))
        assert len(python_symbols) > 0

        ts_parser = get_parser("typescript")
        ts_symbols = ts_parser.parse(str(SAMPLE_TYPESCRIPT))
        assert len(ts_symbols) > 0

        # Verify different symbol types
        python_types = {s["type"] for s in python_symbols}
        ts_types = {s["type"] for s in ts_symbols}

        # Both should have some common types
        assert "function" in python_types or "class" in python_types
        assert "function" in ts_types or "class" in ts_types

    def test_generate_specs_for_both_languages(self):
        """Test generating specs for both Python and TypeScript."""
        python_parser = get_parser("python")
        python_symbols = python_parser.parse(str(SAMPLE_PYTHON))

        ts_parser = get_parser("typescript")
        ts_symbols = ts_parser.parse(str(SAMPLE_TYPESCRIPT))

        generator = ApiSpecGenerator()

        python_spec = generator.generate(
            symbols=python_symbols,
            output_format="yaml",
            project_name="mixed_project",
            language="python",
        )

        ts_spec = generator.generate(
            symbols=ts_symbols,
            output_format="yaml",
            project_name="mixed_project",
            language="typescript",
        )

        python_data = yaml.safe_load(python_spec)
        ts_data = yaml.safe_load(ts_spec)

        assert python_data["language"] == "python"
        assert ts_data["language"] == "typescript"
        assert python_data["project_name"] == ts_data["project_name"]
