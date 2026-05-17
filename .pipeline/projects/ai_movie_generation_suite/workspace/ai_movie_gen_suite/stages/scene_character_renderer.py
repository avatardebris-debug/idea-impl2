"""Scene Character Renderer — Renders each scene with character dialogue and action.

This module provides the SceneCharacterRenderer which takes a Script, BeatSheet,
and CharacterRegistry and produces a fully rendered screenplay with dialogue,
action lines, and character-specific content.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from ai_movie_gen_suite.models import (
    Beat,
    BeatSheet,
    Character,
    CharacterRegistry,
    DialogueLine,
    Script,
    Scene,
)

logger = logging.getLogger(__name__)


class RenderedScene:
    """A fully rendered scene with dialogue and action."""

    def __init__(
        self,
        scene: Scene,
        action_lines: List[str],
        dialogue_lines: List[DialogueLine],
        character_notes: Dict[str, str],
    ):
        self.scene = scene
        self.action_lines = action_lines
        self.dialogue_lines = dialogue_lines
        self.character_notes = character_notes  # char_name -> notes

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scene_id": self.scene.scene_id,
            "scene_heading": self.scene.scene_heading,
            "action": "\n".join(self.action_lines),
            "dialogue": [dl.model_dump() for dl in self.dialogue_lines],
            "character_notes": self.character_notes,
        }


class RenderedScript:
    """Collection of rendered scenes."""

    def __init__(self, script: Script):
        self.script = script
        self.rendered_scenes: List[RenderedScene] = []

    def add_rendered_scene(self, rendered: RenderedScene) -> None:
        self.rendered_scenes.append(rendered)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "title": self.script.title,
            "logline": self.script.logline,
            "genre": self.script.genre,
            "scenes": [rs.to_dict() for rs in self.rendered_scenes],
        }

    def to_screenplay_format(self) -> str:
        """Render the screenplay in standard screenplay format."""
        lines = [
            f"TITLE: {self.script.title}",
            f"GENRE: {self.script.genre}",
            f"LOGLINE: {self.script.logline}",
            "",
        ]

        for rendered in self.rendered_scenes:
            lines.append(rendered.scene.scene_heading)
            lines.append("")

            # Action lines
            for action in rendered.action_lines:
                lines.append(f"    {action}")
            lines.append("")

            # Dialogue
            for dl in rendered.dialogue_lines:
                lines.append(f"    {dl.character_name}")
                if dl.parenthetical:
                    lines.append(f"        ({dl.parenthetical})")
                lines.append(f"        {dl.text}")
                lines.append("")

        return "\n".join(lines)


class SceneCharacterRenderer:
    """Renders each scene with character dialogue and action.

    This renderer takes a Script, BeatSheet, and CharacterRegistry and produces
    a fully rendered screenplay with dialogue, action lines, and character-specific
    content.
    """

    def __init__(
        self,
        script: Script,
        beat_sheet: Optional[BeatSheet] = None,
        character_registry: Optional[CharacterRegistry] = None,
    ):
        self.script = script
        self.beat_sheet = beat_sheet
        self.character_registry = character_registry

    def render(self) -> RenderedScript:
        """Render the full screenplay with dialogue and action.

        Returns:
            RenderedScript with fully rendered scenes.
        """
        rendered_script = RenderedScript(self.script)

        for scene in self.script.scenes:
            rendered_scene = self._render_scene(scene)
            rendered_script.add_rendered_scene(rendered_scene)

        return rendered_script

    def _render_scene(self, scene: Scene) -> RenderedScene:
        """Render a single scene with dialogue and action."""
        action_lines = self._generate_action_lines(scene)
        dialogue_lines = self._generate_dialogue(scene)
        character_notes = self._generate_character_notes(scene)

        return RenderedScene(
            scene=scene,
            action_lines=action_lines,
            dialogue_lines=dialogue_lines,
            character_notes=character_notes,
        )

    def _generate_action_lines(self, scene: Scene) -> List[str]:
        """Generate action lines for a scene."""
        action_lines = []

        # Use beat reference if available
        if scene.beat_ref and self.beat_sheet:
            beat = self._find_beat_by_name(scene.beat_ref)
            if beat:
                action_lines.append(f"[{beat.summary}]")

        # Add character-specific action
        if scene.characters_present:
            for char_name in scene.characters_present:
                char = self._find_character(char_name)
                if char:
                    action_lines.append(f"{char.name} enters the scene, {char.personality_traits[0] if char.personality_traits else 'determined'}.")

        # Default action if none generated
        if not action_lines:
            action_lines.append(f"Scene action for {scene.scene_heading}.")

        return action_lines

    def _generate_dialogue(self, scene: Scene) -> List[DialogueLine]:
        """Generate dialogue for a scene."""
        dialogue_lines = []

        for char_name in scene.characters_present:
            char = self._find_character(char_name)
            if char:
                # Generate dialogue based on character role and scene context
                dialogue = self._generate_character_dialogue(char, scene)
                if dialogue:
                    dialogue_lines.append(
                        DialogueLine(
                            character_name=char.name,
                            character_id=char.id,
                            text=dialogue,
                        )
                    )

        return dialogue_lines

    def _generate_character_dialogue(self, character: Character, scene: Scene) -> str:
        """Generate dialogue for a specific character in a scene."""
        # Use character's voice notes to inform dialogue
        voice = character.voice_notes.lower() if character.voice_notes else ""

        # Generate dialogue based on role
        if character.role.value == "protagonist":
            return f"I need to figure out what to do next."
        elif character.role.value == "antagonist":
            return f"You can't stop what's coming."
        elif character.role.value == "mentor":
            return f"Remember what I told you about this."
        elif character.role.value == "ally":
            return f"I've got your back."
        elif character.role.value == "sidekick":
            return f"Wow, this is incredible!"
        else:
            return f"This is important."

    def _generate_character_notes(self, scene: Scene) -> Dict[str, str]:
        """Generate character notes for a scene."""
        notes = {}

        for char_name in scene.characters_present:
            char = self._find_character(char_name)
            if char:
                notes[char.name] = (
                    f"Role: {char.role.value}\n"
                    f"Backstory: {char.backstory}\n"
                    f"Visual Anchor: {char.visual_anchor}"
                )

        return notes

    def _find_character(self, name: str) -> Optional[Character]:
        """Find a character by name in the registry."""
        if not self.character_registry:
            return None
        return self.character_registry.get_by_name(name)

    def _find_beat_by_name(self, beat_name: str) -> Optional[Beat]:
        """Find a beat by name in the beat sheet."""
        if not self.beat_sheet:
            return None
        for beat in self.beat_sheet.beats:
            if beat.beat_name == beat_name:
                return beat
        return None

    def render_with_llm(self, llm_client=None, prompt_template: str = "") -> RenderedScript:
        """Render the screenplay using an LLM for richer content.

        Args:
            llm_client: An LLM client with a .generate() method.
            prompt_template: Jinja2 template for the rendering prompt.

        Returns:
            RenderedScript with LLM-generated content.
        """
        if llm_client is None:
            return self.render()

        prompt = self._build_llm_prompt(prompt_template)
        response = llm_client.generate(prompt)
        return self._parse_llm_response(response)

    def _build_llm_prompt(self, template: str = "") -> str:
        """Build the prompt for LLM rendering."""
        if template:
            return template.format(
                script=self.script.model_dump(),
                beat_sheet=self.beat_sheet.model_dump() if self.beat_sheet else {},
                characters=self.character_registry.model_dump() if self.character_registry else {},
            )

        prompt = f"Render the screenplay for '{self.script.title}' in standard format.\n\n"
        prompt += f"Genre: {self.script.genre}\n"
        prompt += f"Logline: {self.script.logline}\n\n"

        if self.beat_sheet:
            prompt += "Beat Sheet:\n"
            for beat in self.beat_sheet.beats:
                prompt += f"  {beat.beat_number}. {beat.beat_name}: {beat.summary}\n"

        if self.character_registry:
            prompt += "\nCharacters:\n"
            for char in self.character_registry.characters:
                prompt += f"  - {char.name} ({char.role.value})\n"

        prompt += "\nWrite the full screenplay with dialogue and action."
        return prompt

    def _parse_llm_response(self, response: str) -> RenderedScript:
        """Parse LLM response into a RenderedScript."""
        rendered_script = RenderedScript(self.script)

        # Simple parsing: split by scene headings
        current_scene = None
        current_action = []
        current_dialogue = []

        for line in response.split("\n"):
            line = line.strip()
            if line.upper().startswith(("INT.", "EXT.", "INT/EXT.")):
                # Save previous scene
                if current_scene:
                    rendered_scene = RenderedScene(
                        scene=current_scene,
                        action_lines=current_action,
                        dialogue_lines=current_dialogue,
                        character_notes={},
                    )
                    rendered_script.add_rendered_scene(rendered_scene)

                # Start new scene
                scene_id = f"SC-{len(rendered_script.rendered_scenes) + 1:03d}"
                current_scene = Scene(
                    scene_id=scene_id,
                    scene_heading=line,
                    action="",
                    characters_present=[],
                    dialogue_lines=[],
                )
                current_action = []
                current_dialogue = []
            elif current_scene:
                if line.startswith("(") and ")" in line:
                    # Parenthetical - skip for now
                    pass
                elif line.isupper() and not line.startswith("("):
                    # Character name
                    pass
                else:
                    # Action or dialogue
                    current_action.append(line)

        # Save last scene
        if current_scene:
            rendered_scene = RenderedScene(
                scene=current_scene,
                action_lines=current_action,
                dialogue_lines=current_dialogue,
                character_notes={},
            )
            rendered_script.add_rendered_scene(rendered_scene)

        return rendered_script
