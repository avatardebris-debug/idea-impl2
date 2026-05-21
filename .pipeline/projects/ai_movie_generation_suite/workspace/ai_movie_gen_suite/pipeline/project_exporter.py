"""Project Exporter — writes phase 2/4 artifacts to a project directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_movie_gen_suite.config import SuiteConfig
from ai_movie_gen_suite.models import (
    AnimaticAudioCues,
    AnimaticTimeline,
    CharacterMoodBoard,
    CharacterRegistry,
    CharacterSheetPrompt,
    SceneDescriptionCollection,
    SceneMoodBoard,
    SceneStoryboardPrompts,
    Script,
)
from ai_movie_gen_suite.stages.animatic_builder import AnimaticTimelineBuilder
from ai_movie_gen_suite.stages.character_consistency import CharacterConsistencyEngine
from ai_movie_gen_suite.stages.mood_board_generator import MoodBoardGenerator
from ai_movie_gen_suite.stages.storyboard_prompt_generator import StoryboardPromptGenerator


class ProjectExporter:
    """Generates and writes storyboard prompts, mood boards, and animatic files."""

    def __init__(
        self,
        project_dir: Path,
        script: Script,
        character_registry: CharacterRegistry,
        scene_descriptions: SceneDescriptionCollection,
        tone: str = "",
        suite_config: Optional[SuiteConfig] = None,
    ):
        self.project_dir = Path(project_dir)
        self.script = script
        self.character_registry = character_registry
        self.scene_descriptions = scene_descriptions
        self.tone = tone
        self.config = suite_config or SuiteConfig()

    def export_phase2(self) -> Tuple[Dict[str, SceneStoryboardPrompts], Dict[str, Any]]:
        """Write characters.json, storyboard_prompts/, mood_boards/."""
        consistency = CharacterConsistencyEngine(
            self.character_registry,
            script=self.script,
            tone=self.tone,
        )
        enriched = consistency.enrich_registry()
        sheets = consistency.generate_all_sheets()

        storyboard_gen = StoryboardPromptGenerator(
            script=self.script,
            scene_descriptions=self.scene_descriptions,
            character_registry=enriched,
            tone=self.tone,
        )
        storyboards = storyboard_gen.generate_all()

        mood_gen = MoodBoardGenerator(
            character_registry=enriched,
            character_sheets=sheets,
            storyboard_prompts=storyboards,
            tone=self.tone,
        )
        char_boards = mood_gen.generate_character_boards()
        scene_boards = mood_gen.generate_scene_boards()

        self._write_characters(enriched, sheets)
        self._write_storyboard_prompts(storyboards)
        self._write_mood_boards(char_boards, scene_boards)

        return storyboards, {
            "character_sheets": sheets,
            "character_mood_boards": char_boards,
            "scene_mood_boards": scene_boards,
        }

    def export_phase4(
        self,
        storyboards: Dict[str, SceneStoryboardPrompts],
        manual_overrides: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Write animatic/ timeline, audio cues, and preview manifest."""
        builder = AnimaticTimelineBuilder(
            script=self.script,
            storyboard_prompts=storyboards,
            tone=self.tone,
            manual_overrides=manual_overrides,
        )
        timeline = builder.build_timeline()
        audio = builder.build_audio_cues(timeline)
        preview = builder.build_preview_manifest(timeline)

        animatic_dir = self.project_dir / self.config.animatic_dir
        animatic_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(animatic_dir / "timeline.json", timeline.model_dump())
        self._write_json(animatic_dir / "audio_cues.json", audio.model_dump())
        self._write_json(animatic_dir / "preview_manifest.json", preview)

        return {
            "timeline": timeline,
            "audio_cues": audio,
            "preview_manifest": preview,
        }

    def export_visual_and_animatic(
        self,
        manual_overrides: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Run phase 2 then phase 4 export in one call."""
        storyboards, phase2_meta = self.export_phase2()
        phase4_meta = self.export_phase4(storyboards, manual_overrides=manual_overrides)
        return {"phase2": phase2_meta, "phase4": phase4_meta, "storyboards": storyboards}

    def _write_characters(
        self,
        registry: CharacterRegistry,
        sheets: List[CharacterSheetPrompt],
    ) -> None:
        sheet_by_id = {s.character_id: s for s in sheets}
        data = registry.model_dump()
        for char in data.get("characters", []):
            sheet = sheet_by_id.get(char.get("id", ""))
            if sheet:
                char["character_sheet_prompt"] = sheet.prompt
                char["character_sheet_negative_prompt"] = sheet.negative_prompt
                char["character_sheet_target_model"] = sheet.target_model.value
        self._write_json(self.project_dir / "characters.json", data)

    def _write_storyboard_prompts(
        self,
        storyboards: Dict[str, SceneStoryboardPrompts],
    ) -> None:
        out_dir = self.project_dir / self.config.storyboard_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        for scene_id, sb in storyboards.items():
            self._write_json(out_dir / f"{scene_id}.json", sb.model_dump())

    def _write_mood_boards(
        self,
        char_boards: Dict[str, CharacterMoodBoard],
        scene_boards: Dict[str, SceneMoodBoard],
    ) -> None:
        base = self.project_dir / self.config.mood_board_dir
        char_dir = base / "characters"
        scene_dir = base / "scenes"
        char_dir.mkdir(parents=True, exist_ok=True)
        scene_dir.mkdir(parents=True, exist_ok=True)
        for cid, board in char_boards.items():
            self._write_json(char_dir / f"{cid}.json", board.model_dump())
        for sid, board in scene_boards.items():
            self._write_json(scene_dir / f"{sid}.json", board.model_dump())

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
