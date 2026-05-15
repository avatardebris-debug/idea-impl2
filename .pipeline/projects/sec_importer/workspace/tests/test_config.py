"""Tests for SEC Importer config."""

import pytest
import os
import tempfile
from sec_importer.config import Config


class TestConfig:
    def test_default_config(self):
        config = Config()
        assert config.db_path == "sec_importer.db"
        assert config.requests_per_second == 10
        assert config.max_retries == 3
        assert config.timeout == 30

    def test_config_from_env(self, monkeypatch):
        monkeypatch.setenv("SEC_IMPORTER_DB_PATH", "/tmp/test.db")
        monkeypatch.setenv("SEC_IMPORTER_REQUESTS_PER_SECOND", "5")
        config = Config()
        assert config.db_path == "/tmp/test.db"
        assert config.requests_per_second == 5

    def test_config_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("database:\n  db_path: /tmp/test.yaml.db\nrate_limiting:\n  requests_per_second: 15\n")
            f.flush()
        
        try:
            config = Config.from_file(f.name)
            assert config.db_path == "/tmp/test.yaml.db"
            assert config.requests_per_second == 15
        finally:
            os.unlink(f.name)

    def test_config_merge(self):
        config = Config()
        config.db_path = "/tmp/merged.db"
        config.requests_per_second = 20
        assert config.db_path == "/tmp/merged.db"
        assert config.requests_per_second == 20
