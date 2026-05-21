"""Character Consistency Engine — character sheets and visual anchor enforcement."""

from __future__ import annotations

from typing import List, Optional

from ai_movie_gen_suite.models import (
    Character,
    CharacterRegistry,
    CharacterSheetPrompt,
    ImageModelTarget,
    Script,
)


DEFAULT_STYLE = "cinematic, 35mm film, anamorphic lens, production still"
DEFAULT_NEGATIVE = "blurry, low quality, deformed, watermark, text overlay"


class CharacterConsistencyEngine:
    """Ensures consistent character visuals and builds character-sheet prompts."""

    def __init__(
        self,
        character_registry: CharacterRegistry,
        script: Optional[Script] = None,
        tone: str = "",
        target_model: ImageModelTarget = ImageModelTarget.SDXL,
    ):
        self.character_registry = character_registry
        self.script = script
        self.tone = tone
        self.target_model = target_model

    def enrich_registry(self) -> CharacterRegistry:
        """Fill missing visual anchors and physical descriptions from role templates."""
        for char in self.character_registry.characters:
            if not char.visual_anchor:
                char.visual_anchor = self._default_visual_anchor(char)
            if not char.physical_description:
                char.physical_description = (
                    f"{char.name}, {char.role.value}, distinctive look for {self.tone or 'the story'}."
                )
        return self.character_registry

    def generate_character_sheet(self, character: Character) -> CharacterSheetPrompt:
        """Build an AI image prompt for a character reference sheet."""
        appearance = character.physical_description or character.visual_anchor
        costume = character.costume_notes or "wardrobe consistent with role"
        traits = ", ".join(character.personality_traits[:3]) if character.personality_traits else ""

        prompt = (
            f"Character reference sheet, full body and portrait, {character.name}. "
            f"{appearance}. Costume: {costume}. "
            f"Personality: {traits}. Visual anchor: {character.visual_anchor}. "
            f"Style: {DEFAULT_STYLE}."
        )
        if self.tone:
            prompt += f" Tone: {self.tone}."

        return CharacterSheetPrompt(
            character_id=character.id,
            character_name=character.name,
            prompt=prompt.strip(),
            negative_prompt=DEFAULT_NEGATIVE,
            target_model=self.target_model,
            visual_anchor=character.visual_anchor,
            parameters={"aspect_ratio": "2:3", "sheet_layout": "turnaround"},
        )

    def generate_all_sheets(self) -> List[CharacterSheetPrompt]:
        """Generate character sheet prompts for every character in the registry."""
        self.enrich_registry()
        return [self.generate_character_sheet(c) for c in self.character_registry.characters]

    def _default_visual_anchor(self, character: Character) -> str:
        role = character.role.value
        if role == "protagonist":
            return "distinctive eyes and posture that read as the hero"
        if role == "antagonist":
            return "sharp silhouette and controlled menace"
        if role == "mentor":
            return "weathered face and knowing gaze"
        return f"memorable visual signature for {character.name}"
