import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from transcript_extractor.config import Config

class TestConfig:
    def test_default_initialization(self):
        config = Config()
        assert config.model_path is not None
        assert config.output_dir is not None
        assert config.temp_dir is not None
        assert config.api_endpoint == "local"
    
    def test_custom_initialization(self):
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
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_MODEL_PATH": "/env/model"}):
            with patch("os.path.exists", return_value=True):
                config = Config()
                assert config.model_path == "/env/model"
    
    def test_model_path_fallback_when_env_invalid(self):
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_MODEL_PATH": "/nonexistent/model"}):
            with patch("os.path.exists", return_value=False):
                config = Config()
                assert "transcript_extractor" in config.model_path
    
    def test_output_dir_from_env(self):
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_OUTPUT_DIR": "/env/output"}):
            config = Config.from_env()
            assert config.output_dir == "/env/output"
    
    def test_temp_dir_from_env(self):
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_TEMP_DIR": "/env/temp"}):
            config = Config()
            assert config.temp_dir == "/env/temp"
    
    def test_api_endpoint_from_env(self):
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_API_ENDPOINT": "https://custom.api.com"}):
            config = Config.from_env()
            assert config.api_endpoint == "https://custom.api.com"
    
    def test_api_endpoint_fallback_when_env_empty(self):
        with patch.dict(os.environ, {"TRANSCRIPT_EXTRACTOR_API_ENDPOINT": ""}):
            config = Config.from_env()
            assert config.api_endpoint == "local"
