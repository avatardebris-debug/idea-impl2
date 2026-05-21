"""Storyboard Prompt Generator — per-scene AI image prompts from screenplay metadata."""

from __future__ import annotations

from typing import Dict, List, Optional

from ai_movie_gen_suite.models import (
    CharacterRegistry,
    ImageModelTarget,
    Scene,
    SceneDescription,
    SceneDescriptionCollection,
    SceneStoryboardPrompts,
    Script,
    StoryboardFramePrompt,
)


class StoryboardPromptGenerator:
    """Generates 1–3 storyboard frame prompts per scene."""

    def __init__(
        self,
        script: Script,
        scene_descriptions: SceneDescriptionCollection,
        character_registry: Optional[CharacterRegistry] = None,
        tone: str = "",
        target_model: ImageModelTarget = ImageModelTarget.SDXL,
    ):
        self.script = script
        self.scene_descriptions = scene_descriptions
        self.character_registry = character_registry
        self.tone = tone or script.genre
        self.target_model = target_model

    def generate_all(self) -> Dict[str, SceneStoryboardPrompts]:
        """Generate storyboard prompts for every scene in the script."""
        result: Dict[str, SceneStoryboardPrompts] = {}
        for scene in self.script.scenes:
            desc = self.scene_descriptions.get_description(scene.scene_id)
            if desc is None:
                desc = SceneDescription(scene_id=scene.scene_id, setting=scene.scene_heading)
            result[scene.scene_id] = self.generate_for_scene(scene, desc)
        return result

    def generate_for_scene(
        self,
        scene: Scene,
        desc: SceneDescription,
    ) -> SceneStoryboardPrompts:
        """Generate 1–3 frame prompts for a single scene."""
        char_names = self._resolve_character_names(scene)
        char_appearance = self._character_appearance_text(char_names)
        style = desc.visual_style or f"cinematic, {self.tone}"
        base_negative = "blurry, low quality, deformed, watermark, text"

        frames: List[StoryboardFramePrompt] = []

        # Frame 1: establishing
        frames.append(
            StoryboardFramePrompt(
                frame_index=1,
                prompt=(
                    f"Storyboard frame, {scene.scene_heading}. {desc.setting}. "
                    f"Lighting: {desc.lighting}. Mood: {desc.mood}. "
                    f"Camera: {desc.camera_notes or 'wide establishing shot'}. "
                    f"Characters: {char_appearance or 'environment focus'}. Style: {style}."
                ),
                negative_prompt=base_negative,
                camera=desc.camera_notes or "wide shot",
                lighting=desc.lighting,
                mood=desc.mood,
                style=style,
                characters=char_names,
                parameters={"aspect_ratio": "16:9", "shot_type": "establishing"},
            )
        )

        # Frame 2: medium / character focus (if dialogue or characters present)
        if char_names or scene.dialogue_lines:
            frames.append(
                StoryboardFramePrompt(
                    frame_index=2,
                    prompt=(
                        f"Storyboard frame, {scene.scene_heading}. Medium shot. "
                        f"{char_appearance}. Action: {scene.action[:200]}. "
                        f"Mood: {desc.mood}. Lighting: {desc.lighting}. Style: {style}."
                    ),
                    negative_prompt=base_negative,
                    camera="medium shot, eye level",
                    lighting=desc.lighting,
                    mood=desc.mood,
                    style=style,
                    characters=char_names,
                    parameters={"aspect_ratio": "16:9", "shot_type": "medium"},
                )
            )

        # Frame 3: detail / tension (if action beats exist)
        if desc.action_beats:
            beats_text = "; ".join(desc.action_beats[:2])
            frames.append(
                StoryboardFramePrompt(
                    frame_index=3,
                    prompt=(
                        f"Storyboard frame, {scene.scene_heading}. Detail or tension beat. "
                        f"{beats_text}. Mood: {desc.mood}. Style: {style}."
                    ),
                    negative_prompt=base_negative,
                    camera="close-up or dutch angle",
                    lighting=desc.lighting,
                    mood=desc.mood,
                    style=style,
                    characters=char_names,
                    parameters={"aspect_ratio": "16:9", "shot_type": "detail"},
                )
            )

        return SceneStoryboardPrompts(
            scene_id=scene.scene_id,
            scene_heading=scene.scene_heading,
            target_model=self.target_model,
            beat_ref=scene.beat_ref,
            prompts=frames[:3],
        )

    def _resolve_character_names(self, scene: Scene) -> List[str]:
        names: List[str] = []
        if scene.characters_present:
            names.extend(scene.characters_present)
        for line in scene.dialogue_lines:
            if line.character_name not in names:
                names.append(line.character_name)
        return names

    def _character_appearance_text(self, names: List[str]) -> str:
        if not self.character_registry or not names:
            return ""
        parts: List[str] = []
        for name in names:
            char = self.character_registry.get_by_name(name)
            if char:
                parts.append(
                    f"{char.name}: {char.physical_description or char.visual_anchor}"
                )
        return "; ".join(parts)
