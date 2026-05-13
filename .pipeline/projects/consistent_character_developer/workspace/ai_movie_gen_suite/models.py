"""Core data models for the AI movie generation suite.

Defines Character, CharacterRegistry, Scene, and Script models used
throughout the pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Character(BaseModel):
    """A character in the screenplay.

    Fields:
        id: Unique character identifier.
        name: Character's name.
        role: Role in the story (e.g., protagonist, antagonist).
        motivation: What drives the character.
        physical_description: Physical appearance.
        personality_traits: List of personality traits.
        voice_notes: Notes on voice/tone.
        costume_notes: Notes on costume/appearance.
        visual_anchor: Key visual feature for consistency.
        backstory: Character backstory.
        arc_summary: Character arc summary.
        reference_image_path: Path to generated reference image (optional).
    """

    id: str
    name: str
    role: str
    motivation: str
    physical_description: str
    personality_traits: List[str] = Field(default_factory=list)
    voice_notes: str = ""
    costume_notes: str = ""
    visual_anchor: str = ""
    backstory: str = ""
    arc_summary: str = ""
    reference_image_path: str = ""

    def model_dump(self, **kwargs) -> dict:
        d = super().model_dump(**kwargs)
        return d


class CharacterRegistry(BaseModel):
    """Registry of all characters in the screenplay.

    Fields:
        characters: Mapping of character_id → Character.
    """

    characters: Dict[str, Character] = Field(default_factory=dict)

    def add_character(self, character: Character) -> None:
        """Add a character to the registry."""
        self.characters[character.id] = character

    def get_character(self, character_id: str) -> Optional[Character]:
        """Get a character by ID."""
        return self.characters.get(character_id)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v.model_dump() for k, v in self.characters.items()}


class Scene(BaseModel):
    """A single scene in the screenplay.

    Fields:
        scene_id: Unique scene identifier.
        scene_heading: Scene heading (e.g., "INT. CAVE - DAY").
        action: Scene action description.
    """

    scene_id: str
    scene_heading: str
    action: str

    def model_dump(self, **kwargs) -> dict:
        d = super().model_dump(**kwargs)
        return d


class Script(BaseModel):
    """A complete screenplay.

    Fields:
        title: Movie title.
        logline: One-sentence summary.
        genre: Movie genre.
        scenes: List of scenes.
    """

    title: str
    logline: str
    genre: str
    scenes: List[Scene] = Field(default_factory=list)

    def model_dump(self, **kwargs) -> dict:
        d = super().model_dump(**kwargs)
        return d
