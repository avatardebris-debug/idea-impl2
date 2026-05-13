"""Tests for the DocsAI LLM interface."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add workspace to path
WORKSPACE = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE))

from docsai.llm_interface import (
    LLMInterface,
    build_prompt,
    format_symbols_for_llm,
    generate_readme_content,
)


class TestBuildPrompt:
    """Tests for the build_prompt function."""

    def test_build_prompt_includes_symbols(self):
        """Test that build_prompt includes symbol data."""
        symbols = [
            {"name": "greet", "kind": "function", "params": [], "return_type": "str", "docstring": "Greet someone.", "line_number": 1},
        ]
        prompt = build_prompt(symbols, "python")
        assert "greet" in prompt
        assert "function" in prompt

    def test_build_prompt_includes_language(self):
        """Test that build_prompt includes language info."""
        symbols = []
        prompt = build_prompt(symbols, "typescript")
        assert "typescript" in prompt

    def test_build_prompt_includes_instructions(self):
        """Test that build_prompt includes instructions."""
        symbols = []
        prompt = build_prompt(symbols, "python")
        assert "instructions" in prompt.lower() or "generate" in prompt.lower()

    def test_build_prompt_empty_symbols(self):
        """Test that build_prompt handles empty symbols."""
        prompt = build_prompt([], "python")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestFormatSymbolsForLLM:
    """Tests for the format_symbols_for_llm function."""

    def test_format_symbols_returns_string(self):
        """Test that format_symbols_for_llm returns a string."""
        symbols = [
            {"name": "greet", "kind": "function", "params": [], "return_type": "str", "docstring": "Greet someone.", "line_number": 1},
        ]
        result = format_symbols_for_llm(symbols)
        assert isinstance(result, str)

    def test_format_symbols_includes_name(self):
        """Test that format_symbols_for_llm includes symbol names."""
        symbols = [
            {"name": "greet", "kind": "function", "params": [], "return_type": "str", "docstring": "Greet someone.", "line_number": 1},
        ]
        result = format_symbols_for_llm(symbols)
        assert "greet" in result

    def test_format_symbols_includes_kind(self):
        """Test that format_symbols_for_llm includes symbol kinds."""
        symbols = [
            {"name": "greet", "kind": "function", "params": [], "return_type": "str", "docstring": "Greet someone.", "line_number": 1},
        ]
        result = format_symbols_for_llm(symbols)
        assert "function" in result

    def test_format_symbols_empty_list(self):
        """Test that format_symbols_for_llm handles empty list."""
        result = format_symbols_for_llm([])
        assert isinstance(result, str)


class TestGenerateReadmeContent:
    """Tests for the generate_readme_content function."""

    @patch("docsai.llm_interface.LLMInterface")
    def test_generate_readme_content_calls_llm(self, mock_llm_class):
        """Test that generate_readme_content calls the LLM interface."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate.return_value = "# Generated README"

        symbols = [
            {"name": "greet", "kind": "function", "params": [], "return_type": "str", "docstring": "Greet someone.", "line_number": 1},
        ]
        result = generate_readme_content(symbols, "python", "test_project")
        mock_llm.generate.assert_called_once()

    @patch("docsai.llm_interface.LLMInterface")
    def test_generate_readme_content_returns_string(self, mock_llm_class):
        """Test that generate_readme_content returns a string."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate.return_value = "# Generated README"

        symbols = []
        result = generate_readme_content(symbols, "python", "test_project")
        assert isinstance(result, str)

    @patch("docsai.llm_interface.LLMInterface")
    def test_generate_readme_content_with_empty_symbols(self, mock_llm_class):
        """Test that generate_readme_content handles empty symbols."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate.return_value = "# Generated README"

        result = generate_readme_content([], "python", "test_project")
        assert isinstance(result, str)


class TestLLMInterface:
    """Tests for the LLMInterface class."""

    @patch("docsai.llm_interface.LLMInterface._get_api_key")
    def test_init_sets_api_key(self, mock_get_key):
        """Test that __init__ sets the API key."""
        mock_get_key.return_value = "test_key"
        interface = LLMInterface()
        assert interface.api_key == "test_key"

    @patch("docsai.llm_interface.LLMInterface._get_api_key")
    def test_init_sets_model(self, mock_get_key):
        """Test that __init__ sets the model."""
        mock_get_key.return_value = "test_key"
        interface = LLMInterface()
        assert interface.model is not None

    @patch("docsai.llm_interface.LLMInterface._get_api_key")
    def test_generate_returns_string(self, mock_get_key):
        """Test that generate returns a string."""
        mock_get_key.return_value = "test_key"
        interface = LLMInterface()
        # Mock the actual API call
        with patch.object(interface, "_call_api") as mock_call:
            mock_call.return_value = "Test response"
            result = interface.generate("Test prompt")
            assert isinstance(result, str)

    @patch("docsai.llm_interface.LLMInterface._get_api_key")
    def test_generate_calls_api(self, mock_get_key):
        """Test that generate calls the API."""
        mock_get_key.return_value = "test_key"
        interface = LLMInterface()
        with patch.object(interface, "_call_api") as mock_call:
            interface.generate("Test prompt")
            mock_call.assert_called_once()

    def test_get_api_key_returns_string(self):
        """Test that _get_api_key returns a string."""
        interface = LLMInterface()
        # This may return None if no key is set, but should be a string
        key = interface._get_api_key()
        assert isinstance(key, str) or key is None
