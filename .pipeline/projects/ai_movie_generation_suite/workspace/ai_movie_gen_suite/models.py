"""Core data models for the AI Movie Generation Suite."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class BeatPhase(str, Enum):
    """Save-the-Cat act phases."""
    SETUP = "setup"
    CONFRONTATION = "confrontation"
    RESOLUTION = "resolution"


class CharacterRole(str, Enum):
    """Standard character roles."""
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    MENTOR = "mentor"
    ALLY = "ally"
    SIDEKICK = "sidekick"
    DEUS_EX_MACHINA = "deus_ex_machina"
    SUPPORTING = "supporting"


# ── Beat Models ──────────────────────────────────────────────────────────────

SAVE_THE_CAT_BEATS = [
    "Opening Image",
    "Theme Stated",
    "Setup",
    "Catalyst",
    "Debate",
    "Break into Two",
    "B Story",
    "Fun and Games",
    "Midpoint",
    "Bad Guys Close In",
    "All Is Lost",
    "Dark Night of the Soul",
    "Break into Three",
    "Finale",
    "Final Image",
]


class Beat(BaseModel):
    """A single Save-the-Cat beat."""
    beat_name: str
    beat_number: int
    summary: str
    description: str = ""
    characters_involved: List[str] = Field(default_factory=list)
    estimated_page_range: Optional[str] = None
    phase: Optional[BeatPhase] = None
    scene_ids: List[str] = Field(default_factory=list)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        if self.phase is not None:
            d["phase"] = self.phase.value
        return d


class BeatSheet(BaseModel):
    """Collection of 15 Save-the-Cat beats."""
    logline: str
    genre: str
    beats: List[Beat] = Field(default_factory=list)

    def add_beat(self, beat: Beat) -> None:
        self.beats.append(beat)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["beats"] = [b.model_dump() for b in self.beats]
        return d


# ── Character Models ─────────────────────────────────────────────────────────

class Character(BaseModel):
    """A character in the screenplay."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    role: CharacterRole
    physical_description: str = ""
    personality_traits: List[str] = Field(default_factory=list)
    voice_notes: str = ""
    costume_notes: str = ""
    visual_anchor: str = ""
    backstory: str = ""
    arc_summary: str = ""

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["role"] = self.role.value
        return d


class CharacterRegistry(BaseModel):
    """Registry of all characters."""
    characters: List[Character] = Field(default_factory=list)

    def add_character(self, character: Character) -> None:
        self.characters.append(character)

    def get_by_id(self, char_id: str) -> Optional[Character]:
        for c in self.characters:
            if c.id == char_id:
                return c
        return None

    def get_by_name(self, name: str) -> Optional[Character]:
        for c in self.characters:
            if c.name.lower() == name.lower():
                return c
        return None

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["characters"] = [c.model_dump() for c in self.characters]
        return d


# ── Scene / Script Models ────────────────────────────────────────────────────

class DialogueLine(BaseModel):
    """A single line of dialogue."""
    character_name: str
    character_id: str
    text: str
    parenthetical: Optional[str] = None
    delivery: Optional[str] = None  # e.g. "whispering", "shouting"


class Scene(BaseModel):
    """A single screenplay scene."""
    scene_id: str = Field(default_factory=lambda: f"SC-{uuid.uuid4().hex[:6].upper()}")
    scene_heading: str  # e.g. "INT. COFFEE SHOP - DAY"
    action: str
    characters_present: List[str] = Field(default_factory=list)
    dialogue_lines: List[DialogueLine] = Field(default_factory=list)
    estimated_page_range: Optional[str] = None
    beat_ref: Optional[str] = None  # references which beat this scene expands

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["dialogue_lines"] = [dl.model_dump() for dl in self.dialogue_lines]
        return d


class Script(BaseModel):
    """Full screenplay output."""
    title: str
    logline: str
    genre: str
    scenes: List[Scene] = Field(default_factory=list)

    def add_scene(self, scene: Scene) -> None:
        self.scenes.append(scene)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["scenes"] = [s.model_dump() for s in self.scenes]
        return d


# ── Scene Description Models ─────────────────────────────────────────────────

class SceneDescription(BaseModel):
    """Visual direction for a single scene."""
    scene_id: str
    setting: str = ""
    lighting: str = ""
    camera_notes: str = ""
    mood: str = ""
    action_beats: List[str] = Field(default_factory=list)
    visual_style: str = ""


class SceneDescriptionCollection(BaseModel):
    """All scene descriptions."""
    descriptions: Dict[str, SceneDescription] = Field(default_factory=dict)

    def add_description(self, scene_id: str, desc: SceneDescription) -> None:
        self.descriptions[scene_id] = desc

    def get_description(self, scene_id: str) -> Optional[SceneDescription]:
        return self.descriptions.get(scene_id)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["descriptions"] = {k: v.model_dump() for k, v in self.descriptions.items()}
        return d


# ── Project Model ────────────────────────────────────────────────────────────

class Project(BaseModel):
    """Top-level project container."""
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    logline: str
    genre: str
    tone: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    beat_sheet: Optional[BeatSheet] = None
    character_registry: Optional[CharacterRegistry] = None
    script: Optional[Script] = None
    scene_descriptions: Optional[SceneDescriptionCollection] = None

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        if self.beat_sheet:
            d["beat_sheet"] = self.beat_sheet.model_dump()
        if self.character_registry:
            d["character_registry"] = self.character_registry.model_dump()
        if self.script:
            d["script"] = self.script.model_dump()
        if self.scene_descriptions:
            d["scene_descriptions"] = self.scene_descriptions.model_dump()
        return d
