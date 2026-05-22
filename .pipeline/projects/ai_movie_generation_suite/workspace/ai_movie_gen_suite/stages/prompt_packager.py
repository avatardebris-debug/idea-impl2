"""Prompt Packager — combines storyboard prompts with character and scene data."""

from __future__ import annotations

from ai_movie_gen_suite.models import (
    CharacterRegistry,
    SceneDescriptionCollection,
    VideoShot,
)


class PromptPackager:
    """Combines a storyboard prompt with character visual anchors and scene details."""

    @staticmethod
    def pack(
        shot: VideoShot,
        characters: CharacterRegistry,
        scenes: SceneDescriptionCollection,
    ) -> str:
        """Return a generation-ready prompt string for the given shot."""
        parts: list[str] = []

        # 1. Storyboard prompt (core visual description)
        parts.append(f"Storyboard: {shot.storyboard_prompt_ref}")

        # 2. Character visual anchors from registry
        scene_desc = scenes.get_description(shot.scene_id)
        if scene_desc:
            char_names = getattr(scene_desc, "characters", []) or []
        else:
            char_names = []

        character_anchors: list[str] = []
        for name in char_names:
            char = characters.get_by_name(name)
            if char:
                anchor = (
                    f"{char.name}: {char.physical_description}"
                    f" Wardrobe: {char.costume_notes}"
                )
                character_anchors.append(anchor)

        if character_anchors:
            parts.append("Characters: " + " | ".join(character_anchors))

        # 3. Scene setting details
        if scene_desc:
            setting = getattr(scene_desc, "setting", "") or ""
            mood = getattr(scene_desc, "mood", "") or ""
            if setting:
                parts.append(f"Setting: {setting}")
            if mood:
                parts.append(f"Mood: {mood}")

        # 4. Camera metadata
        parts.append(f"Camera: angle={shot.camera_angle}, movement={shot.camera_movement}")

        return " | ".join(parts)
