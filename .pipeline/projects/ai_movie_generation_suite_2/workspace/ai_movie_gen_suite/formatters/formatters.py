"""Formatters for the AI Movie Generation Suite.

Provides formatters for converting project data to various output formats.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ai_movie_gen_suite.models import Project

logger = logging.getLogger(__name__)


class BaseFormatter(ABC):
    """Abstract base class for all formatters.

    Each formatter converts project data to a specific output format.
    """

    @abstractmethod
    def format(self, project: Project) -> str:
        """Format the project data.

        Args:
            project: The project to format.

        Returns:
            The formatted output string.
        """
        ...

    @abstractmethod
    def get_extension(self) -> str:
        """Get the file extension for this format.

        Returns:
            File extension (e.g., 'txt', 'json', 'pdf').
        """
        ...

    @abstractmethod
    def get_description(self) -> str:
        """Get a human-readable description of this format.

        Returns:
            Format description.
        """
        ...


class TextFormatter(BaseFormatter):
    """Formats project data as plain text.

    Produces a human-readable text document with all project information.
    """

    def format(self, project: Project) -> str:
        """Format the project as plain text.

        Args:
            project: The project to format.

        Returns:
            Formatted text string.
        """
        lines: List[str] = []

        # Header
        lines.append("=" * 80)
        lines.append(f"  {project.title}")
        lines.append(f"  Genre: {project.genre}")
        lines.append(f"  Tone: {project.tone}")
        lines.append(f"  Logline: {project.logline}")
        lines.append("=" * 80)
        lines.append("")

        # Synopsis
        if project.synopsis:
            lines.append("SYNOPSIS")
            lines.append("-" * 40)
            lines.append(project.synopsis)
            lines.append("")

        # Characters
        if project.characters:
            lines.append("CHARACTERS")
            lines.append("-" * 40)
            for char in project.characters:
                lines.append(f"\n{char['name']}:")
                if char.get('age'):
                    lines.append(f"  Age: {char['age']}")
                if char.get('occupation'):
                    lines.append(f"  Occupation: {char['occupation']}")
                if char.get('personality'):
                    lines.append(f"  Personality: {', '.join(char['personality'])}")
                if char.get('backstory'):
                    lines.append(f"  Backstory: {char['backstory']}")
                if char.get('motivation'):
                    lines.append(f"  Motivation: {char['motivation']}")
                if char.get('arc'):
                    lines.append(f"  Arc: {char['arc']}")
                if char.get('voice'):
                    lines.append(f"  Voice: {char['voice']}")
                if char.get('appearance'):
                    lines.append(f"  Appearance: {char['appearance']}")
            lines.append("")

        # Script
        if project.script:
            lines.append("SCRIPT")
            lines.append("-" * 40)
            for scene in project.script.get('scenes', []):
                lines.append(f"\nScene {scene.get('number', '?')}: {scene.get('location', 'Unknown')}")
                lines.append(f"  Description: {scene.get('description', 'No description')}")
                for dialogue in scene.get('dialogue', []):
                    lines.append(f"  {dialogue.get('character', 'Unknown')}:")
                    lines.append(f"    \"{dialogue.get('text', '')}\"")
                    if dialogue.get('emotion'):
                        lines.append(f"    (Emotion: {dialogue['emotion']})")
            lines.append("")

        # Scenes
        if project.scenes:
            lines.append("SCENES")
            lines.append("-" * 40)
            for scene in project.scenes:
                lines.append(f"\nScene {scene.get('scene_number', '?')}: {scene.get('location', 'Unknown')}")
                if scene.get('visual_description'):
                    lines.append(f"  Visual Description: {scene['visual_description']}")
                if scene.get('camera_directions'):
                    lines.append(f"  Camera Directions: {scene['camera_directions']}")
                if scene.get('lighting'):
                    lines.append(f"  Lighting: {scene['lighting']}")
                if scene.get('color_palette'):
                    lines.append(f"  Color Palette: {scene['color_palette']}")
                if scene.get('mood'):
                    lines.append(f"  Mood: {scene['mood']}")
                if scene.get('props_and_set_design'):
                    lines.append(f"  Props/Set Design: {scene['props_and_set_design']}")
            lines.append("")

        # Beats
        if project.beats:
            lines.append("BEATS")
            lines.append("-" * 40)
            for beat in project.beats:
                lines.append(f"\nBeat {beat.get('beat_number', '?')}:")
                if beat.get('action'):
                    lines.append(f"  Action: {beat['action']}")
                if beat.get('dialogue'):
                    lines.append(f"  Dialogue: {beat['dialogue']}")
                if beat.get('emotion'):
                    lines.append(f"  Emotion: {beat['emotion']}")
                if beat.get('camera_directions'):
                    lines.append(f"  Camera Directions: {beat['camera_directions']}")
            lines.append("")

        return "\n".join(lines)

    def get_extension(self) -> str:
        """Get the file extension for this format.

        Returns:
            'txt'
        """
        return "txt"

    def get_description(self) -> str:
        """Get a human-readable description of this format.

        Returns:
            Format description.
        """
        return "Plain text document with all project information"


class JSONFormatter(BaseFormatter):
    """Formats project data as JSON.

    Produces a structured JSON document with all project information.
    """

    def format(self, project: Project) -> str:
        """Format the project as JSON.

        Args:
            project: The project to format.

        Returns:
            Formatted JSON string.
        """
        data = {
            "title": project.title,
            "genre": project.genre,
            "tone": project.tone,
            "logline": project.logline,
            "synopsis": project.synopsis,
            "characters": project.characters,
            "script": project.script,
            "scenes": project.scenes,
            "beats": project.beats,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def get_extension(self) -> str:
        """Get the file extension for this format.

        Returns:
            'json'
        """
        return "json"

    def get_description(self) -> str:
        """Get a human-readable description of this format.

        Returns:
            Format description.
        """
        return "Structured JSON document with all project information"


class MarkdownFormatter(BaseFormatter):
    """Formats project data as Markdown.

    Produces a Markdown document with all project information.
    """

    def format(self, project: Project) -> str:
        """Format the project as Markdown.

        Args:
            project: The project to format.

        Returns:
            Formatted Markdown string.
        """
        lines: List[str] = []

        # Header
        lines.append(f"# {project.title}")
        lines.append("")
        lines.append(f"**Genre:** {project.genre}")
        lines.append(f"**Tone:** {project.tone}")
        lines.append(f"**Logline:** {project.logline}")
        lines.append("")

        # Synopsis
        if project.synopsis:
            lines.append("## Synopsis")
            lines.append("")
            lines.append(project.synopsis)
            lines.append("")

        # Characters
        if project.characters:
            lines.append("## Characters")
            lines.append("")
            for char in project.characters:
                lines.append(f"### {char['name']}")
                lines.append("")
                if char.get('age'):
                    lines.append(f"- **Age:** {char['age']}")
                if char.get('occupation'):
                    lines.append(f"- **Occupation:** {char['occupation']}")
                if char.get('personality'):
                    lines.append(f"- **Personality:** {', '.join(char['personality'])}")
                if char.get('backstory'):
                    lines.append(f"- **Backstory:** {char['backstory']}")
                if char.get('motivation'):
                    lines.append(f"- **Motivation:** {char['motivation']}")
                if char.get('arc'):
                    lines.append(f"- **Arc:** {char['arc']}")
                if char.get('voice'):
                    lines.append(f"- **Voice:** {char['voice']}")
                if char.get('appearance'):
                    lines.append(f"- **Appearance:** {char['appearance']}")
                lines.append("")

        # Script
        if project.script:
            lines.append("## Script")
            lines.append("")
            for scene in project.script.get('scenes', []):
                lines.append(f"### Scene {scene.get('number', '?')}: {scene.get('location', 'Unknown')}")
                lines.append("")
                lines.append(f"{scene.get('description', 'No description')}")
                lines.append("")
                for dialogue in scene.get('dialogue', []):
                    lines.append(f"**{dialogue.get('character', 'Unknown')}**")
                    lines.append("")
                    lines.append(f"> {dialogue.get('text', '')}")
                    if dialogue.get('emotion'):
                        lines.append(f"> *({dialogue['emotion']})*")
                    lines.append("")

        # Scenes
        if project.scenes:
            lines.append("## Scenes")
            lines.append("")
            for scene in project.scenes:
                lines.append(f"### Scene {scene.get('scene_number', '?')}: {scene.get('location', 'Unknown')}")
                lines.append("")
                if scene.get('visual_description'):
                    lines.append(f"**Visual Description:** {scene['visual_description']}")
                if scene.get('camera_directions'):
                    lines.append(f"**Camera Directions:** {scene['camera_directions']}")
                if scene.get('lighting'):
                    lines.append(f"**Lighting:** {scene['lighting']}")
                if scene.get('color_palette'):
                    lines.append(f"**Color Palette:** {scene['color_palette']}")
                if scene.get('mood'):
                    lines.append(f"**Mood:** {scene['mood']}")
                if scene.get('props_and_set_design'):
                    lines.append(f"**Props/Set Design:** {scene['props_and_set_design']}")
                lines.append("")

        # Beats
        if project.beats:
            lines.append("## Beats")
            lines.append("")
            for beat in project.beats:
                lines.append(f"### Beat {beat.get('beat_number', '?')}")
                lines.append("")
                if beat.get('action'):
                    lines.append(f"**Action:** {beat['action']}")
                if beat.get('dialogue'):
                    lines.append(f"**Dialogue:** {beat['dialogue']}")
                if beat.get('emotion'):
                    lines.append(f"**Emotion:** {beat['emotion']}")
                if beat.get('camera_directions'):
                    lines.append(f"**Camera Directions:** {beat['camera_directions']}")
                lines.append("")

        return "\n".join(lines)

    def get_extension(self) -> str:
        """Get the file extension for this format.

        Returns:
            'md'
        """
        return "md"

    def get_description(self) -> str:
        """Get a human-readable description of this format.

        Returns:
            Format description.
        """
        return "Markdown document with all project information"


class Formatters:
    """Registry of available formatters.

    Provides access to all formatters used in the pipeline.
    """

    def __init__(self):
        """Initialize the formatter registry."""
        self._formatters: Dict[str, BaseFormatter] = {
            "txt": TextFormatter(),
            "json": JSONFormatter(),
            "md": MarkdownFormatter(),
        }

    def get_formatter(self, format_type: str) -> BaseFormatter:
        """Get a formatter by format type.

        Args:
            format_type: Format type (e.g., 'txt', 'json', 'md').

        Returns:
            The formatter instance.

        Raises:
            ValueError: If the format type is not supported.
        """
        formatter = self._formatters.get(format_type)
        if not formatter:
            raise ValueError(f"Unsupported format type: {format_type}. Supported: {list(self._formatters.keys())}")
        return formatter

    def list_formats(self) -> List[str]:
        """List all available format types.

        Returns:
            List of format type strings.
        """
        return list(self._formatters.keys())

    def format_project(self, project: Project, format_type: str) -> str:
        """Format a project with the specified format type.

        Args:
            project: The project to format.
            format_type: Format type (e.g., 'txt', 'json', 'md').

        Returns:
            Formatted output string.

        Raises:
            ValueError: If the format type is not supported.
        """
        formatter = self.get_formatter(format_type)
        return formatter.format(project)


# Global formatter registry instance
formatters = Formatters()
