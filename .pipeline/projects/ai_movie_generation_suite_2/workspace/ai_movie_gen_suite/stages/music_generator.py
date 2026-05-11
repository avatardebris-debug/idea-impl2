"""Stage 7: Music generator.

Generates music and sound design descriptions for the movie.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class MusicGenerator(BaseStageGenerator):
    """Generate music and sound design for the movie.

    Uses the MUSIC prompt template to create music cues, sound effects,
    and audio direction for each scene.
    """

    def execute(self, project: Project) -> Project:
        """Execute music generation on the project.

        Args:
            project: Project with scene descriptions.

        Returns:
            Updated project with music data populated.
        """
        scene_descriptions = project.scene_descriptions
        if not scene_descriptions:
            raise ValueError("Project must have scene descriptions for music generation")

        from ai_movie_gen_suite.prompts import prompt_library

        music_cues: List[Dict[str, Any]] = []
        for scene_desc in scene_descriptions:
            scene_num = scene_desc.get("scene_number", 0)
            mood = scene_desc.get("mood", "")
            location = scene_desc.get("location", "")

            prompt = prompt_library.render_template(
                "music",
                scene_number=scene_num,
                mood=mood,
                location=location,
                genre=project.genre,
            )
            messages = self._get_messages(prompt)

            response = self.client.generate(messages)
            data = self._parse_json_response(response.content)
            data["scene_number"] = scene_num
            music_cues.append(data)

        project.music = {
            "music_cues": music_cues,
            "sound_effects": self._generate_sound_effects(project),
            "audio_direction": self._generate_audio_direction(project),
        }
        project.status = "music_created"
        logger.info(f"Music generated: {len(music_cues)} music cues")
        return project

    def _generate_sound_effects(self, project: Project) -> List[Dict[str, Any]]:
        """Generate sound effects for the project."""
        return [{"scene": i + 1, "effects": []} for i in range(len(project.scene_descriptions or []))]

    def _generate_audio_direction(self, project: Project) -> Dict[str, Any]:
        """Generate overall audio direction."""
        return {
            "overall_mood": project.tone,
            "genre": project.genre,
            "audio_style": "cinematic",
        }
