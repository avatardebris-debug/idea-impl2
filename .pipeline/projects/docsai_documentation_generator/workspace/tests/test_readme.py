"""Tests for the DocsAI README generator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

# Add workspace to path
WORKSPACE = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE))

from docsai.generators.readme import (
    READMEGenerator,
    load_template,
    render_readme,
)


TEMPLATE_DIR = WORKSPACE / "docsai" / "generators" / "readme_templates"


class TestLoadTemplate:
    """Tests for the load_template function."""

    def test_load_template_returns_string(self):
        """Test that load_template returns a string."""
        template = load_template()
        assert isinstance(template, str)

    def test_load_template_contains_expected_sections(self):
        """Test that load_template contains expected sections."""
        template = load_template()
        assert "project_name" in template
        assert "language" in template
        assert "symbols" in template

    def test_load_template_contains_markdown_formatting(self):
        """Test that load_template contains markdown formatting."""
        template = load_template()
        assert "# " in template
        assert "## " in template
        assert "- " in template


class TestRenderReadme:
    """Tests for the render_readme function."""

    def test_render_readme_returns_string(self):
        """Test that render_readme returns a string."""
        symbols = [
            {"name": "greet", "kind": "function", "params": [], "return_type": "str", "docstring": "Greet someone.", "line_number": 1},
        ]
        result = render_readme(symbols, "python", "test_project")
        assert isinstance(result, str)

    def test_render_readme_contains_project_name(self):
        """Test that render_readme contains project name."""
        symbols = []
        result = render_readme(symbols, "python", "test_project")
        assert "test_project" in result

    def test_render_readme_contains_language(self):
        """Test that render_readme contains language info."""
        symbols = []
        result = render_readme(symbols, "python", "test_project")
        assert "Python" in result

    def test_render_readme_contains_symbols(self):
        """Test that render_readme contains symbol info."""
        symbols = [
            {"name": "greet", "kind": "function", "params": [], "return_type": "str", "docstring": "Greet someone.", "line_number": 1},
        ]
        result = render_readme(symbols, "python", "test_project")
        assert "greet" in result

    def test_render_readme_empty_symbols(self):
        """Test that render_readme handles empty symbols."""
        result = render_readme([], "python", "test_project")
        assert isinstance(result, str)
        assert "test_project" in result

    def test_render_readme_contains_markdown(self):
        """Test that render_readme contains markdown formatting."""
        symbols = []
        result = render_readme(symbols, "python", "test_project")
        assert "# " in result
        assert "## " in result


class TestREADMEGenerator:
    """Tests for the READMEGenerator class."""

    def test_generate_returns_string(self):
        """Test that generate returns a string."""
        generator = READMEGenerator()
        symbols = [
            {"name": "greet", "kind": "function", "params": [], "return_type": "str", "docstring": "Greet someone.", "line_number": 1},
        ]
        result = generator.generate(
            symbols=symbols,
            output_format="markdown",
            project_name="test_project",
            language="python",
        )
        assert isinstance(result, str)

    def test_generate_contains_project_name(self):
        """Test that generate contains project name."""
        generator = READMEGenerator()
        result = generator.generate(
            symbols=[],
            output_format="markdown",
            project_name="test_project",
            language="python",
        )
        assert "test_project" in result

    def test_generate_contains_language(self):
        """Test that generate contains language info."""
        generator = READMEGenerator()
        result = generator.generate(
            symbols=[],
            output_format="markdown",
            project_name="test_project",
            language="python",
        )
        assert "Python" in result

    def test_generate_contains_symbols(self):
        """Test that generate contains symbol info."""
        generator = READMEGenerator()
        symbols = [
            {"name": "greet", "kind": "function", "params": [], "return_type": "str", "docstring": "Greet someone.", "line_number": 1},
        ]
        result = generator.generate(
            symbols=symbols,
            output_format="markdown",
            project_name="test_project",
            language="python",
        )
        assert "greet" in result

    def test_generate_empty_symbols(self):
        """Test that generate handles empty symbols."""
        generator = READMEGenerator()
        result = generator.generate(
            symbols=[],
            output_format="markdown",
            project_name="test_project",
            language="python",
        )
        assert isinstance(result, str)
        assert "test_project" in result

    def test_generate_default_project_name(self):
        """Test that generate uses default project name."""
        generator = READMEGenerator()
        result = generator.generate(
            symbols=[],
            output_format="markdown",
        )
        assert "unknown" in result

    def test_generate_default_language(self):
        """Test that generate uses default language."""
        generator = READMEGenerator()
        result = generator.generate(
            symbols=[],
            output_format="markdown",
        )
        assert "unknown" in result

    def test_generate_markdown_format(self):
        """Test that generate produces markdown output."""
        generator = READMEGenerator()
        result = generator.generate(
            symbols=[],
            output_format="markdown",
            project_name="test_project",
            language="python",
        )
        assert "# " in result
        assert "## " in result

    def test_generate_inherits_from_base_generator(self):
        """Test that READMEGenerator inherits from BaseGenerator."""
        from docsai.generators.base import BaseGenerator
        generator = READMEGenerator()
        assert isinstance(generator, BaseGenerator)
