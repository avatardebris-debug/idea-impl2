"""Tests for the DocsAI parsers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Add workspace to path
WORKSPACE = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE))

from docsai.parsers.python_parser import PythonParser
from docsai.parsers.typescript_parser import TypeScriptParser
from docsai.parsers import get_parser, _PARSER_REGISTRY


SAMPLE_PYTHON = WORKSPACE / "tests" / "sample_project" / "sample_python.py"
SAMPLE_TYPESCRIPT = WORKSPACE / "tests" / "sample_project" / "sample_typescript.ts"


class TestPythonParser:
    """Tests for the Python parser."""

    @pytest.fixture
    def parser(self) -> PythonParser:
        return PythonParser()

    def test_parse_returns_symbols(self, parser: PythonParser):
        """Test that parse returns a list of symbol dicts."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        assert isinstance(symbols, list)
        assert len(symbols) > 0

    def test_parse_contains_expected_functions(self, parser: PythonParser):
        """Test that expected functions are found."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        names = [s["name"] for s in symbols]
        assert "greet" in names
        assert "compute_sum" in names

    def test_parse_contains_expected_class(self, parser: PythonParser):
        """Test that expected class is found."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        names = [s["name"] for s in symbols]
        assert "Calculator" in names

    def test_symbol_structure(self, parser: PythonParser):
        """Test that each symbol has the required fields."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        required_keys = {"name", "kind", "params", "return_type", "docstring", "line_number"}
        for symbol in symbols:
            assert required_keys.issubset(symbol.keys()), f"Missing keys in {symbol}"

    def test_function_params_extracted(self, parser: PythonParser):
        """Test that function parameters are extracted."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        greet = next(s for s in symbols if s["name"] == "greet")
        assert len(greet["params"]) == 1
        assert greet["params"][0]["name"] == "name"
        assert greet["params"][0]["type"] == "str"

    def test_function_return_type(self, parser: PythonParser):
        """Test that return types are extracted."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        greet = next(s for s in symbols if s["name"] == "greet")
        assert greet["return_type"] == "str"

    def test_class_method_params(self, parser: PythonParser):
        """Test that class method parameters are extracted."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        add_method = next(s for s in symbols if s["name"] == "add")
        assert len(add_method["params"]) == 1
        assert add_method["params"][0]["name"] == "number"

    def test_docstrings_extracted(self, parser: PythonParser):
        """Test that docstrings are extracted."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        greet = next(s for s in symbols if s["name"] == "greet")
        assert "Greet a person by name" in greet["docstring"]

    def test_private_symbols_excluded(self, parser: PythonParser):
        """Test that private symbols (starting with _) are excluded."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        names = [s["name"] for s in symbols]
        assert "_private" not in names

    def test_kind_field_correct(self, parser: PythonParser):
        """Test that kind field is set correctly."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        for symbol in symbols:
            assert symbol["kind"] in ("function", "class", "method")

    def test_line_numbers_present(self, parser: PythonParser):
        """Test that line numbers are present and positive."""
        symbols = parser.parse(str(SAMPLE_PYTHON))
        for symbol in symbols:
            assert isinstance(symbol["line_number"], int)
            assert symbol["line_number"] > 0


class TestTypeScriptParser:
    """Tests for the TypeScript parser."""

    @pytest.fixture
    def parser(self) -> TypeScriptParser:
        return TypeScriptParser()

    def test_parse_returns_symbols(self, parser: TypeScriptParser):
        """Test that parse returns a list of symbol dicts."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        assert isinstance(symbols, list)
        assert len(symbols) > 0

    def test_parse_contains_expected_functions(self, parser: TypeScriptParser):
        """Test that expected functions are found."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        names = [s["name"] for s in symbols]
        assert "greet" in names
        assert "computeSum" in names

    def test_parse_contains_expected_class(self, parser: TypeScriptParser):
        """Test that expected class is found."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        names = [s["name"] for s in symbols]
        assert "Calculator" in names

    def test_parse_contains_interface(self, parser: TypeScriptParser):
        """Test that interfaces are found."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        names = [s["name"] for s in symbols]
        assert "Point" in names
        interfaces = [s for s in symbols if s["kind"] == "interface"]
        assert len(interfaces) > 0

    def test_symbol_structure(self, parser: TypeScriptParser):
        """Test that each symbol has the required fields."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        required_keys = {"name", "kind", "params", "return_type", "docstring", "line_number"}
        for symbol in symbols:
            assert required_keys.issubset(symbol.keys()), f"Missing keys in {symbol}"

    def test_function_params_extracted(self, parser: TypeScriptParser):
        """Test that function parameters are extracted."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        greet = next(s for s in symbols if s["name"] == "greet")
        assert len(greet["params"]) == 1
        assert greet["params"][0]["name"] == "name"
        assert "string" in greet["params"][0]["type"]

    def test_function_return_type(self, parser: TypeScriptParser):
        """Test that return types are extracted."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        greet = next(s for s in symbols if s["name"] == "greet")
        assert "string" in greet["return_type"]

    def test_class_method_params(self, parser: TypeScriptParser):
        """Test that class method parameters are extracted."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        add_method = next(s for s in symbols if s["name"] == "add")
        assert len(add_method["params"]) == 1
        assert add_method["params"][0]["name"] == "number"

    def test_docstrings_extracted(self, parser: TypeScriptParser):
        """Test that JSDoc comments are extracted."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        greet = next(s for s in symbols if s["name"] == "greet")
        assert "Greet a person by name" in greet["docstring"]

    def test_kind_field_correct(self, parser: TypeScriptParser):
        """Test that kind field is set correctly."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        kinds = set(s["kind"] for s in symbols)
        assert kinds.issubset({"function", "class", "method", "interface", "type", "enum", "variable", "field"})

    def test_line_numbers_present(self, parser: TypeScriptParser):
        """Test that line numbers are present and positive."""
        symbols = parser.parse(str(SAMPLE_TYPESCRIPT))
        for symbol in symbols:
            assert isinstance(symbol["line_number"], int)
            assert symbol["line_number"] > 0


class TestParserRegistry:
    """Tests for the parser registry."""

    def test_get_python_parser(self):
        """Test getting a Python parser."""
        parser = get_parser("python")
        assert isinstance(parser, PythonParser)

    def test_get_typescript_parser(self):
        """Test getting a TypeScript parser."""
        parser = get_parser("typescript")
        assert isinstance(parser, TypeScriptParser)

    def test_get_tsx_parser(self):
        """Test getting a TSX parser (maps to TypeScriptParser)."""
        parser = get_parser("tsx")
        assert isinstance(parser, TypeScriptParser)

    def test_get_unsupported_language_raises(self):
        """Test that unsupported language raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported language"):
            get_parser("rust")

    def test_registry_contains_expected_languages(self):
        """Test that registry contains expected languages."""
        assert "python" in _PARSER_REGISTRY
        assert "typescript" in _PARSER_REGISTRY
        assert "tsx" in _PARSER_REGISTRY
