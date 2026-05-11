"""Stage 1: Concept Development generator.

Takes a user prompt and generates a movie concept including title, genre,
logline, synopsis, visual style, and other metadata.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class ConceptGenerator(BaseStageGenerator):
    """Generate a movie concept from a user prompt.

    Uses the CONCEPT_DEVELOPMENT prompt template to create a compelling
    movie concept with title, genre, logline, synopsis, and more.
    """

    def execute(self, project: Project) -> Project:
        """Execute concept development on the project.

        Args:
            project: Project with an 'input_prompt' field.

        Returns:
            Updated project with concept data populated.
        """
        input_prompt = getattr(project, "input_prompt", None)
        if not input_prompt:
            raise ValueError("Project must have 'input_prompt' for concept development")

        from ai_movie_gen_suite.prompts import prompt_library

        prompt = prompt_library.render_template(
            "concept_development", input_prompt=input_prompt
        )
        messages = self._get_messages(prompt)

        response = self.client.generate(messages)
        data = self._parse_json_response(response.content)

        project.beat_sheet = data
        project.genre = data.get("genre", project.genre)
        project.tone = data.get("mood", project.tone)
        project.status = "concept_developed"
        logger.info(f"Concept developed: {data.get('title', 'Unknown')}")
        return project
