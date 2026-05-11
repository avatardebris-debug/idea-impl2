"""Pydantic data models for the AI Movie Generation Suite.

This module defines all core data models used throughout the pipeline,
including Project, BeatSheet, Beat, CharacterRegistry, Character,
Script, Scene, DialogueLine, and SceneDescription.

Each model includes:
- Pydantic field validation
- `to_dict()` method for JSON serialization
- Proper type hints and docstrings
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ====================================================================
# Beat Models
# ====================================================================

class Beat(BaseModel):
    """A single beat in the Save-the-Cat beat sheet structure.

    Attributes:
        id: Unique beat identifier.
        act: Act number (1, 2, or 3).
        description: Detailed description of what happens in this beat.
    """

    id: str = Field(..., min_length=1, description="Unique beat identifier")
    act: int = Field(..., ge=1, le=3, description="Act number (1, 2, or 3)")
    description: str = Field(..., min_length=1, description="Detailed description")

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Beat id cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert beat to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "act": self.act,
            "description": self.description,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert beat to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class BeatSheet(BaseModel):
    """Complete beat sheet for a screenplay.

    Attributes:
        title: Title of the screenplay.
        logline: One-sentence logline.
        beats: List of Beat objects.
        genre: Genre of the screenplay.
        tone: Tone/mood of the screenplay.
    """

    title: str = Field(..., min_length=1, description="Title of the screenplay")
    logline: str = Field(..., min_length=1, description="One-sentence logline")
    beats: List[Beat] = Field(..., min_length=1, description="List of beats")
    genre: str = Field(default="Drama", description="Genre of the screenplay")
    tone: str = Field(default="Serious", description="Tone/mood of the screenplay")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert beat sheet to a dictionary for JSON serialization."""
        return {
            "title": self.title,
            "logline": self.logline,
            "beats": [beat.to_dict() for beat in self.beats],
            "genre": self.genre,
            "tone": self.tone,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert beat sheet to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# ====================================================================
# Character Models
# ====================================================================

class Character(BaseModel):
    """A single character profile.

    Attributes:
        id: Unique character identifier.
        name: Character name.
        description: Character description.
    """

    id: str = Field(..., min_length=1, description="Unique character identifier")
    name: str = Field(..., min_length=1, description="Character name")
    description: str = Field(..., min_length=1, description="Character description")

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Character id cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Character name cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert character profile to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert character profile to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class CharacterRegistry(BaseModel):
    """Registry of all characters in the screenplay.

    Attributes:
        characters: List of Character objects.
    """

    characters: List[Character] = Field(..., min_length=1, description="List of character profiles")

    def to_dict(self) -> Dict[str, Any]:
        """Convert character registry to a dictionary for JSON serialization."""
        return {
            "characters": [char.to_dict() for char in self.characters],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert character registry to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def get_character(self, name: str) -> Optional[Character]:
        """Get a character by name (case-insensitive)."""
        for char in self.characters:
            if char.name.lower() == name.lower():
                return char
        return None


# ====================================================================
# Script Models
# ====================================================================

class DialogueLine(BaseModel):
    """A single line of dialogue in a scene.

    Attributes:
        character_name: Name of the character speaking.
        parenthetical: Optional parenthetical direction.
        text: The spoken line.
    """

    character_name: str = Field(..., min_length=1, description="Character name")
    parenthetical: Optional[str] = Field(None, description="Parenthetical direction")
    text: str = Field(..., min_length=1, description="Spoken line")

    def to_dict(self) -> Dict[str, Any]:
        """Convert dialogue line to a dictionary for JSON serialization."""
        return {
            "character_name": self.character_name,
            "parenthetical": self.parenthetical,
            "text": self.text,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert dialogue line to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class Scene(BaseModel):
    """A single scene in the screenplay.

    Attributes:
        scene_id: Unique scene identifier.
        scene_heading: Scene heading (e.g., 'INT. COFFEE SHOP - DAY').
        action: Action/description text.
        characters_present: List of character names present.
        dialogue_lines: List of dialogue lines.
    """

    scene_id: str = Field(..., min_length=1, description="Unique scene identifier")
    scene_heading: str = Field(..., min_length=1, description="Scene heading")
    action: str = Field(..., min_length=1, description="Action/description text")
    characters_present: List[str] = Field(default_factory=list, description="Characters present")
    dialogue_lines: List[DialogueLine] = Field(default_factory=list, description="Dialogue lines")

    @field_validator("scene_id")
    @classmethod
    def scene_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Scene id cannot be empty")
        return v.strip()

    @field_validator("scene_heading")
    @classmethod
    def scene_heading_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Scene heading cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert scene to a dictionary for JSON serialization."""
        return {
            "scene_id": self.scene_id,
            "scene_heading": self.scene_heading,
            "action": self.action,
            "characters_present": self.characters_present,
            "dialogue_lines": [d.to_dict() for d in self.dialogue_lines],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert scene to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class Script(BaseModel):
    """A complete screenplay script.

    Attributes:
        logline: One-sentence logline.
        scenes: List of Scene objects.
    """

    logline: str = Field(..., min_length=1, description="One-sentence logline")
    scenes: List[Scene] = Field(..., min_length=1, description="List of scenes")

    def to_dict(self) -> Dict[str, Any]:
        """Convert script to a dictionary for JSON serialization."""
        return {
            "logline": self.logline,
            "scenes": [scene.to_dict() for scene in self.scenes],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert script to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# ====================================================================
# Scene Description Models
# ====================================================================

class SceneDescription(BaseModel):
    """Visual direction for a single scene.

    Attributes:
        scene_number: Corresponding scene number.
        location: Scene location.
        visual_description: Detailed visual description for video generation.
        camera_directions: Camera movement and framing directions.
        lighting: Lighting description.
        color_palette: Color palette for the scene.
        mood: Mood/atmosphere description.
        props_and_set_design: Key props and set design elements.
    """

    scene_number: int = Field(..., ge=1, description="Corresponding scene number")
    location: str = Field(..., min_length=1, description="Scene location")
    visual_description: str = Field(..., min_length=1, description="Detailed visual description")
    camera_directions: str = Field(..., min_length=1, description="Camera movement and framing")
    lighting: str = Field(..., min_length=1, description="Lighting description")
    color_palette: str = Field(..., min_length=1, description="Color palette")
    mood: str = Field(..., min_length=1, description="Mood/atmosphere")
    props_and_set_design: str = Field(..., min_length=1, description="Key props and set design")

    def to_dict(self) -> Dict[str, Any]:
        """Convert scene description to a dictionary for JSON serialization."""
        return {
            "scene_number": self.scene_number,
            "location": self.location,
            "visual_description": self.visual_description,
            "camera_directions": self.camera_directions,
            "lighting": self.lighting,
            "color_palette": self.color_palette,
            "mood": self.mood,
            "props_and_set_design": self.props_and_set_design,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert scene description to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# ====================================================================
# Project Model
# ====================================================================

class Project(BaseModel):
    """Top-level project model representing the entire screenplay project.

    Attributes:
        project_id: Unique project identifier.
        title: Title of the project.
        logline: One-sentence logline.
        genre: Genre.
        tone: Tone/mood.
        created_at: Project creation timestamp.
        updated_at: Last update timestamp.
        status: Current pipeline status.
        beat_sheet: Beat sheet data (optional, populated after stage 1).
        characters: Character registry data (optional, populated after stage 2).
        script: Script data (optional, populated after stage 3).
        scene_descriptions: Scene descriptions (optional, populated after stage 4).
    """

    project_id: str = Field(..., min_length=1, description="Unique project identifier")
    title: str = Field(..., min_length=1, description="Title of the project")
    logline: str = Field(..., min_length=1, description="One-sentence logline")
    genre: str = Field(default="Drama", description="Genre")
    tone: str = Field(default="Serious", description="Tone/mood")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Last update timestamp")
    status: str = Field(default="initialized", description="Current pipeline status")
    beat_sheet: Optional[BeatSheet] = Field(None, description="Beat sheet data")
    characters: Optional[CharacterRegistry] = Field(None, description="Character registry data")
    script: Optional[Script] = Field(None, description="Script data")
    scene_descriptions: Optional[List[SceneDescription]] = Field(None, description="Scene descriptions")

    @field_validator("project_id")
    @classmethod
    def project_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Project id cannot be empty")
        return v.strip()

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to a dictionary for JSON serialization."""
        return {
            "project_id": self.project_id,
            "title": self.title,
            "logline": self.logline,
            "genre": self.genre,
            "tone": self.tone,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "beat_sheet": self.beat_sheet.to_dict() if self.beat_sheet else None,
            "characters": self.characters.to_dict() if self.characters else None,
            "script": self.script.to_dict() if self.script else None,
            "scene_descriptions": [sd.to_dict() for sd in self.scene_descriptions] if self.scene_descriptions else None,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert project to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def update_status(self, new_status: str) -> None:
        """Update the project status and timestamp."""
        self.status = new_status
        self.updated_at = datetime.now().isoformat()


# ====================================================================
# JSON Schema helpers
# ====================================================================

def get_json_schema(model: type[BaseModel]) -> Dict[str, Any]:
    """Get the JSON schema for a Pydantic model."""
    return model.model_json_schema()


def validate_json_with_schema(data: Dict[str, Any], model: type[BaseModel]) -> BaseModel:
    """Validate and parse JSON data against a Pydantic model.

    Args:
        data: Dictionary of data to validate.
        model: Pydantic model class to validate against.

    Returns:
        Validated model instance.

    Raises:
        ValueError: If validation fails.
    """
    try:
        return model(**data)
    except Exception as e:
        raise ValueError(f"Validation failed: {e}")
