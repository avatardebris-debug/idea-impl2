"""Configuration loader for the dropshipping environment."""

from __future__ import annotations

import pathlib
from typing import Any, Dict

import yaml


def load_settings(config_path: str | None = None) -> Dict[str, Any]:
    """Load settings from YAML config file.

    Args:
        config_path: Path to settings.yaml. Defaults to config/settings.yaml
            relative to the project root.

    Returns:
        Dictionary of configuration values.
    """
    if config_path is None:
        # Navigate to the project root (three levels up from this file)
        _project_root = pathlib.Path(__file__).resolve().parent.parent.parent
        config_path = _project_root / "config" / "settings.yaml"

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def get_env_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract environment-specific parameters from config."""
    return {
        "episode_length": config["env"]["episode_length"],
        "n_competitors": config["env"]["n_competitors"],
        "n_consumers": config["env"]["n_consumers"],
        "initial_budget": config["env"]["initial_budget"],
        "max_inventory": config["env"]["max_inventory"],
    }


def get_market_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract market-specific parameters from config."""
    return {
        "base_conversion_rate": config["market"]["base_conversion_rate"],
        "ad_effectiveness": config["market"]["ad_effectiveness"],
        "competition_intensity": config["market"]["competition_intensity"],
    }
