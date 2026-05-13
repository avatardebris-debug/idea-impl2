"""Reference sheet generator — creates character reference sheets.

Generates reference images and JSON profiles for all characters in a registry,
saving them to a specified output directory.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from ai_movie_gen_suite.models import CharacterRegistry

from ai_consistent_char.image_provider import CharacterImageProvider

logger = logging.getLogger(__name__)


class ReferenceSheetGenerator:
    """Generates reference sheets for all characters in a registry.

    For each character, the generator:
    1. Calls the image provider to create a reference image.
    2. Saves a JSON profile with character metadata.

    Args:
        provider: CharacterImageProvider to generate reference images.
        output_dir: Directory to save reference sheets and profiles.
    """

    def __init__(
        self,
        provider: CharacterImageProvider,
        output_dir: Path,
    ):
        self.provider = provider
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_for_registry(
        self,
        registry: CharacterRegistry,
    ) -> List[str]:
        """Generate reference sheets for all characters in the registry.

        Args:
            registry: CharacterRegistry with characters to generate sheets for.

        Returns:
            List of paths to generated reference images.
        """
        image_paths: List[str] = []

        for char_id, character in registry.characters.items():
            ref_path = self.output_dir / f"{char_id}_reference.png"
            visual_anchor = character.visual_anchor or character.physical_description
            generated_path = self.provider.generate_reference_image(
                character_id=char_id,
                visual_anchor_text=visual_anchor,
                output_path=ref_path,
            )
            image_paths.append(generated_path)

            # Save JSON profile
            self._save_profile(char_id, character)

            logger.info("Generated reference sheet for '%s' at %s", char_id, generated_path)

        return image_paths

    def _save_profile(
        self,
        char_id: str,
        character: Any,
    ) -> None:
        """Save a JSON profile for a character."""
        profile = {
            "id": character.id,
            "name": character.name,
            "role": character.role,
            "motivation": character.motivation,
            "physical_description": character.physical_description,
            "personality_traits": character.personality_traits,
            "voice_notes": character.voice_notes,
            "costume_notes": character.costume_notes,
            "visual_anchor": character.visual_anchor,
            "backstory": character.backstory,
            "arc_summary": character.arc_summary,
            "reference_image": f"{char_id}_reference.png",
        }

        profile_path = self.output_dir / f"{char_id}_profile.json"
        profile_path.write_text(json.dumps(profile, indent=2))
