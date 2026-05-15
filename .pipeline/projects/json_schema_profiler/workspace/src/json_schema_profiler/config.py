import os
import yaml
from typing import Any

DEFAULT_CONFIG = {
    "default_format": "jsonschema",
    "thresholds": {
        "null_rate": 0.10,
        "iqr_multiplier": 1.5
    }
}

def load_config() -> dict[str, Any]:
    """Load configuration from ~/.json-schema-profiler.yaml"""
    config = dict(DEFAULT_CONFIG)
    config_path = os.path.expanduser("~/.json-schema-profiler.yaml")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    config.update(user_config)
        except Exception:
            pass
            
    return config
