"""Tests for the DocsAI config module."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add workspace to path
WORKSPACE = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE))

from docsai.core.config import (
    load_config,
    DEFAULT_CONFIG_PATH,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_LANGUAGES,
)


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_returns_dict(self):
        """Test that load_config returns a dict."""
        config = load_config()
        assert isinstance(config, dict)

    def test_load_config_has_expected_keys(self):
        """Test that load_config has expected keys."""
        config = load_config()
        assert "output_format" in config
        assert "languages" in config
        assert "output_path" in config

    def test_load_config_default_values(self):
        """Test that load_config returns defaults when no config file exists."""
        config = load_config()
        assert config["output_format"] == DEFAULT_OUTPUT_FORMAT
        assert config["languages"] == DEFAULT_LANGUAGES
        assert config["output_path"] == DEFAULT_OUTPUT_PATH

    def test_load_config_with_nonexistent_file(self):
        """Test that load_config returns defaults for nonexistent file."""
        config = load_config(config_path="/nonexistent/path/docsai.yaml")
        assert config["output_format"] == DEFAULT_OUTPUT_FORMAT
        assert config["languages"] == DEFAULT_LANGUAGES

    @patch("pathlib.Path.exists")
    def test_load_config_with_existing_file(self, mock_exists):
        """Test that load_config reads from an existing file."""
        mock_exists.return_value = True
        mock_config = {
            "output_format": "json",
            "languages": ["typescript"],
            "output_path": "/tmp/output.json",
        }
        with patch("builtins.open", patch.mock_open(read_data="output_format: json\nlanguages:\n  - typescript\noutput_path: /tmp/output.json\n")):
            config = load_config(config_path="/fake/docsai.yaml")
            assert config["output_format"] == "json"
            assert config["languages"] == ["typescript"]
            assert config["output_path"] == "/tmp/output.json"

    def test_load_config_with_empty_file(self):
        """Test that load_config handles empty config file."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", patch.mock_open(read_data="")):
                config = load_config(config_path="/fake/docsai.yaml")
                # Should return defaults since empty file yields None from yaml.safe_load
                assert config["output_format"] == DEFAULT_OUTPUT_FORMAT

    def test_load_config_with_partial_file(self):
        """Test that load_config handles partial config file."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", patch.mock_open(read_data="output_format: xml\n")):
                config = load_config(config_path="/fake/docsai.yaml")
                assert config["output_format"] == "xml"
                assert config["languages"] == DEFAULT_LANGUAGES  # defaults
                assert config["output_path"] == DEFAULT_OUTPUT_PATH  # defaults

    def test_load_config_default_path(self):
        """Test that load_config uses default path when no path provided."""
        with patch("pathlib.Path.exists", return_value=False):
            config = load_config()
            assert isinstance(config, dict)
