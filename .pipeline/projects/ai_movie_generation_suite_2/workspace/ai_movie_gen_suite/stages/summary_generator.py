"""Stage 6: Summary generator.

Generates a concise summary of the movie project.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class SummaryGenerator(BaseStageGenerator):
    """Generate a movie summary from the project data.

    Uses the SUMMARY prompt template to create a concise summary
    of the movie including title, logline, genre, and key plot points.
    """

    def execute(self, project: Project) -> Project:
        """Execute summary generation on the project.

        Args:
            project: Project with all stage data.

        Returns:
            Updated project with summary populated.
        """
        concept = project.beat_sheet or {}
        title = concept.get("title", project.title)
        logline = concept.get("logline", project.logline)
        genre = concept.get("genre", project.genre)
        synopsis = concept.get("synopsis", "")

        from ai_movie_gen_suite.prompts import prompt_library

        prompt = prompt_library.render_template(
            "summary",
            title=title,
            logline=logline,
            genre=genre,
            synopsis=synopsis,
        )
        messages = self._get_messages(prompt)

        response = self.client.generate(messages)
        data = self._parse_json_response(response.content)

        project.summary = data
        project.status = "summary_created"
        logger.info(f"Summary created for: {title}")
        return project
