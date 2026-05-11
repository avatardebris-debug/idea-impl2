"""Pipeline orchestrator for the AI Movie Generation Suite.

Ties all stage generators together into a configurable pipeline that
processes a project through all stages in order.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from ai_movie_gen_suite.config import AppConfig
from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator
from ai_movie_gen_suite.stages.stage1_beat_sheet import Stage1BeatSheetGenerator
from ai_movie_gen_suite.stages.stage2_characters import Stage2CharacterGenerator
from ai_movie_gen_suite.stages.stage3_script import Stage3ScriptWriter
from ai_movie_gen_suite.stages.stage4_scene_descriptions import Stage4SceneDescriptionGenerator
from ai_movie_gen_suite.stages.stage5_music import Stage5MusicComposer
from ai_movie_gen_suite.stages.stage6_post_production import Stage6PostProductionPlanner

logger = logging.getLogger(__name__)


class MoviePipeline:
    """Orchestrates the AI movie generation pipeline.

    Manages the sequence of stage generators and executes them in order
    to transform a user prompt into a complete movie project.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        stages: Optional[List[Type[BaseStageGenerator]]] = None,
        config: Optional[AppConfig] = None,
    ):
        """Initialize the pipeline.

        Args:
            llm_client: LLM client for generating content. Creates default if None.
            stages: List of stage generator classes to use. Uses default pipeline if None.
            config: Application configuration. Uses default if None.
        """
        self.config = config or AppConfig()
        self.llm_client = llm_client or LLMClient(self.config.llm)
        self.stages: List[BaseStageGenerator] = []
        self._stage_instances: Dict[str, BaseStageGenerator] = {}

        # Use custom stages if provided
        if stages:
            self.stages = [stage(config=self.config) for stage in stages]
        else:
            self.stages = [
                Stage1BeatSheetGenerator(config=self.config),
                Stage2CharacterGenerator(config=self.config),
                Stage3ScriptWriter(config=self.config),
                Stage4SceneDescriptionGenerator(config=self.config),
                Stage5MusicComposer(config=self.config),
                Stage6PostProductionPlanner(config=self.config),
            ]

        # Register stage instances for lookup
        for stage in self.stages:
            self._stage_instances[stage.__class__.__name__] = stage

    def run(self, project: Project) -> Project:
        """Execute the full pipeline on a project.

        Args:
            project: Project with initial concept (title + logline).

        Returns:
            Updated project with all stages completed.
        """
        logger.info(f"Starting pipeline for '{project.title}'")

        for stage in self.stages:
            logger.info(f"Running stage: {stage.__class__.__name__}")
            project = stage.execute(project)
            logger.info(f"Stage {stage.__class__.__name__} complete")

        logger.info(f"Pipeline complete for '{project.title}'")
        return project

    def run_stage(self, project: Project, stage_name: str) -> Project:
        """Run a specific stage by name.

        Args:
            project: Current project state.
            stage_name: Name of the stage to run (class name).

        Returns:
            Updated project after the stage completes.
        """
        if stage_name not in self._stage_instances:
            raise ValueError(f"Unknown stage: {stage_name}")

        stage = self._stage_instances[stage_name]
        logger.info(f"Running specific stage: {stage_name}")
        project = stage.execute(project)
        logger.info(f"Stage {stage_name} complete")
        return project

    def get_stage_names(self) -> List[str]:
        """Get the names of all stages in the pipeline.

        Returns:
            List of stage class names.
        """
        return [stage.__class__.__name__ for stage in self.stages]
