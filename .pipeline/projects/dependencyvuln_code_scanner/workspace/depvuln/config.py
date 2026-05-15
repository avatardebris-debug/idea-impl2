"""Configuration manager for depvuln."""
import json
import os
from typing import Any


class ConfigManager:
    """Manage depvuln configuration via a JSON config file."""

    CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".depvuln", "config.json")

    DEFAULT_CONFIG = {
        "cache_enabled": True,
        "cache_ttl": 3600,
        "cache_dir": None,
        "output_format": "text",
        "severity_threshold": "LOW",
        "osv_api_url": "https://api.osv.dev/v1/query",
        "nvd_api_url": "https://services.nvd.nist.gov/rest/json/cve/1.0/",
        "timeout": 30,
        "max_concurrent": 5,
    }

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = self.CONFIG_PATH
        self.config_path = config_path
        self.config = dict(self.DEFAULT_CONFIG)
        self._load()

    def _load(self):
        """Load config from file, merging with defaults."""
        # 1. Load global config
        if os.path.isfile(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    file_config = json.load(f)
                self.config.update(file_config)
            except (json.JSONDecodeError, OSError):
                pass
                
        # 2. Load local project config (.depvulnrc)
        local_config = os.path.join(os.getcwd(), ".depvulnrc")
        if os.path.isfile(local_config):
            try:
                # Support YAML if pyyaml is installed, fallback to JSON
                try:
                    import yaml
                    with open(local_config, "r") as f:
                        file_config = yaml.safe_load(f)
                        if file_config:
                            self.config.update(file_config)
                except ImportError:
                    with open(local_config, "r") as f:
                        file_config = json.load(f)
                    if file_config:
                        self.config.update(file_config)
            except Exception:
                pass

    def save(self):
        """Save current config to file."""
        os.makedirs(os.path.dirname(self.config_path) or ".", exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a config value."""
        self.config[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Return the current config as a dict."""
        return dict(self.config)
