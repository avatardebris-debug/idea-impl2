"""Configuration module for YouTube Workflow Tool.

Handles configuration loading from files, environment variables, and dictionaries.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG = {
    "min_tags": 5,
    "max_tags": 15,
    "min_hashtags": 3,
    "max_hashtags": 10,
    "min_title_length": 10,
    "max_title_length": 100,
    "min_description_length": 100,
    "default_niche": "general",
    "default_tone": "informative",
    "score_weights": {
        "title": 0.35,
        "description": 0.25,
        "tags": 0.25,
        "hashtags": 0.15,
    },
}


@dataclass
class Config:
    """Configuration for the YouTube Workflow Tool.

    Attributes:
        min_tags: Minimum number of tags to generate.
        max_tags: Maximum number of tags to generate.
        min_hashtags: Minimum number of hashtags to generate.
        max_hashtags: Maximum number of hashtags to generate.
        min_title_length: Minimum title length in characters.
        max_title_length: Maximum title length in characters.
        min_description_length: Minimum description length in characters.
        default_niche: Default content niche.
        default_tone: Default content tone.
        score_weights: Weights for metadata scoring components.
    """

    min_tags: int = 5
    max_tags: int = 15
    min_hashtags: int = 3
    max_hashtags: int = 10
    min_title_length: int = 10
    max_title_length: int = 100
    min_description_length: int = 100
    default_niche: str = "general"
    default_tone: str = "informative"
    score_weights: Dict[str, float] = field(default_factory=lambda: {
        "title": 0.35,
        "description": 0.25,
        "tags": 0.25,
        "hashtags": 0.15,
    })

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary, preserving defaults for missing keys."""
        merged = DEFAULT_CONFIG.copy()
        merged.update(data)
        return cls(**merged)

    @classmethod
    def from_file(cls, filepath: str) -> "Config":
        """Load Config from JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_env(cls) -> "Config":
        """Load Config from environment variables.

        Environment variables should be prefixed with YW_ (e.g., YW_MIN_TAGS).
        """
        env_map = {
            "min_tags": "YW_MIN_TAGS",
            "max_tags": "YW_MAX_TAGS",
            "min_hashtags": "YW_MIN_HASHTAGS",
            "max_hashtags": "YW_MAX_HASHTAGS",
            "min_title_length": "YW_MIN_TITLE_LENGTH",
            "max_title_length": "YW_MAX_TITLE_LENGTH",
            "min_description_length": "YW_MIN_DESCRIPTION_LENGTH",
            "default_niche": "YW_DEFAULT_NICHE",
            "default_tone": "YW_DEFAULT_TONE",
        }

        data: Dict[str, Any] = {}
        for key, env_var in env_map.items():
            value = os.getenv(env_var)
            if value is not None:
                if key in ["min_tags", "max_tags", "min_hashtags", "max_hashtags",
                          "min_title_length", "max_title_length", "min_description_length"]:
                    data[key] = int(value)
                else:
                    data[key] = value

        return cls.from_dict(data)

    @classmethod
    def load(cls, filepath: Optional[str] = None) -> "Config":
        """Load Config from file or environment.

        Args:
            filepath: Optional path to JSON config file. If not provided,
                     loads from environment variables.

        Returns:
            Config instance.
        """
        if filepath:
            return cls.from_file(filepath)
        return cls.from_env()

    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to dictionary."""
        return {
            "min_tags": self.min_tags,
            "max_tags": self.max_tags,
            "min_hashtags": self.min_hashtags,
            "max_hashtags": self.max_hashtags,
            "min_title_length": self.min_title_length,
            "max_title_length": self.max_title_length,
            "min_description_length": self.min_description_length,
            "default_niche": self.default_niche,
            "default_tone": self.default_tone,
            "score_weights": self.score_weights,
        }

    def save(self, filepath: str) -> None:
        """Save Config to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
