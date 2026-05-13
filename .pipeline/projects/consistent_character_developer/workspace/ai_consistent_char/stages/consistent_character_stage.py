"""ConsistentCharacterStage — pipeline stage for reference image generation.

Integrates with MovieGenerationPipeline by generating reference images for
all characters and augmenting the registry with visual data.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ai_movie_gen_suite.models import CharacterRegistry

from ai_consistent_char.image_provider import CharacterImageProvider
from ai_consistent_char.reference_sheet_generator import ReferenceSheetGenerator

logger = logging.getLogger(__name__)


class ConsistentCharacterStage:
    """Pipeline stage that generates character reference images.

    Args:
        registry: The character registry to process.
        output_dir: Directory for generated images and profiles.
        provider: Image provider that produces reference images.
    """

    def __init__(
        self,
        registry: CharacterRegistry,
        output_dir: Path,
        provider: CharacterImageProvider,
    ):
        self.registry = registry
        self.output_dir = Path(output_dir)
        self.provider = provider
        self.generator = ReferenceSheetGenerator(provider, output_dir)

    def execute(self) -> CharacterRegistry:
        """Run the stage: generate reference images and update the registry.

        Returns:
            The same registry instance, now augmented with visual data.
        """
        logger.info(
            "ConsistentCharacterStage: generating reference images for %d characters.",
            len(self.registry.characters),
        )

        image_paths = self.generator.generate_for_registry(self.registry)

        # Store visual data on the registry for downstream stages
        self.registry._visual_data = image_paths  # type: ignore[attr-defined]

        for character in self.registry.characters:
            if character.id in image_paths:
                logger.info(
                    "Attached reference image to %s: %s",
                    character.id,
                    image_paths[character.id],
                )

        logger.info("ConsistentCharacterStage complete.")
        return self.registry
