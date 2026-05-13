"""Pipeline extension — integrates character consistency into MovieGenerationPipeline.

Adds a `--generate-scene-renders` flag to the pipeline that, when enabled,
runs the SceneCharacterRendererStage after the script is written.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_movie_gen_suite.models import CharacterRegistry, Script

from ai_consistent_char.image_provider import CharacterImageProvider
from ai_consistent_char.models import SceneCharacterRenderCollection
from ai_consistent_char.reference_sheet_generator import ReferenceSheetGenerator
from ai_consistent_char.stages.scene_character_renderer import SceneCharacterRendererStage

logger = logging.getLogger(__name__)


class PipelineExtension:
    """Extends MovieGenerationPipeline with character consistency features.

    Usage:
        extension = PipelineExtension(pipeline)
        extension.add_character_consistency(provider, output_dir)
        pipeline.run()
    """

    def __init__(self, pipeline: Any):
        self.pipeline = pipeline

    def add_character_consistency(
        self,
        provider: CharacterImageProvider,
        output_dir: Path,
        generate_renders: bool = False,
    ) -> None:
        """Add character consistency to the pipeline.

        Args:
            provider: CharacterImageProvider for generating reference images.
            output_dir: Directory to save reference sheets and renders.
            generate_renders: Whether to generate scene renders.
        """
        if not isinstance(provider, CharacterImageProvider):
            raise TypeError(
                f"provider must be a CharacterImageProvider, got {type(provider).__name__}"
            )

        # Store in pipeline state (not instance var) per spec
        self.pipeline.state["character_image_provider"] = provider
        self.pipeline.state["character_output_dir"] = output_dir
        self.pipeline.state["generate_scene_renders"] = generate_renders

        # Register the stage
        self.pipeline.state["character_consistency_stage"] = SceneCharacterRendererStage(
            provider=provider,
            output_dir=output_dir,
        )

    def run_character_consistency(
        self,
        script: Script,
        registry: CharacterRegistry,
    ) -> Optional[SceneCharacterRenderCollection]:
        """Run character consistency after script generation.

        Args:
            script: The generated screenplay.
            registry: Character registry with reference image paths.

        Returns:
            SceneCharacterRenderCollection if renders were generated, else None.
        """
        if not self.pipeline.state.get("generate_scene_renders"):
            return None

        stage = self.pipeline.state.get("character_consistency_stage")
        if not stage:
            return None

        # Generate reference sheets for all characters
        output_dir = self.pipeline.state.get("character_output_dir", Path("output"))
        provider = self.pipeline.state.get("character_image_provider")
        if provider and output_dir:
            ref_generator = ReferenceSheetGenerator(
                provider=provider,
                output_dir=output_dir,
            )
            ref_generator.generate_for_registry(registry)

        collection = stage.execute(script, registry, pipeline_state=self.pipeline.state)

        # Store on pipeline state
        self.pipeline.state["character_renders"] = collection

        return collection
