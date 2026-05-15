"""Configuration loader for SEC Importer.

Loads settings from config.yaml with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

import yaml


# Default configuration values
DEFAULTS = {
    "database": {"db_path": "sec_importer.db"},
    "rate_limiting": {
        "requests_per_second": 10,
        "delay": 0.1,
        "max_retries": 3,
        "base_backoff": 1.0,
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    },
    "importer": {
        "batch_size": 10,
        "timeout": 30,
    },
}


class Config:
    """Configuration class that loads from YAML with fallback defaults."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize config, loading from YAML file or using defaults.

        Args:
            config_path: Path to config.yaml. If None, looks in current dir.
        """
        self._data = {}
        self._load_defaults()

        if config_path is None:
            # Try common locations
            candidates = [
                "config.yaml",
                str(Path(__file__).parent.parent.parent / "config.yaml"),
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    config_path = candidate
                    break

        if config_path and os.path.exists(config_path):
            self._load_file(config_path)

        # Load from environment variables last so they override file settings
        self._load_from_env()

    def _load_defaults(self):
        """Apply default configuration values."""
        self._data = {}
        for section, values in DEFAULTS.items():
            self._data[section] = dict(values)

    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Database path
        env_db_path = os.environ.get("SEC_IMPORTER_DB_PATH")
        if env_db_path:
            self._data["database"]["db_path"] = env_db_path

        # Rate limiting
        env_rps = os.environ.get("SEC_IMPORTER_REQUESTS_PER_SECOND")
        if env_rps:
            self._data["rate_limiting"]["requests_per_second"] = int(env_rps)

    def _load_file(self, path: str):
        """Load configuration from a YAML file, merging with defaults."""
        with open(path, "r") as f:
            file_data = yaml.safe_load(f) or {}

        for section, values in file_data.items():
            if isinstance(values, dict) and section in self._data:
                self._data[section].update(values)
            elif section not in self._data:
                self._data[section] = values

    @property
    def db_path(self) -> str:
        """Get database path."""
        return self._data.get("database", {}).get("db_path", "sec_importer.db")

    @db_path.setter
    def db_path(self, value: str):
        """Set database path."""
        self._data["database"]["db_path"] = value

    @property
    def requests_per_second(self) -> int:
        """Get rate limit: requests per second."""
        return self._data.get("rate_limiting", {}).get("requests_per_second", 10)

    @requests_per_second.setter
    def requests_per_second(self, value: int):
        """Set rate limit."""
        self._data["rate_limiting"]["requests_per_second"] = value

    @property
    def rate_limit_delay(self) -> float:
        """Get delay between requests in seconds."""
        return self._data.get("rate_limiting", {}).get("delay", 0.1)

    @property
    def max_retries(self) -> int:
        """Get maximum number of retries."""
        return self._data.get("rate_limiting", {}).get("max_retries", 3)

    @property
    def base_backoff(self) -> float:
        """Get base backoff time in seconds."""
        return self._data.get("rate_limiting", {}).get("base_backoff", 1.0)

    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self._data.get("logging", {}).get("level", "INFO")

    @property
    def log_format(self) -> str:
        """Get logging format string."""
        return self._data.get("logging", {}).get(
            "format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

    @property
    def batch_size(self) -> int:
        """Get batch size for imports."""
        return self._data.get("importer", {}).get("batch_size", 10)

    @property
    def timeout(self) -> int:
        """Get HTTP timeout in seconds."""
        return self._data.get("importer", {}).get("timeout", 30)

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from a YAML file.

        Args:
            config_path: Path to config.yaml.

        Returns:
            Config instance loaded from the file.
        """
        return cls(config_path=config_path)

    def to_dict(self) -> dict:
        """Return the full configuration as a dictionary."""
        return dict(self._data)
