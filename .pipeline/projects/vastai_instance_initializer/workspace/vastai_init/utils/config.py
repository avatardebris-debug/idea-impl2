"""Configuration utilities for the VAST.ai Instance Initializer.

Provides functions for loading, saving, and managing the application
configuration stored in ~/.vastai-init/config.ini.
"""

import configparser
import os
from pathlib import Path


DEFAULT_CONFIG_PATH = Path.home() / ".vastai-init" / "config.ini"


def get_config_path() -> Path:
    """Get the path to the configuration file.

    Returns:
        The path to the config file.
    """
    return DEFAULT_CONFIG_PATH


def load_config(config_path: Path | None = None) -> configparser.ConfigParser:
    """Load the application configuration.

    Args:
        config_path: Path to the config file. Defaults to ~/.vastai-init/config.ini.

    Returns:
        The loaded ConfigParser object.
    """
    path = config_path or get_config_path()
    config = configparser.ConfigParser()

    if path.exists():
        config.read(path)

    # Ensure default sections exist
    if "api" not in config:
        config["api"] = {}
    if "defaults" not in config:
        config["defaults"] = {
            "timeout": "300",
            "poll_interval": "10",
            "storage": "50GB",
        }

    return config


def save_config(config: configparser.ConfigParser, config_path: Path | None = None) -> None:
    """Save the application configuration.

    Args:
        config: The ConfigParser object to save.
        config_path: Path to save the config to. Defaults to ~/.vastai-init/config.ini.
    """
    path = config_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        config.write(f)

    # Restrict permissions
    os.chmod(path, 0o600)


def get_api_key(config: configparser.ConfigParser | None = None) -> str | None:
    """Get the API key from the configuration.

    Args:
        config: The ConfigParser object. If None, loads from default path.

    Returns:
        The API key string, or None if not configured.
    """
    if config is None:
        config = load_config()

    if "api" in config and config["api"].get("api_key"):
        return config["api"]["api_key"].strip()
    return None


def set_api_key(api_key: str, config: configparser.ConfigParser | None = None) -> configparser.ConfigParser:
    """Set the API key in the configuration.

    Args:
        api_key: The API key to save.
        config: The ConfigParser object. If None, loads from default path.

    Returns:
        The updated ConfigParser object.
    """
    if config is None:
        config = load_config()

    config["api"]["api_key"] = api_key
    save_config(config)
    return config


def get_default_setting(key: str, config: configparser.ConfigParser | None = None) -> str | None:
    """Get a default setting from the configuration.

    Args:
        key: The setting key to look up.
        config: The ConfigParser object. If None, loads from default path.

    Returns:
        The setting value, or None if not found.
    """
    if config is None:
        config = load_config()

    if "defaults" in config and key in config["defaults"]:
        return config["defaults"][key]
    return None
