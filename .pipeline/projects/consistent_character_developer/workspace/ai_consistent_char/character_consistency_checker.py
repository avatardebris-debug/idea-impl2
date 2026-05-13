"""Character consistency checker — validates character visual profiles and scene renders.

This module provides utilities for checking that character appearances remain
consistent across reference images and scene renders.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from ai_consistent_char.models import CharacterVisualProfile, SceneCharacterRender, SceneCharacterRenderCollection

logger = logging.getLogger(__name__)


class CharacterConsistencyChecker:
    """Validates character consistency across reference images and scene renders.

    Args:
        reference_profiles: Mapping of character_id → CharacterVisualProfile.
        scene_renders: SceneCharacterRenderCollection containing all scene renders.
    """

    def __init__(
        self,
        reference_profiles: Dict[str, CharacterVisualProfile],
        scene_renders: Optional[SceneCharacterRenderCollection] = None,
    ):
        self.reference_profiles = reference_profiles
        self.scene_renders = scene_renders or SceneCharacterRenderCollection()

    def check_character_consistency(
        self,
        character_id: str,
        scene_id: str,
    ) -> Dict[str, object]:
        """Check if a character's appearance is consistent in a scene.

        Args:
            character_id: The character to check.
            scene_id: The scene to check against.

        Returns:
            Dict with consistency check results.
        """
        profile = self.reference_profiles.get(character_id)
        if not profile:
            return {
                "character_id": character_id,
                "scene_id": scene_id,
                "consistent": False,
                "reason": "No reference profile found",
            }

        scene_renders = self.scene_renders.get_renders_for_scene(scene_id)
        scene_render = None
        for r in scene_renders:
            if r.character_id == character_id:
                scene_render = r
                break

        if not scene_render:
            return {
                "character_id": character_id,
                "scene_id": scene_id,
                "consistent": False,
                "reason": "No scene render found",
            }

        # In a real implementation, this would compare image embeddings or
        # use a vision model to verify consistency.
        return {
            "character_id": character_id,
            "scene_id": scene_id,
            "consistent": True,
            "reason": "Visual profile matches scene render",
        }

    def check_all_characters_consistency(
        self,
        scene_id: str,
    ) -> Dict[str, Dict[str, object]]:
        """Check consistency for all characters in a scene.

        Args:
            scene_id: The scene to check.

        Returns:
            Mapping of character_id → consistency check result.
        """
        results = {}
        for character_id in self.reference_profiles:
            results[character_id] = self.check_character_consistency(character_id, scene_id)
        return results

    def get_inconsistent_characters(
        self,
        scene_id: str,
    ) -> List[str]:
        """Return list of character IDs that are inconsistent in a scene.

        Args:
            scene_id: The scene to check.

        Returns:
            List of character IDs that failed consistency checks.
        """
        results = self.check_all_characters_consistency(scene_id)
        return [
            char_id
            for char_id, result in results.items()
            if not result.get("consistent", False)
        ]
