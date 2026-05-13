"""Configuration module for Video Scribe.

Loads API keys from environment variables or a .env file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Supported VLM providers
PROVIDER_GPT4O = "gpt-4o"
PROVIDER_CLAUDE = "claude"
DEFAULT_PROVIDER = PROVIDER_GPT4O

# Default .env file location
_DEFAULT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env(env_path: Optional[Path] = None) -> None:
    """Load environment variables from a .env file if it exists."""
    path = env_path or _DEFAULT_ENV_PATH
    if path.exists():
        load_dotenv(dotenv_path=path)


def get_api_key(provider: str = DEFAULT_PROVIDER) -> str:
    """Return the API key for the given provider.

    Raises:
        ValueError: If the API key is not set in the environment.
    """
    if provider == PROVIDER_GPT4O:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Set it or add it to a .env file."
            )
        return key
    elif provider == PROVIDER_CLAUDE:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Set it or add it to a .env file."
            )
        return key
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_base_url(provider: str = DEFAULT_PROVIDER) -> str:
    """Return the API base URL for the given provider."""
    if provider == PROVIDER_GPT4O:
        return "https://api.openai.com/v1"
    elif provider == PROVIDER_CLAUDE:
        return "https://api.anthropic.com/v1"
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_model(provider: str = DEFAULT_PROVIDER) -> str:
    """Return the model name for the given provider."""
    if provider == PROVIDER_GPT4O:
        return "gpt-4o"
    elif provider == PROVIDER_CLAUDE:
        return "claude-sonnet-4-20250514"
    else:
        raise ValueError(f"Unknown provider: {provider}")


# Scene detection defaults
DEFAULT_SCENE_THRESHOLD = 15.0
DEFAULT_MIN_SCENE_DURATION = 2.0

# Concurrency defaults
DEFAULT_MAX_WORKERS = 4
