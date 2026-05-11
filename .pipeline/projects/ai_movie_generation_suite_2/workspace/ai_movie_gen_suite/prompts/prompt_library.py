"""Prompt templates for the AI Movie Generation Suite.

Provides a library of reusable prompt templates for each pipeline stage.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptTemplate:
    """A reusable prompt template with variable substitution.

    Attributes:
        name: Template name.
        template: The template string with {variable} placeholders.
        description: Human-readable description.
    """

    def __init__(self, name: str, template: str, description: str = ""):
        """Initialize the prompt template.

        Args:
            name: Template name.
            template: The template string with {variable} placeholders.
            description: Human-readable description.
        """
        self.name = name
        self.template = template
        self.description = description

    def render(self, **kwargs: Any) -> str:
        """Render the template with the given variables.

        Args:
            **kwargs: Variables to substitute into the template.

        Returns:
            The rendered template string.

        Raises:
            KeyError: If a required variable is missing.
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"Missing variable in template '{self.name}': {e}") from e

    def __str__(self) -> str:
        """Return the template name."""
        return self.name


class PromptLibrary:
    """Library of prompt templates for the pipeline.

    Provides access to all prompt templates used in the movie generation pipeline.
    """

    def __init__(self):
        """Initialize the prompt library with all templates."""
        self._templates: Dict[str, PromptTemplate] = {}
        self._register_templates()

    def _register_templates(self) -> None:
        """Register all prompt templates."""
        self._templates = {
            "beat_generator": PromptTemplate(
                name="beat_generator",
                description="Generates beats for a scene",
                template=(
                    "You are an expert screenwriter specializing in {genre} films.\n\n"
                    "Given the following scene information, generate detailed beats for the scene.\n\n"
                    "Scene Number: {scene_number}\n"
                    "Location: {location}\n"
                    "Scene Description: {description}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n\n"
                    "For each beat, provide:\n"
                    "- beat_number: The beat number (integer)\n"
                    "- action: The action taking place\n"
                    "- dialogue: Any dialogue (or null if none)\n"
                    "- emotion: The emotional tone of the beat\n"
                    "- camera_directions: Camera directions for the beat\n\n"
                    "Return a JSON object with a 'beats' array containing all beats.\n"
                    "Each beat should be a JSON object with the fields listed above.\n"
                    "Ensure the beats flow logically and build tension appropriately.\n"
                    "Include at least 3 beats and no more than 8 beats.\n"
                ),
            ),
            "character_generator": PromptTemplate(
                name="character_generator",
                description="Generates character profiles",
                template=(
                    "You are an expert character developer for {genre} films.\n\n"
                    "Given the following script information, generate detailed character profiles.\n\n"
                    "Script Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Logline: {logline}\n\n"
                    "For each character, provide:\n"
                    "- name: Character name\n"
                    "- age: Character age (or null if unknown)\n"
                    "- occupation: Character occupation\n"
                    "- personality: Personality traits (array of strings)\n"
                    "- backstory: Character backstory\n"
                    "- motivation: What drives the character\n"
                    "- arc: Character development arc\n"
                    "- voice: Speaking style and mannerisms\n"
                    "- appearance: Physical description\n\n"
                    "Return a JSON object with a 'characters' array containing all characters.\n"
                    "Include at least 3 characters and no more than 10 characters.\n"
                    "Ensure characters have distinct personalities and motivations.\n"
                ),
            ),
            "script_generator": PromptTemplate(
                name="script_generator",
                description="Generates script content",
                template=(
                    "You are an expert screenwriter specializing in {genre} films.\n\n"
                    "Given the following script information, generate a detailed script.\n\n"
                    "Title: {title}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n"
                    "Logline: {logline}\n"
                    "Characters: {characters}\n\n"
                    "Generate a script with the following structure:\n"
                    "- title: Script title\n"
                    "- logline: One-sentence summary\n"
                    "- genre: Film genre\n"
                    "- tone: Overall tone\n"
                    "- scenes: Array of scene objects\n"
                    "Each scene should have:\n"
                    "- number: Scene number (integer)\n"
                    "- location: Scene location\n"
                    "- description: Scene description\n"
                    "- dialogue: Array of dialogue objects\n"
                    "Each dialogue should have:\n"
                    "- character: Character name\n"
                    "- text: Dialogue text\n"
                    "- emotion: Emotional tone\n\n"
                    "Ensure the script has a clear beginning, middle, and end.\n"
                    "Include at least 5 scenes and no more than 20 scenes.\n"
                    "Make the dialogue natural and engaging.\n"
                ),
            ),
            "scene_generator": PromptTemplate(
                name="scene_generator",
                description="Generates scene details",
                template=(
                    "You are an expert director specializing in {genre} films.\n\n"
                    "Given the following scene information, generate detailed scene directions.\n\n"
                    "Scene Number: {scene_number}\n"
                    "Location: {location}\n"
                    "Scene Description: {description}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n\n"
                    "For this scene, provide:\n"
                    "- scene_number: The scene number (integer)\n"
                    "- location: Scene location\n"
                    "- visual_description: Detailed visual description of the scene\n"
                    "- camera_directions: Camera directions and movements\n"
                    "- lighting: Lighting design and mood\n"
                    "- color_palette: Color palette for the scene\n"
                    "- mood: Overall mood and atmosphere\n"
                    "- props_and_set_design: Props and set design details\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific and detailed in your descriptions.\n"
                    "Consider the genre and tone when making creative choices.\n"
                ),
            ),
            "scene_description": PromptTemplate(
                name="scene_description",
                description="Generates scene descriptions",
                template=(
                    "You are an expert cinematographer specializing in {genre} films.\n\n"
                    "Given the following scene information, generate a detailed scene description.\n\n"
                    "Scene Number: {scene_number}\n"
                    "Location: {location}\n"
                    "Scene Description: {description}\n"
                    "Genre: {genre}\n"
                    "Tone: {tone}\n\n"
                    "Provide a detailed scene description including:\n"
                    "- scene_number: The scene number (integer)\n"
                    "- location: Scene location\n"
                    "- visual_description: Detailed visual description\n"
                    "- camera_directions: Camera directions\n"
                    "- lighting: Lighting design\n"
                    "- color_palette: Color palette\n"
                    "- mood: Overall mood\n"
                    "- props_and_set_design: Props and set design\n\n"
                    "Return a JSON object with the fields listed above.\n"
                    "Be specific and detailed in your descriptions.\n"
                    "Consider the genre and tone when making creative choices.\n"
                ),
            ),
        }

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name.

        Args:
            name: Template name.

        Returns:
            The PromptTemplate object, or None if not found.
        """
        return self._templates.get(name)

    def render_template(self, name: str, **kwargs: Any) -> str:
        """Render a template by name with the given variables.

        Args:
            name: Template name.
            **kwargs: Variables to substitute into the template.

        Returns:
            The rendered template string.

        Raises:
            KeyError: If the template is not found or a required variable is missing.
        """
        template = self.get_template(name)
        if not template:
            raise KeyError(f"Template '{name}' not found")
        return template.render(**kwargs)

    def list_templates(self) -> List[str]:
        """List all available template names.

        Returns:
            List of template names.
        """
        return list(self._templates.keys())

    def get_template_info(self, name: str) -> Optional[Dict[str, str]]:
        """Get information about a template.

        Args:
            name: Template name.

        Returns:
            Dictionary with template information, or None if not found.
        """
        template = self.get_template(name)
        if not template:
            return None
        return {
            "name": template.name,
            "description": template.description,
            "template": template.template,
        }


# Global prompt library instance
prompt_library = PromptLibrary()
