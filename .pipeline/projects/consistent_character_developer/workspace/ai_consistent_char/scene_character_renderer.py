"""Scene character renderer — generates per-scene character renders.

Injects character reference images as control inputs into the image-generation
provider so that the same character looks identical across different scenes.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_movie_gen_suite.models import CharacterRegistry, Scene, Script

from ai_consistent_char.image_provider import CharacterImageProvider
from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection

logger = logging.getLogger(__name__)


class SceneCharacterRenderer:
    """Generates per-scene character renders using reference images.

    For each scene, the renderer determines which characters are present,
    looks up their reference images, and calls the image provider to produce
    a consistent render for each character in the context of that scene.

    Args:
        provider: CharacterImageProvider that produces reference images.
        reference_images: Mapping of character_id → path to reference image.
        output_dir: Directory where rendered images are saved.
    """

    def __init__(
        self,
        provider: CharacterImageProvider,
        reference_images: Dict[str, str],
        output_dir: Path,
    ):
        self.provider = provider
        self.reference_images = dict(reference_images)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_script(
        self,
        script: Script,
        registry: CharacterRegistry,
    ) -> SceneCharacterRenderCollection:
        """Render every character in every scene.

        Args:
            script: The screenplay to render.
            registry: Character registry with reference image paths.

        Returns:
            SceneCharacterRenderCollection with all renders.
        """
        collection = SceneCharacterRenderCollection()

        for scene in script.scenes:
            present = self._detect_present_characters(scene, registry)
            renders = self.render_scene(scene, present)
            for render in renders:
                collection.add_render(render)

        return collection

    def render_all_scenes(
        self,
        script: Script,
        registry: CharacterRegistry,
    ) -> SceneCharacterRenderCollection:
        """Alias for render_script for compatibility."""
        return self.render_script(script, registry)

    def render_scene(
        self,
        scene: Scene,
        character_ids: List[str],
    ) -> List[SceneCharacterRender]:
        """Render a list of characters for a single scene.

        Args:
            scene: The scene to render.
            character_ids: List of character IDs to render.

        Returns:
            List of SceneCharacterRender objects.
        """
        renders: List[SceneCharacterRender] = []

        for char_id in character_ids:
            ref_path = self.reference_images.get(char_id)
            if not ref_path:
                logger.warning("No reference image for character '%s' — skipping.", char_id)
                continue

            render_path = self.output_dir / f"{scene.scene_id}_{char_id}.png"
            rendered_path = self.provider.render_character(
                character_id=char_id,
                reference_image_path=ref_path,
                scene_context=scene.action,
                output_path=render_path,
            )

            render = SceneCharacterRender(
                scene_id=scene.scene_id,
                character_id=char_id,
                render_path=str(rendered_path),
                scene_context=scene.action,
            )
            renders.append(render)

        return renders

    def _detect_present_characters(
        self,
        scene: Scene,
        registry: CharacterRegistry,
    ) -> List[str]:
        """Detect which characters appear in a scene.

        Uses a simple keyword matching approach: if a character's name appears
        in the scene action, that character is considered present.

        Args:
            scene: The scene to analyze.
            registry: Character registry.

        Returns:
            List of character IDs present in the scene.
        """
        present: List[str] = []
        scene_text = scene.action.lower()

        for char_id, character in registry.characters.items():
            name = character.name.lower()
            if name in scene_text:
                present.append(char_id)

        return present
