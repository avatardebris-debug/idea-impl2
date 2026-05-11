"""JSON Formatter — Converts screenplay data to JSON format.

Generates structured JSON output for Script, BeatSheet, CharacterRegistry, etc.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ai_movie_gen_suite.models import (
    BeatSheet,
    CharacterRegistry,
    SceneDescriptionCollection,
    Script,
)


class JSONFormatter:
    """Formats screenplay data into JSON."""

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

    def format(self) -> Dict[str, Any]:
        """Generate JSON-serializable dictionary."""
        data: Dict[str, Any] = {}

        if self.script:
            data["script"] = self.script.model_dump()

        if self.beat_sheet:
            data["beat_sheet"] = self.beat_sheet.model_dump()

        if self.characters:
            data["characters"] = self.characters.model_dump()

        if self.scene_descriptions:
            data["scene_descriptions"] = self.scene_descriptions.model_dump()

        return data

    def format_string(self) -> str:
        """Generate JSON string."""
        data = self.format()
        return json.dumps(data, indent=2, ensure_ascii=False)

    def save(self, filepath: str) -> None:
        """Save JSON file to disk."""
        json_str = self.format_string()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_str)
