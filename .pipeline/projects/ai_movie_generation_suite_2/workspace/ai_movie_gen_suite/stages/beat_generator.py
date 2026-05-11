"""Stage 2: Beat Sheet generator.

Takes a movie concept and generates a Save-the-Cat beat sheet with 15 beats.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Beat, Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class BeatSheetGenerator(BaseStageGenerator):
    """Generate a Save-the-Cat beat sheet from a movie concept.

    Uses the BEAT_SHEET prompt template to create a structured beat sheet
    with 15 beats following the Save-the-Cat screenplay structure.
    """

    def execute(self, project: Project) -> Project:
        """Execute beat sheet generation on the project.

        Args:
            project: Project with concept data.

        Returns:
            Updated project with beat_sheet populated.
        """
        concept = project.concept
        if not concept:
            raise ValueError("Project must have concept data for beat sheet generation")

        from ai_movie_gen_suite.prompts import prompt_library

        prompt = prompt_library.render_template(
            "beat_sheet",
            title=concept.title,
            genre=concept.genre,
            logline=concept.logline,
            synopsis=concept.synopsis,
        )
        messages = self._get_messages(prompt)

        response = self.client.generate(messages)
        data = self._parse_json_response(response.content)

        # Convert to Beat model
        beats_data = data.get("beats", [])
        beats: List[Beat] = [
            Beat(
                number=b.get("number", i + 1),
                name=b.get("name", f"Beat {i + 1}"),
                description=b.get("description", ""),
                scene_numbers=b.get("scene_numbers", []),
            )
            for i, b in enumerate(beats_data)
        ]

        project.beat_sheet = beats
        project.status = "beat_sheet_created"
        logger.info(f"Beat sheet created: {concept.title} with {len(beats)} beats")
        return project
