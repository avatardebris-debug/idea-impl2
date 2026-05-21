"""Mood Board Generator — aggregates prompts into per-character and per-scene boards."""

from __future__ import annotations

from typing import Dict, List

from ai_movie_gen_suite.models import (
    CharacterMoodBoard,
    CharacterRegistry,
    CharacterSheetPrompt,
    MoodBoardReference,
    SceneMoodBoard,
    SceneStoryboardPrompts,
)


class MoodBoardGenerator:
    """Builds mood boards from character sheets and storyboard prompts."""

    def __init__(
        self,
        character_registry: CharacterRegistry,
        character_sheets: List[CharacterSheetPrompt],
        storyboard_prompts: Dict[str, SceneStoryboardPrompts],
        tone: str = "",
    ):
        self.character_registry = character_registry
        self.character_sheets = {s.character_id: s for s in character_sheets}
        self.storyboard_prompts = storyboard_prompts
        self.tone = tone

    def generate_character_boards(self) -> Dict[str, CharacterMoodBoard]:
        """One mood board per character."""
        boards: Dict[str, CharacterMoodBoard] = {}
        for char in self.character_registry.characters:
            sheet = self.character_sheets.get(char.id)
            sheet_prompt = sheet.prompt if sheet else ""
            refs = [
                MoodBoardReference(
                    label="character_sheet",
                    prompt=sheet_prompt,
                    notes="Primary reference for AI image generation",
                )
            ]
            if char.visual_anchor:
                refs.append(
                    MoodBoardReference(
                        label="visual_anchor",
                        prompt=char.visual_anchor,
                        notes="Key visual identifier",
                    )
                )
            boards[char.id] = CharacterMoodBoard(
                character_id=char.id,
                character_name=char.name,
                character_sheet_prompt=sheet_prompt,
                references=refs,
                style_tags=self._style_tags(),
            )
        return boards

    def generate_scene_boards(self) -> Dict[str, SceneMoodBoard]:
        """One mood board per scene, referencing storyboard prompts."""
        boards: Dict[str, SceneMoodBoard] = {}
        for scene_id, sb in self.storyboard_prompts.items():
            refs = [
                MoodBoardReference(
                    label=f"frame_{p.frame_index}",
                    prompt=p.prompt,
                    notes=f"{p.camera} | {p.mood}",
                )
                for p in sb.prompts
            ]
            boards[scene_id] = SceneMoodBoard(
                scene_id=scene_id,
                scene_heading=sb.scene_heading,
                storyboard_frame_count=len(sb.prompts),
                references=refs,
                style_tags=self._style_tags(),
            )
        return boards

    def _style_tags(self) -> List[str]:
        tags = ["cinematic", "storyboard"]
        if self.tone:
            tags.append(self.tone.lower().replace(" ", "_"))
        return tags
