"""YAML Formatter — Converts screenplay data to YAML format.

Generates human-readable YAML output for Script, BeatSheet, CharacterRegistry, etc.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None

from ai_movie_gen_suite.models import (
    BeatSheet,
    CharacterRegistry,
    SceneDescriptionCollection,
    Script,
)


class YAMLFormatter:
    """Formats screenplay data into YAML."""

    def __init__(
        self,
        script: Optional[Script] = None,
        beat_sheet: Optional[BeatSheet] = None,
        characters: Optional[CharacterRegistry] = None,
        scene_descriptions: Optional[SceneDescriptionCollection] = None,
    ):
        self.script = script
        self.beat_sheet = beat_sheet
        self.characters = characters
        self.scene_descriptions = scene_descriptions

    def format(self) -> str:
        """Generate YAML string."""
        if yaml is None:
            raise ImportError("PyYAML is required for YAML formatting. Install with: pip install pyyaml")

        data: Dict[str, Any] = {}

        if self.script:
            data["script"] = self.script.model_dump()

        if self.beat_sheet:
            data["beat_sheet"] = self.beat_sheet.model_dump()

        if self.characters:
            data["characters"] = self.characters.model_dump()

        if self.scene_descriptions:
            data["scene_descriptions"] = self.scene_descriptions.model_dump()

        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def save(self, filepath: str) -> None:
        """Save YAML file to disk."""
        yaml_str = self.format()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(yaml_str)
