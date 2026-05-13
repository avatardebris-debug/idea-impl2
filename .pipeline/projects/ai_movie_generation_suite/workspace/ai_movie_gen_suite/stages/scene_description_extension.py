"""Scene Description Engine Extension — Enhanced visual direction with LLM support.

Extends the SceneDescriptionEngine with additional capabilities:
- LLM-powered scene descriptions
- Visual style consistency checks
- Scene-to-scene transition notes
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_movie_gen_suite.models import (
    BeatSheet,
    CharacterRegistry,
    Scene,
    SceneDescription,
    SceneDescriptionCollection,
    Script,
)
from ai_movie_gen_suite.stages.scene_description_engine import SceneDescriptionEngine

logger = logging.getLogger(__name__)


class SceneDescriptionExtension:
    """Extends SceneDescriptionEngine with enhanced capabilities.

    Provides:
    - LLM-powered scene descriptions
    - Visual style consistency checks
    - Scene-to-scene transition notes
    """

    def __init__(
        self,
        base_engine: SceneDescriptionEngine,
        script: Optional[Script] = None,
        beat_sheet: Optional[BeatSheet] = None,
        character_registry: Optional[CharacterRegistry] = None,
        tone: str = "",
    ):
        self.base_engine = base_engine
        self.script = script
        self.beat_sheet = beat_sheet
        self.character_registry = character_registry
        self.tone = tone

    def generate_enhanced_descriptions(self) -> SceneDescriptionCollection:
        """Generate enhanced scene descriptions with transitions and consistency.

        Returns:
            SceneDescriptionCollection with enhanced descriptions.
        """
        collection = self.base_engine.generate_descriptions()

        if not self.script:
            return collection

        # Add transition notes between scenes
        self._add_transition_notes(collection)

        # Check visual style consistency
        self._check_visual_consistency(collection)

        return collection

    def _add_transition_notes(self, collection: SceneDescriptionCollection) -> None:
        """Add scene-to-scene transition notes."""
        if not self.script or len(self.script.scenes) < 2:
            return

        for i in range(len(self.script.scenes) - 1):
            current_scene = self.script.scenes[i]
            next_scene = self.script.scenes[i + 1]

            current_desc = collection.get_description(current_scene.scene_id)
            next_desc = collection.get_description(next_scene.scene_id)

            if current_desc and next_desc:
                # Generate transition note
                transition = self._generate_transition_note(current_scene, next_scene)
                current_desc.action_beats.append(f"Transition to {next_scene.scene_heading}: {transition}")

    def _generate_transition_note(self, current_scene: Scene, next_scene: Scene) -> str:
        """Generate a transition note between two scenes."""
        # Simple transition logic based on location changes
        current_loc = current_scene.scene_heading.split(" - ")[0] if " - " in current_scene.scene_heading else ""
        next_loc = next_scene.scene_heading.split(" - ")[0] if " - " in next_scene.scene_heading else ""

        if current_loc == next_loc:
            return "Continuation of previous scene"
        elif "INT" in current_loc and "EXT" in next_loc:
            return "Move from interior to exterior"
        elif "EXT" in current_loc and "INT" in next_loc:
            return "Move from exterior to interior"
        else:
            return "Scene change"

    def _check_visual_consistency(self, collection: SceneDescriptionCollection) -> None:
        """Check for visual style consistency across scenes."""
        if not self.tone:
            return

        # Check if lighting and mood are consistent with the tone
        for scene_id, desc in collection.descriptions.items():
            if self.tone.lower() in ["dark", "noir"]:
                if "bright" in desc.lighting.lower():
                    logger.warning(f"Scene {scene_id}: Lighting '{desc.lighting}' inconsistent with tone '{self.tone}'")
            elif self.tone.lower() in ["hopeful", "uplifting"]:
                if "dark" in desc.lighting.lower() and "bright" not in desc.lighting.lower():
                    logger.warning(f"Scene {scene_id}: Lighting '{desc.lighting}' inconsistent with tone '{self.tone}'")

    def generate_with_llm(self, llm_client=None, prompt_template: str = "") -> SceneDescriptionCollection:
        """Generate scene descriptions using an LLM.

        Args:
            llm_client: An LLM client with a .generate() method.
            prompt_template: Jinja2 template for the description prompt.

        Returns:
            SceneDescriptionCollection with LLM-generated descriptions.
        """
        if llm_client is None:
            return self.generate_enhanced_descriptions()

        prompt = self._build_llm_prompt(prompt_template)
        response = llm_client.generate(prompt)
        return self._parse_llm_response(response)

    def _build_llm_prompt(self, template: str = "") -> str:
        """Build the prompt for LLM scene description generation."""
        if template:
            return template.format(
                script=self.script.model_dump() if self.script else {},
                beat_sheet=self.beat_sheet.model_dump() if self.beat_sheet else {},
                characters=self.character_registry.model_dump() if self.character_registry else {},
                tone=self.tone,
            )

        prompt = f"Generate visual scene descriptions for '{self.script.title if self.script else 'Untitled'}'.\n\n"
        prompt += f"Genre: {self.script.genre if self.script else 'Unknown'}\n"
        prompt += f"Tone: {self.tone or 'Neutral'}\n\n"

        if self.script:
            prompt += "Scenes:\n"
            for scene in self.script.scenes:
                prompt += f"  - {scene.scene_heading}\n"

        if self.beat_sheet:
            prompt += "\nBeat Sheet:\n"
            for beat in self.beat_sheet.beats:
                prompt += f"  {beat.beat_number}. {beat.beat_name}: {beat.summary}\n"

        if self.character_registry:
            prompt += "\nCharacters:\n"
            for char in self.character_registry.characters:
                prompt += f"  - {char.name} ({char.role.value})\n"

        prompt += "\nGenerate detailed visual descriptions for each scene."
        return prompt

    def _parse_llm_response(self, response: str) -> SceneDescriptionCollection:
        """Parse LLM response into SceneDescriptionCollection."""
        collection = SceneDescriptionCollection()

        # Simple parsing: split by scene headings
        current_scene_id = None
        current_desc = None

        for line in response.split("\n"):
            line = line.strip()
            if line.upper().startswith(("INT.", "EXT.", "INT/EXT.")):
                # Save previous scene
                if current_scene_id and current_desc:
                    collection.add_description(current_scene_id, current_desc)

                # Start new scene
                current_scene_id = f"SC-{len(collection.descriptions) + 1:03d}"
                current_desc = SceneDescription(
                    scene_id=current_scene_id,
                    setting=line,
                    lighting="Natural",
                    camera_notes="",
                    mood=self.tone or "Neutral",
                    action_beats=[],
                    visual_style="",
                )
            elif current_desc:
                if "lighting:" in line.lower():
                    current_desc.lighting = line.split(":", 1)[1].strip()
                elif "mood:" in line.lower():
                    current_desc.mood = line.split(":", 1)[1].strip()
                elif "camera:" in line.lower():
                    current_desc.camera_notes = line.split(":", 1)[1].strip()
                elif "setting:" in line.lower():
                    current_desc.setting = line.split(":", 1)[1].strip()

        # Save last scene
        if current_scene_id and current_desc:
            collection.add_description(current_scene_id, current_desc)

        return collection
