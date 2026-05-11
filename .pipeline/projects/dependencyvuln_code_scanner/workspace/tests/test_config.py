"""Tests for configuration management."""
import json
import os
import tempfile
import pytest
from depvuln.config import ConfigManager


class TestConfigManager:
    """Test suite for ConfigManager."""

    def setup_method(self):
        """Create a temporary config file for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "depvuln_config.json")
        # Patch the config path
        self.original_config_path = ConfigManager.CONFIG_PATH
        ConfigManager.CONFIG_PATH = self.config_path
        self.config = ConfigManager()

    def teardown_method(self):
        """Clean up temporary files."""
        ConfigManager.CONFIG_PATH = self.original_config_path
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_default_config(self):
        """Test that default config values are correct."""
        assert self.config.get("output_format") == "text"
        assert self.config.get("cache_enabled") is True
        assert self.config.get("severity_threshold") == "LOW"
        assert self.config.get("cache_ttl") == 3600

    def test_set_and_get(self):
        """Test setting and getting config values."""
        self.config.set("output_format", "json")
        assert self.config.get("output_format") == "json"

    def test_set_and_save(self):
        """Test that set() persists to file."""
        self.config.set("output_format", "html")
        self.config.save()
        
        # Reload config
        config2 = ConfigManager()
        assert config2.get("output_format") == "html"

    def test_to_dict(self):
        """Test that to_dict returns all config values."""
        d = self.config.to_dict()
        assert isinstance(d, dict)
        assert "output_format" in d
        assert "cache_enabled" in d
        assert "severity_threshold" in d

    def test_set_nonexistent_key(self):
        """Test setting a key that doesn't exist in defaults."""
        self.config.set("custom_key", "custom_value")
        assert self.config.get("custom_key") == "custom_value"

    def test_get_nonexistent_key_returns_none(self):
        """Test getting a key that doesn't exist."""
        assert self.config.get("nonexistent_key") is None

    def test_save_creates_file(self):
        """Test that save() creates the config file."""
        self.config.set("output_format", "json")
        self.config.save()
        assert os.path.exists(self.config_path)

    def test_load_existing_config(self):
        """Test loading an existing config file."""
        # Create config file manually
        with open(self.config_path, "w") as f:
            json.dump({"output_format": "html", "cache_enabled": False}, f)
        
        # Reload config
        config2 = ConfigManager()
        assert config2.get("output_format") == "html"
        assert config2.get("cache_enabled") is False

    def test_config_path_default(self):
        """Test that default config path is in home directory."""
        assert "~/.depvuln" in self.original_config_path
