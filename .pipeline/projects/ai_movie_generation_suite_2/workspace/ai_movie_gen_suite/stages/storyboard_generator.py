"""Stage 4: Storyboard Generator.

Takes scene descriptions and generates detailed storyboard frames with shot design.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class StoryboardGenerator(BaseStageGenerator):
    """Generate storyboard frames from scene descriptions.

    Uses the STORYBOARD prompt template to create detailed storyboard
    descriptions including shot types, camera angles, composition,
    and visual effects for each frame.
    """

    def execute(self, project: Project) -> Project:
        """Execute storyboard generation on the project.

        Args:
            project: Project with scene_descriptions data.

        Returns:
            Updated project with storyboards populated.
        """
        scene_descriptions = project.scene_descriptions
        if not scene_descriptions:
            raise ValueError("Project must have scene_descriptions for storyboard generation")

        # Build storyboards
        storyboards: List[Dict[str, Any]] = []
        for scene_desc in scene_descriptions:
            scene_num = scene_desc.get("scene_number", 0)
            location = scene_desc.get("location", "")
            visual_desc = scene_desc.get("visual_description", "")

            prompt = self.prompt_library.render_template(
                "storyboard",
                scene_number=scene_num,
                location=location,
                visual_description=visual_desc,
                genre=project.genre,
                tone=project.tone,
            )
            messages = self._get_messages(prompt)

            response = self.client.chat(messages)
            data = self._parse_json_response(response.content)

            storyboard = {
                "scene_number": data.get("scene_number", scene_num),
                "shot_number": data.get("shot_number", 0),
                "shot_type": data.get("shot_type", ""),
                "camera_angle": data.get("camera_angle", ""),
                "camera_movement": data.get("camera_movement", ""),
                "composition": data.get("composition", ""),
                "visual_effects": data.get("visual_effects", ""),
                "audio_cues": data.get("audio_cues", ""),
                "duration": data.get("duration", 0),
                "transitions": data.get("transitions", ""),
                "description": data.get("description", ""),
            }
            storyboards.append(storyboard)

        project.storyboards = storyboards
        project.status = "storyboards_created"
        logger.info(f"Storyboards created: {len(storyboards)} frames")
        return project
