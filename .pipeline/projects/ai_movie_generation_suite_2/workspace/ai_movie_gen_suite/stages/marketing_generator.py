"""Stage 9: Marketing generator.

Generates marketing materials for the movie.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class MarketingGenerator(BaseStageGenerator):
    """Generate marketing materials for the movie.

    Uses the MARKETING prompt template to create taglines, poster descriptions,
    and social media content.
    """

    def execute(self, project: Project) -> Project:
        """Execute marketing generation on the project.

        Args:
            project: Project with all stage data.

        Returns:
            Updated project with marketing data populated.
        """
        concept = project.beat_sheet or {}
        title = concept.get("title", project.title)
        logline = concept.get("logline", project.logline)
        genre = concept.get("genre", project.genre)

        from ai_movie_gen_suite.prompts import prompt_library

        prompt = prompt_library.render_template(
            "marketing",
            title=title,
            logline=logline,
            genre=genre,
            tone=project.tone,
        )
        messages = self._get_messages(prompt)

        response = self.client.generate(messages)
        data = self._parse_json_response(response.content)

        project.marketing = {
            "tagline": data.get("tagline", ""),
            "poster_description": data.get("poster_description", ""),
            "social_media": data.get("social_media", []),
            "press_release": data.get("press_release", ""),
        }
        project.status = "marketing_done"
        logger.info(f"Marketing materials created for: {title}")
        return project
