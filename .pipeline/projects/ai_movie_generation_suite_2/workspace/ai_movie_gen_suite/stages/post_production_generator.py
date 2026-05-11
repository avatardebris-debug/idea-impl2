"""Stage 8: Post-production generator.

Generates post-production notes including editing, VFX, and color grading.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class PostProductionGenerator(BaseStageGenerator):
    """Generate post-production data for the movie.

    Uses the POST_PRODUCTION prompt template to create editing notes,
    VFX requirements, and color grading direction.
    """

    def execute(self, project: Project) -> Project:
        """Execute post-production generation on the project.

        Args:
            project: Project with scene descriptions and music data.

        Returns:
            Updated project with post_production data populated.
        """
        scene_descriptions = project.scene_descriptions
        if not scene_descriptions:
            raise ValueError("Project must have scene descriptions for post-production")

        from ai_movie_gen_suite.prompts import prompt_library

        editing_notes: List[Dict[str, Any]] = []
        vfx_requirements: List[Dict[str, Any]] = []

        for scene_desc in scene_descriptions:
            scene_num = scene_desc.get("scene_number", 0)

            # Editing notes
            edit_prompt = prompt_library.render_template(
                "post_production",
                scene_number=scene_num,
                location=scene_desc.get("location", ""),
                mood=scene_desc.get("mood", ""),
                genre=project.genre,
                action="editing",
            )
            messages = self._get_messages(edit_prompt)
            response = self.client.generate(messages)
            data = self._parse_json_response(response.content)
            data["scene_number"] = scene_num
            editing_notes.append(data)

            # VFX requirements
            vfx_prompt = prompt_library.render_template(
                "post_production",
                scene_number=scene_num,
                location=scene_desc.get("location", ""),
                mood=scene_desc.get("mood", ""),
                genre=project.genre,
                action="vfx",
            )
            messages = self._get_messages(vfx_prompt)
            response = self.client.generate(messages)
            data = self._parse_json_response(response.content)
            data["scene_number"] = scene_num
            vfx_requirements.append(data)

        project.post_production = {
            "editing_notes": editing_notes,
            "vfx_requirements": vfx_requirements,
            "color_grading": {
                "overall_palette": self._determine_palette(project),
                "scene_grading": [
                    {"scene": i + 1, "grading": "standard"}
                    for i in range(len(scene_descriptions))
                ],
            },
        }
        project.status = "post_production_done"
        logger.info("Post-production data generated")
        return project

    def _determine_palette(self, project: Project) -> str:
        """Determine overall color palette based on genre and tone."""
        genre = project.genre.lower()
        tone = project.tone.lower()

        palettes = {
            "drama": "muted earth tones",
            "comedy": "bright and saturated",
            "horror": "dark and desaturated",
            "sci-fi": "cool blues and silvers",
            "romance": "warm pastels",
            "action": "high contrast",
            "thriller": "cool greens and grays",
        }
        return palettes.get(genre, "cinematic neutral")
