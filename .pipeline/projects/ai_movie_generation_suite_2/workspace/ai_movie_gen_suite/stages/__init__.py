"""AI Movie Generation Suite - Pipeline Stages.

This package contains all pipeline stages for the AI movie generation workflow.
Each stage is responsible for a specific part of the creative pipeline.

Stages:
    - Stage 1: Concept & Beat Sheet Generation
    - Stage 2: Character Registry Generation
    - Stage 3: Script Writing
    - Stage 4: Scene Description Generation
    - Stage 5: Music Composition
    - Stage 6: Post-Production Planning
"""

from ai_movie_gen_suite.stages.base import BaseStageGenerator
from ai_movie_gen_suite.stages.stage1_beat_sheet import Stage1BeatSheetGenerator
from ai_movie_gen_suite.stages.stage2_characters import Stage2CharacterGenerator
from ai_movie_gen_suite.stages.stage3_script import Stage3ScriptWriter
from ai_movie_gen_suite.stages.stage4_scene_descriptions import Stage4SceneDescriptionGenerator
from ai_movie_gen_suite.stages.stage5_music import Stage5MusicComposer
from ai_movie_gen_suite.stages.stage6_post_production import Stage6PostProductionPlanner

__all__ = [
    "BaseStageGenerator",
    "Stage1BeatSheetGenerator",
    "Stage2CharacterGenerator",
    "Stage3ScriptWriter",
    "Stage4SceneDescriptionGenerator",
    "Stage5MusicComposer",
    "Stage6PostProductionPlanner",
]
