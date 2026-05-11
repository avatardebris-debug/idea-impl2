"""Tests for forensic config."""

import os
import pytest
from forensic.config import get_config, ForensicConfig


class TestConfig:
    """Tests for the ForensicConfig class."""

    def test_default_values(self):
        """Test that default config values are correct."""
        config = ForensicConfig()
        assert config.db_path == "forensic.db"
        assert config.requests_per_second == 10
        assert config.max_retries == 3
        assert config.log_level == "INFO"
        assert config.batch_size == 10
        assert config.timeout == 30

    def test_env_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("FORENSIC_DB_PATH", "test.db")
        monkeypatch.setenv("FORENSIC_MAX_RETRIES", "5")
        monkeypatch.setenv("FORENSIC_LOG_LEVEL", "DEBUG")
        
        config = ForensicConfig()
        assert config.db_path == "test.db"
        assert config.max_retries == 5
        assert config.log_level == "DEBUG"

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_config_with_env(self, monkeypatch):
        """Test that get_config respects environment variables."""
        monkeypatch.setenv("FORENSIC_DB_PATH", "test_singleton.db")
        config = get_config()
        assert config.db_path == "test_singleton.db"

    def test_to_dict(self):
        """Test that to_dict returns a proper dict."""
        config = ForensicConfig()
        d = config.to_dict()
        assert isinstance(d, dict)
        assert "database" in d
        assert "rate_limiting" in d
        assert "logging" in d
        assert "importer" in d
        assert "fraud_detection" in d
