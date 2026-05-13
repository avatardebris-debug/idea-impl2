"""SceneCharacterRendererStage — pipeline stage for per-scene character rendering.

Integrates with MovieGenerationPipeline by rendering every character in every
scene using reference images, and storing results on the pipeline state.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_movie_gen_suite.models import CharacterRegistry, Script

from ai_consistent_char.image_provider import CharacterImageProvider
from ai_consistent_char.models import SceneCharacterRenderCollection
from ai_consistent_char.scene_character_renderer import SceneCharacterRenderer

logger = logging.getLogger(__name__)


class SceneCharacterRendererStage:
    """Pipeline stage that renders characters per scene.

    Args:
        provider: CharacterImageProvider for generating reference images.
        output_dir: Directory to save renders.
    """

    def __init__(
        self,
        provider: CharacterImageProvider,
        output_dir: Path,
    ):
        self.provider = provider
        self.output_dir = Path(output_dir)

    def execute(
        self,
        script: Script,
        registry: CharacterRegistry,
        pipeline_state: Optional[Dict[str, Any]] = None,
    ) -> SceneCharacterRenderCollection:
        """Execute the stage: render all characters in all scenes.

        Args:
            script: The screenplay to render.
            registry: Character registry with reference image paths.
            pipeline_state: Optional pipeline state dict to store results on.

        Returns:
            SceneCharacterRenderCollection with all renders.
        """
        # Build reference image lookup from registry
        reference_images: Dict[str, str] = {
            char_id: char.reference_image_path
            for char_id, char in registry.characters.items()
            if char.reference_image_path
        }

        renderer = SceneCharacterRenderer(
            provider=self.provider,
            reference_images=reference_images,
            output_dir=self.output_dir,
        )

        collection = renderer.render_script(script, registry)

        # Store results on pipeline state if provided
        if pipeline_state is not None:
            pipeline_state["character_renders"] = collection

        return collection
