"""VAST.ai API authentication module.

Handles authentication with the VAST.ai API using API keys from
environment variables, config files, or interactive prompts.
"""

import os
import configparser
from pathlib import Path


def authenticate() -> str | None:
    """Authenticate with the VAST.ai API.

    Tries the following methods in order:
    1. VASTAI_API_KEY environment variable
    2. Saved API key in config file (~/.vastai-init/config.ini)
    3. Interactive prompt (if run in a terminal)

    Returns:
        The API key string if authentication succeeds, None otherwise.

    Raises:
        RuntimeError: If no authentication method is available.
    """
    # Method 1: Environment variable
    api_key = os.environ.get("VASTAI_API_KEY")
    if api_key and api_key.strip():
        return api_key.strip()

    # Method 2: Config file
    config_path = Path.home() / ".vastai-init" / "config.ini"
    if config_path.exists():
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            if "api" in config and "api_key" in config["api"]:
                key = config["api"]["api_key"].strip()
                if key:
                    return key
        except (configparser.Error, KeyError):
            pass

    # Method 3: Interactive prompt
    if not os.isatty(0):
        raise RuntimeError(
            "No VAST.ai API key found. Set the VASTAI_API_KEY environment "
            "variable or create a config file at ~/.vastai-init/config.ini "
            "with an [api] section containing api_key = your_key_here"
        )

    api_key = input("Enter your VAST.ai API key: ").strip()
    if not api_key:
        raise RuntimeError("API key cannot be empty.")

    # Save the key for future use
    config_dir = Path.home() / ".vastai-init"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.ini"
    if not config_path.exists():
        config = configparser.ConfigParser()
        config["api"] = {"api_key": api_key}
        with open(config_path, "w") as f:
            config.write(f)
        os.chmod(config_path, 0o600)  # Restrict permissions

    return api_key


def get_auth_headers(api_key: str) -> dict[str, str]:
    """Build HTTP headers for VAST.ai API requests.

    Args:
        api_key: The authenticated API key.

    Returns:
        Dictionary of HTTP headers including the authorization header.
    """
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def validate_api_key(api_key: str) -> bool:
    """Validate that an API key is non-empty and properly formatted.

    Args:
        api_key: The API key to validate.

    Returns:
        True if the key appears valid, False otherwise.
    """
    if not api_key or not isinstance(api_key, str):
        return False
    if not api_key.strip():
        return False
    # Basic check: API keys should be reasonably long
    if len(api_key.strip()) < 8:
        return False
    return True
