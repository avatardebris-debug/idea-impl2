"""Pydantic data models for the AI Movie Generation Suite.

This module defines all core data models used throughout the pipeline,
including Project, BeatSheet, Beat, CharacterRegistry, CharacterProfile,
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
        number: Beat number (1-15 for Save-the-Cat structure).
        name: Short name for the beat (e.g., 'Opening Image').
        description: Detailed description of what happens in this beat.
        scene_numbers: List of scene numbers that correspond to this beat.
    """

    number: int = Field(..., ge=1, le=15, description="Beat number (1-15)")
    name: str = Field(..., min_length=1, description="Short name for the beat")
    description: str = Field(..., min_length=1, description="Detailed description")
    scene_numbers: List[int] = Field(default_factory=list, description="Scene numbers for this beat")

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Beat name cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert beat to a dictionary for JSON serialization."""
        return {
            "number": self.number,
            "name": self.name,
            "description": self.description,
            "scene_numbers": self.scene_numbers,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert beat to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class BeatSheet(BaseModel):
    """A complete beat sheet containing all beats for a screenplay.

    Attributes:
        title: Title of the screenplay.
        logline: One-sentence logline of the story.
        beats: List of Beat objects (typically 15 for Save-the-Cat).
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

class CharacterProfile(BaseModel):
    """A single character profile.

    Attributes:
        name: Character name.
        role: Role in the story (protagonist, antagonist, supporting, etc.).
        age: Character age (optional).
        gender: Character gender (optional).
        description: Physical and personality description.
        motivation: What drives this character.
        arc: Character arc / transformation throughout the story.
        relationships: Dict of relationships to other characters.
    """

    name: str = Field(..., min_length=1, description="Character name")
    role: str = Field(..., min_length=1, description="Role in the story")
    age: Optional[int] = Field(None, ge=0, le=150, description="Character age")
    gender: Optional[str] = Field(None, description="Character gender")
    description: str = Field(..., min_length=1, description="Physical and personality description")
    motivation: str = Field(..., min_length=1, description="What drives this character")
    arc: str = Field(..., min_length=1, description="Character arc / transformation")
    relationships: Dict[str, str] = Field(default_factory=dict, description="Relationships to other characters")

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Character name cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert character profile to a dictionary for JSON serialization."""
        return {
            "name": self.name,
            "role": self.role,
            "age": self.age,
            "gender": self.gender,
            "description": self.description,
            "motivation": self.motivation,
            "arc": self.arc,
            "relationships": self.relationships,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert character profile to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class CharacterRegistry(BaseModel):
    """Registry of all characters in the screenplay.

    Attributes:
        characters: List of CharacterProfile objects.
    """

    characters: List[CharacterProfile] = Field(..., min_length=1, description="List of character profiles")

    def to_dict(self) -> Dict[str, Any]:
        """Convert character registry to a dictionary for JSON serialization."""
        return {
            "characters": [char.to_dict() for char in self.characters],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert character registry to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def get_character(self, name: str) -> Optional[CharacterProfile]:
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
        character: Name of the character speaking.
        dialogue: The spoken line.
        action: Optional parenthetical or action description.
    """

    character: str = Field(..., min_length=1, description="Character name")
    dialogue: str = Field(..., min_length=1, description="Spoken line")
    action: Optional[str] = Field(None, description="Parenthetical or action description")

    def to_dict(self) -> Dict[str, Any]:
        """Convert dialogue line to a dictionary for JSON serialization."""
        return {
            "character": self.character,
            "dialogue": self.dialogue,
            "action": self.action,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert dialogue line to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class Scene(BaseModel):
    """A single scene in the screenplay.

    Attributes:
        number: Scene number.
        location: Scene location (e.g., 'INT. COFFEE SHOP - DAY').
        description: Action/description text for the scene.
        dialogue: List of dialogue lines in the scene.
        characters_present: List of character names present in the scene.
    """

    number: int = Field(..., ge=1, description="Scene number")
    location: str = Field(..., min_length=1, description="Scene location")
    description: str = Field(..., min_length=1, description="Action/description text")
    dialogue: List[DialogueLine] = Field(default_factory=list, description="Dialogue lines")
    characters_present: List[str] = Field(default_factory=list, description="Characters present")

    @field_validator("location")
    @classmethod
    def location_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Scene location cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert scene to a dictionary for JSON serialization."""
        return {
            "number": self.number,
            "location": self.location,
            "description": self.description,
            "dialogue": [d.to_dict() for d in self.dialogue],
            "characters_present": self.characters_present,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert scene to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class Script(BaseModel):
    """A complete screenplay script.

    Attributes:
        title: Title of the screenplay.
        genre: Genre.
        tone: Tone/mood.
        scenes: List of Scene objects.
    """

    title: str = Field(..., min_length=1, description="Title of the screenplay")
    genre: str = Field(default="Drama", description="Genre")
    tone: str = Field(default="Serious", description="Tone/mood")
    scenes: List[Scene] = Field(..., min_length=1, description="List of scenes")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert script to a dictionary for JSON serialization."""
        return {
            "title": self.title,
            "genre": self.genre,
            "tone": self.tone,
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
        title: Title of the project.
        logline: One-sentence logline.
        genre: Genre.
        tone: Tone/mood.
        created_at: Project creation timestamp.
        updated_at: Last update timestamp.
        status: Current pipeline status.
        beat_sheet: Beat sheet data (optional, populated after stage 1).
        characters: Character registry (optional, populated after stage 2).
        script: Script data (optional, populated after stage 3).
        scene_descriptions: Scene descriptions (optional, populated after stage 4).
    """

    title: str = Field(..., min_length=1, description="Title of the project")
    logline: str = Field(..., min_length=1, description="One-sentence logline")
    genre: str = Field(default="Drama", description="Genre")
    tone: str = Field(default="Serious", description="Tone/mood")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Last update timestamp")
    status: str = Field(default="initialized", description="Current pipeline status")
    beat_sheet: Optional[Dict[str, Any]] = Field(None, description="Beat sheet data")
    characters: Optional[Dict[str, Any]] = Field(None, description="Character registry data")
    script: Optional[Dict[str, Any]] = Field(None, description="Script data")
    scene_descriptions: Optional[List[Dict[str, Any]]] = Field(None, description="Scene descriptions")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to a dictionary for JSON serialization."""
        return {
            "title": self.title,
            "logline": self.logline,
            "genre": self.genre,
            "tone": self.tone,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "beat_sheet": self.beat_sheet,
            "characters": self.characters,
            "script": self.script,
            "scene_descriptions": self.scene_descriptions,
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
