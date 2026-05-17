"""Configuration loader for DocsAI.

Loads and validates the docsai.yaml configuration file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


DEFAULT_CONFIG_PATH = "docsai.yaml"
DEFAULT_OUTPUT_FORMAT = "yaml"
DEFAULT_OUTPUT_PATH = "./docsai_output/api_spec.yaml"
DEFAULT_LANGUAGES = ["python", "typescript"]


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load the DocsAI configuration from a YAML file.

    Args:
        config_path: Path to the docsai.yaml file.
                     If None, defaults to 'docsai.yaml' in the current directory.

    Returns:
        A dictionary with keys: output_format, languages, output_path.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    path = Path(config_path)
    if not path.exists():
        # Return defaults if config file doesn't exist
        return {
            "output_format": DEFAULT_OUTPUT_FORMAT,
            "languages": DEFAULT_LANGUAGES,
            "output_path": DEFAULT_OUTPUT_PATH,
        }

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    config: Dict[str, Any] = {}
    config["output_format"] = raw.get("output_format", DEFAULT_OUTPUT_FORMAT)
    config["languages"] = raw.get("languages", DEFAULT_LANGUAGES)
    config["output_path"] = raw.get("output_path", DEFAULT_OUTPUT_PATH)

    return config
