"""Configuration loader for the football simulator.

Supports loading field type configuration from YAML files and provides
default configurations for NFL, College, and High School fields.
"""

import os
import yaml
from typing import Dict, Any, Optional


# Default field configurations (yards)
DEFAULT_CONFIGS = {
    "nfl": {
        "field_type": "nfl",
        "field_length_yards": 120,  # 100yd field + 2x10yd endzones
        "field_width_yards": 53.33,  # 160 feet
        "endzone_depth_yards": 10,
        "field_of_play_yards": 100,
        "yard_line_interval_yards": 1,
        "hash_mark_width": 1.0,  # distance from center to hash marks
        "hash_mark_spacing_yards": 1,
        "goal_line_width": 0,  # lines have no physical width
    },
    "college": {
        "field_type": "college",
        "field_length_yards": 120,  # 100yd field + 2x10yd endzones
        "field_width_yards": 53.33,  # 160 feet
        "endzone_depth_yards": 10,
        "field_of_play_yards": 100,
        "yard_line_interval_yards": 1,
        "hash_mark_width": 1.0,
        "hash_mark_spacing_yards": 1,
        "goal_line_width": 0,
    },
    "high_school": {
        "field_type": "high_school",
        "field_length_yards": 110,  # 100yd field + 2x5yd endzones
        "field_width_yards": 48.0,  # 144 feet
        "endzone_depth_yards": 5,
        "field_of_play_yards": 100,
        "yard_line_interval_yards": 1,
        "hash_mark_width": 1.0,
        "hash_mark_spacing_yards": 1,
        "goal_line_width": 0,
    },
}


class Config:
    """Configuration manager for the football simulator.

    Loads and manages field type configurations. Can load from YAML files
    or use built-in defaults.
    """

    def __init__(self, field_type: str = "nfl", config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            field_type: One of 'nfl', 'college', 'high_school'.
            config_path: Optional path to a YAML config file. If provided,
                        this file overrides the built-in defaults.
        """
        self._config = dict(DEFAULT_CONFIGS.get(field_type, DEFAULT_CONFIGS["nfl"]))
        self._field_type = self._config.get("field_type", field_type)

        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)

    def _load_from_file(self, path: str) -> None:
        """Load configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file.
        """
        with open(path, "r") as f:
            file_config = yaml.safe_load(f)
        if file_config and isinstance(file_config, dict):
            self._config.update(file_config)
            self._field_type = file_config.get("field_type", self._field_type)

    @property
    def field_type(self) -> str:
        """Get the current field type."""
        return self._field_type

    @property
    def field_length_yards(self) -> float:
        """Get total field length in yards."""
        return self._config["field_length_yards"]

    @property
    def field_width_yards(self) -> float:
        """Get field width in yards."""
        return self._config["field_width_yards"]

    @property
    def endzone_depth_yards(self) -> float:
        """Get endzone depth in yards."""
        return self._config["endzone_depth_yards"]

    @property
    def field_of_play_yards(self) -> float:
        """Get field of play (non-endzone) length in yards."""
        return self._config["field_of_play_yards"]

    @property
    def yard_line_interval_yards(self) -> float:
        """Get yard line marking interval in yards."""
        return self._config["yard_line_interval_yards"]

    @property
    def hash_mark_width(self) -> float:
        """Get hash mark width in yards."""
        return self._config["hash_mark_width"]

    @property
    def hash_mark_spacing_yards(self) -> float:
        """Get hash mark spacing in yards."""
        return self._config["hash_mark_spacing_yards"]

    @property
    def goal_line_width(self) -> float:
        """Get goal line width in yards."""
        return self._config["goal_line_width"]

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as a dictionary."""
        return dict(self._config)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create a Config from a dictionary.

        Args:
            config_dict: Dictionary of configuration values.

        Returns:
            A new Config instance.
        """
        field_type = config_dict.get("field_type", "nfl")
        instance = cls(field_type=field_type)
        instance._config.update(config_dict)
        return instance

    @classmethod
    def from_yaml_file(cls, path: str) -> "Config":
        """Create a Config from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            A new Config instance.
        """
        with open(path, "r") as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)

    @classmethod
    def get_available_types(cls) -> list:
        """Get list of available field types."""
        return list(DEFAULT_CONFIGS.keys())
