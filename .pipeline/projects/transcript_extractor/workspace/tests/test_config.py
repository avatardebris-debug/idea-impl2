"""
Tests for Config class.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from transcript_extractor.config import Config


class TestConfig:
    """Tests for the Config class."""
    
    def test_default_initialization(self):
        """Test that default initialization works."""
        config = Config()
        assert config.model_path is not None
        assert config.output_dir is not None
        assert config.temp_dir is not None
        assert config.api_endpoint == "local"
    
    def test_custom_initialization(self):
        """Test custom initialization with provided values."""
        config = Config(
            model_path="/custom/model",
            output_dir="/custom/output",
            temp_dir="/custom/temp",
            api_endpoint="https://api.example.com",
        )
        assert config.model_path == "/custom/model"
        assert config.output_dir == "/custom/output"
        assert config.temp_dir == "/custom/temp"
        assert config.api_endpoint == "https://api.example.com"
    
    def test_model_path_from_env(self):
        """Test that model path can be set from environment variable."""
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_MODEL_PATH": "/env/model"}):
            with patch("os.path.exists", return_value=True):
                config = Config()
                assert config.model_path == "/env/model"
    
    def test_model_path_fallback_when_env_invalid(self):
        """Test that model path falls back to default when env path doesn't exist."""
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_MODEL_PATH": "/nonexistent/model"}):
            with patch("os.path.exists", return_value=False):
                config = Config()
                assert "transcript_extractor" in config.model_path
    
    def test_output_dir_from_env(self):
        """Test that output dir can be set from environment variable."""
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_OUTPUT_DIR": "/env/output"}):
            with patch("os.path.exists", return_value=True):
                config = Config()
                assert config.output_dir == "/env/output"
    
    def test_output_dir_fallback_when_env_invalid(self):
        """Test that output dir falls back to default when env path doesn't exist."""
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_OUTPUT_DIR": "/nonexistent/output"}):
            with patch("os.path.exists", return_value=False):
                config = Config()
                assert "transcript_extractor" in config.output_dir
    
    def test_temp_dir_from_env(self):
        """Test that temp dir can be set from environment variable."""
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_TEMP_DIR": "/env/temp"}):
            with patch("os.path.exists", return_value=True):
                config = Config()
                assert config.temp_dir == "/env/temp"
    
    def test_temp_dir_fallback_when_env_invalid(self):
        """Test that temp dir falls back to default when env path doesn't exist."""
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_TEMP_DIR": "/nonexistent/temp"}):
            with patch("os.path.exists", return_value=False):
                config = Config()
                assert "transcript_extractor" in config.temp_dir
    
    def test_api_endpoint_from_env(self):
        """Test that API endpoint can be set from environment variable."""
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_API_ENDPOINT": "https://custom.api.com"}):
            config = Config()
            assert config.api_endpoint == "https://custom.api.com"
    
    def test_api_endpoint_fallback_when_env_empty(self):
        """Test that API endpoint falls back to default when env is empty."""
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_API_ENDPOINT": ""}):
            config = Config()
            assert config.api_endpoint == "local"
    
    def test_get_model_path(self):
        """Test get_model_path method."""
        config = Config()
        assert config.get_model_path() == config.model_path
    
    def test_get_output_dir(self):
        """Test get_output_dir method."""
        config = Config()
        assert config.get_output_dir() == config.output_dir
    
    def test_get_temp_dir(self):
        """Test get_temp_dir method."""
        config = Config()
        assert config.get_temp_dir() == config.temp_dir
    
    def test_get_api_endpoint(self):
        """Test get_api_endpoint method."""
        config = Config()
        assert config.get_api_endpoint() == config.api_endpoint
    
    def test_get_model_path_with_custom(self):
        """Test get_model_path with custom model path."""
        config = Config(model_path="/custom/model")
        assert config.get_model_path() == "/custom/model"
    
    def test_get_output_dir_with_custom(self):
        """Test get_output_dir with custom output dir."""
        config = Config(output_dir="/custom/output")
        assert config.get_output_dir() == "/custom/output"
    
    def test_get_temp_dir_with_custom(self):
        """Test get_temp_dir with custom temp dir."""
        config = Config(temp_dir="/custom/temp")
        assert config.get_temp_dir() == "/custom/temp"
    
    def test_get_api_endpoint_with_custom(self):
        """Test get_api_endpoint with custom API endpoint."""
        config = Config(api_endpoint="https://custom.api.com")
        assert config.get_api_endpoint() == "https://custom.api.com"
