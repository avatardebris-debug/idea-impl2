"""Stage 5: Scene Description generator.

Takes a script and generates detailed visual descriptions for each scene.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project, SceneDescription
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class SceneDescriptionGenerator(BaseStageGenerator):
    """Generate visual scene descriptions from a screenplay script.

    Uses the SCENE_DESCRIPTION prompt template to create detailed visual
    directions including camera movements, lighting, color palette, and mood.
    """

    def execute(self, project: Project) -> Project:
        """Execute scene description generation on the project.

        Args:
            project: Project with script data.

        Returns:
            Updated project with scene_descriptions populated.
        """
        script = project.script
        if not script:
            raise ValueError("Project must have script for scene description generation")

        from ai_movie_gen_suite.prompts import prompt_library

        scenes = script.get("scenes", [])
        if not scenes:
            raise ValueError("Script must have scenes for scene description generation")

        # Build scene descriptions
        scene_descriptions: List[Dict[str, Any]] = []
        for scene in scenes:
            scene_num = scene.get("number", 0)
            location = scene.get("location", "")
            description = scene.get("description", "")

            prompt = prompt_library.render_template(
                "scene_description",
                scene_number=scene_num,
                location=location,
                description=description,
                genre=script.get("genre", project.genre),
                tone=script.get("tone", project.tone),
            )
            messages = self._get_messages(prompt)

            response = self.client.generate(messages)
            data = self._parse_json_response(response.content)

            scene_desc = SceneDescription(
                scene_number=data.get("scene_number", scene_num),
                location=data.get("location", location),
                visual_description=data.get("visual_description", ""),
                camera_directions=data.get("camera_directions", ""),
                lighting=data.get("lighting", ""),
                color_palette=data.get("color_palette", ""),
                mood=data.get("mood", ""),
                props_and_set_design=data.get("props_and_set_design", ""),
            )
            scene_descriptions.append(scene_desc.to_dict())

        project.scene_descriptions = scene_descriptions
        project.status = "scene_descriptions_created"
        logger.info(f"Scene descriptions created: {len(scene_descriptions)} scenes")
        return project
