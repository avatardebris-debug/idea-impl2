"""Stage 10: Distribution generator.

Generates distribution strategy and platform recommendations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class DistributionGenerator(BaseStageGenerator):
    """Generate distribution strategy for the movie.

    Uses the DISTRIBUTION prompt template to create platform recommendations,
    release strategy, and audience targeting.
    """

    def execute(self, project: Project) -> Project:
        """Execute distribution generation on the project.

        Args:
            project: Project with all stage data.

        Returns:
            Updated project with distribution data populated.
        """
        concept = project.beat_sheet or {}
        title = concept.get("title", project.title)
        genre = concept.get("genre", project.genre)

        from ai_movie_gen_suite.prompts import prompt_library

        prompt = prompt_library.render_template(
            "distribution",
            title=title,
            genre=genre,
            tone=project.tone,
            budget=concept.get("budget", "unknown"),
        )
        messages = self._get_messages(prompt)

        response = self.client.generate(messages)
        data = self._parse_json_response(response.content)

        project.distribution = {
            "platforms": data.get("platforms", []),
            "release_strategy": data.get("release_strategy", ""),
            "target_audience": data.get("target_audience", ""),
            "estimated_budget": data.get("estimated_budget", "unknown"),
        }
        project.status = "distribution_done"
        logger.info(f"Distribution strategy created for: {title}")
        return project
