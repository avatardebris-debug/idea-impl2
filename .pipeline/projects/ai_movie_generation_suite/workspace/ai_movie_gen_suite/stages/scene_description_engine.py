"""Scene Description Engine — Visual direction for each scene.

Generates detailed visual descriptions for each scene, including setting,
lighting, camera notes, mood, and action beats.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ai_movie_gen_suite.models import (
    BeatSheet,
    CharacterRegistry,
    Scene,
    SceneDescription,
    SceneDescriptionCollection,
    Script,
)


class SceneDescriptionEngine:
    """Generates visual descriptions for each scene in the screenplay."""

    def __init__(
        self,
        script: Optional[Script] = None,
        beat_sheet: Optional[BeatSheet] = None,
        character_registry: Optional[CharacterRegistry] = None,
        tone: str = "",
    ):
        self.script = script
        self.beat_sheet = beat_sheet
        self.character_registry = character_registry
        self.tone = tone

    def generate_descriptions(self) -> SceneDescriptionCollection:
        """Generate visual descriptions for all scenes in the script."""
        collection = SceneDescriptionCollection()

        if self.script is None:
            return collection

        for scene in self.script.scenes:
            desc = self._generate_scene_description(scene)
            collection.add_description(scene.scene_id, desc)

        return collection

    def _generate_scene_description(self, scene: Scene) -> SceneDescription:
        """Generate a visual description for a single scene."""
        # Determine mood based on scene heading and context
        mood = self._infer_mood(scene)
        lighting = self._infer_lighting(scene)
        camera_notes = self._infer_camera_notes(scene)
        action_beats = self._infer_action_beats(scene)

        return SceneDescription(
            scene_id=scene.scene_id,
            setting=scene.scene_heading,
            lighting=lighting,
            camera_notes=camera_notes,
            mood=mood,
            action_beats=action_beats,
            visual_style=self.tone if self.tone else "cinematic",
        )

    def _infer_mood(self, scene: Scene) -> str:
        """Infer the mood of a scene from its heading and context."""
        heading = scene.scene_heading.upper()

        if "NIGHT" in heading or "DARK" in heading:
            return "tense, mysterious"
        elif "DAY" in heading or "SUN" in heading:
            return "bright, hopeful"
        elif "RAIN" in heading or "STORM" in heading:
            return "dramatic, somber"
        elif "INT" in heading:
            return "intimate, confined"
        else:
            return "open, expansive"

    def _infer_lighting(self, scene: Scene) -> str:
        """Infer lighting for a scene."""
        heading = scene.scene_heading.upper()

        if "NIGHT" in heading:
            return "low-key, high contrast, practical lights"
        elif "DAY" in heading:
            return "natural, soft, diffused"
        elif "INT" in heading:
            return "mixed, practical sources"
        else:
            return "natural, directional"

    def _infer_camera_notes(self, scene: Scene) -> str:
        """Infer camera notes for a scene."""
        heading = scene.scene_heading.upper()

        if "INT" in heading:
            return "handheld, close-ups, shallow depth of field"
        elif "EXT" in heading:
            return "wide shots, establishing shots, crane"
        else:
            return "mixed, dynamic"

    def _infer_action_beats(self, scene: Scene) -> List[str]:
        """Infer action beats for a scene."""
        beats = []

        if scene.action:
            # Extract key actions from the scene action
            words = scene.action.split()
            if len(words) > 10:
                beats.append(f"Establish the setting ({words[0]} {words[1]} {words[2]}...)")
                beats.append(f"Introduce the conflict ({words[5]} {words[6]} {words[7]}...)")
            else:
                beats.append(f"Action: {scene.action[:50]}...")

        beats.append("Character interaction")
        beats.append("Emotional beat")

        return beats

    def generate_with_llm(self, llm_client=None, prompt_template: str = "") -> SceneDescriptionCollection:
        """Generate descriptions using an LLM (optional, for richer content).

        Args:
            llm_client: An LLM client with a .generate() method.
            prompt_template: Jinja2 template for the scene description prompt.

        Returns:
            SceneDescriptionCollection with LLM-generated content.
        """
        if llm_client is None:
            return self.generate_descriptions()

        collection = SceneDescriptionCollection()

        if self.script is None:
            return collection

        for scene in self.script.scenes:
            prompt = self._build_llm_prompt(scene, prompt_template)
            response = llm_client.generate(prompt)
            desc = self._parse_llm_response(scene.scene_id, response)
            collection.add_description(scene.scene_id, desc)

        return collection

    def _build_llm_prompt(self, scene: Scene, template: str = "") -> str:
        """Build the prompt for LLM scene description generation."""
        if template:
            return template.format(
                scene_heading=scene.scene_heading,
                action=scene.action,
                tone=self.tone,
            )

        return (
            f"Generate a visual description for this scene:\n\n"
            f"Scene Heading: {scene.scene_heading}\n"
            f"Action: {scene.action}\n"
            f"Tone: {self.tone or 'Not specified'}\n\n"
            f"Include:\n"
            f"- Setting details\n"
            f"- Lighting\n"
            f"- Camera notes\n"
            f"- Mood\n"
            f"- Action beats\n"
        )

    def _parse_llm_response(self, scene_id: str, response: str) -> SceneDescription:
        """Parse LLM response into a SceneDescription."""
        desc = SceneDescription(
            scene_id=scene_id,
            setting="",
            lighting="",
            camera_notes="",
            mood="",
            action_beats=[],
            visual_style="",
        )

        for line in response.split("\n"):
            line = line.strip()
            if line.lower().startswith("setting:"):
                desc.setting = line.split(":", 1)[1].strip()
            elif line.lower().startswith("lighting:"):
                desc.lighting = line.split(":", 1)[1].strip()
            elif line.lower().startswith("camera notes:"):
                desc.camera_notes = line.split(":", 1)[1].strip()
            elif line.lower().startswith("mood:"):
                desc.mood = line.split(":", 1)[1].strip()
            elif line.lower().startswith("action beats:"):
                desc.action_beats = [b.strip() for b in line.split(":", 1)[1].split(",")]
            elif line.lower().startswith("visual style:"):
                desc.visual_style = line.split(":", 1)[1].strip()

        return desc
