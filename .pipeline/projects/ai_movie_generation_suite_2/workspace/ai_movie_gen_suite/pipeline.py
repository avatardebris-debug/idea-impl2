"""Pipeline orchestrator for the AI Movie Generation Suite.

Ties all stage generators together into a configurable pipeline that
processes a project through all stages in order.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator
from ai_movie_gen_suite.stages.concept_generator import ConceptGenerator
from ai_movie_gen_suite.stages.beat_generator import BeatSheetGenerator
from ai_movie_gen_suite.stages.character_generator import CharacterGenerator
from ai_movie_gen_suite.stages.script_generator import ScriptGenerator
from ai_movie_gen_suite.stages.scene_generator import SceneDescriptionGenerator
from ai_movie_gen_suite.stages.summary_generator import SummaryGenerator
from ai_movie_gen_suite.stages.music_generator import MusicGenerator
from ai_movie_gen_suite.stages.post_production_generator import PostProductionGenerator
from ai_movie_gen_suite.stages.marketing_generator import MarketingGenerator
from ai_movie_gen_suite.stages.distribution_generator import DistributionGenerator

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
    ):
        """Initialize the pipeline.

        Args:
            llm_client: LLM client for generating content. Creates default if None.
            stages: List of stage generator classes to use. Uses default pipeline if None.
        """
        self.llm_client = llm_client or LLMClient()
        self.stages: List[BaseStageGenerator] = []
        self._stage_instances: Dict[str, BaseStageGenerator] = {}

        # Use custom stages if provided
        if stages:
            self.stages = [stage(config=self.llm_client.config) for stage in stages]
        else:
            self.stages = [
                ConceptGenerator(config=self.llm_client.config),
                BeatSheetGenerator(config=self.llm_client.config),
                CharacterGenerator(config=self.llm_client.config),
                ScriptGenerator(config=self.llm_client.config),
                SceneDescriptionGenerator(config=self.llm_client.config),
                SummaryGenerator(config=self.llm_client.config),
                MusicGenerator(config=self.llm_client.config),
                PostProductionGenerator(config=self.llm_client.config),
                MarketingGenerator(config=self.llm_client.config),
                DistributionGenerator(config=self.llm_client.config),
            ]

        # Create stage instances for lookup
        for stage in self.stages:
            self._stage_instances[stage.__class__.__name__] = stage

    def _register_default_stages(self) -> None:
        """Register the default stage generators."""
        pass  # Stages are registered in __init__

    def run(self, project: Project) -> Project:
        """Run the full pipeline on a project.

        Args:
            project: Project to process through the pipeline.

        Returns:
            Updated project with all stages completed.
        """
        logger.info(f"Starting pipeline for project: {project.title or 'Untitled'}")
        project.status = "pipeline_started"

        for i, stage in enumerate(self.stages):
            logger.info(f"Running stage {i + 1}/{len(self.stages)}: {stage.__class__.__name__}")
            try:
                project = stage.execute(project)
                logger.info(f"Stage {stage.__class__.__name__} completed successfully")
            except Exception as e:
                logger.error(f"Stage {stage.__class__.__name__} failed: {e}")
                project.status = f"failed_at_{stage.__class__.__name__.lower()}"
                raise

        project.status = "pipeline_complete"
        logger.info("Pipeline completed successfully")
        return project

    def get_stage(self, stage_name: str) -> Optional[BaseStageGenerator]:
        """Get a stage generator by name.

        Args:
            stage_name: Name of the stage to retrieve.

        Returns:
            Stage generator instance or None if not found.
        """
        return self._stage_instances.get(stage_name)

    def get_available_stages(self) -> List[str]:
        """Get list of available stage names.

        Returns:
            List of stage generator class names.
        """
        return [stage.__class__.__name__ for stage in self.stages]
