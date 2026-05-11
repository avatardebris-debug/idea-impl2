"""Stage 2: Beat Sheet generator.

Takes a movie concept and generates a Save-the-Cat beat sheet with 15 beats.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import BeatSheet, Project
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
        concept = project.beat_sheet
        if not concept:
            raise ValueError("Project must have concept data (beat_sheet) for beat sheet generation")

        from ai_movie_gen_suite.prompts import prompt_library

        prompt = prompt_library.render_template(
            "beat_sheet",
            title=concept.get("title", ""),
            genre=concept.get("genre", ""),
            logline=concept.get("logline", ""),
            synopsis=concept.get("synopsis", ""),
        )
        messages = self._get_messages(prompt)

        response = self.client.generate(messages)
        data = self._parse_json_response(response.content)

        # Convert to BeatSheet model
        beats_data = data.get("beats", [])
        beat_sheet = BeatSheet(
            title=concept.get("title", project.title),
            logline=concept.get("logline", project.logline),
            beats=[
                {
                    "number": b.get("number", i + 1),
                    "name": b.get("name", f"Beat {i + 1}"),
                    "description": b.get("description", ""),
                    "scene_numbers": b.get("scene_numbers", []),
                }
                for i, b in enumerate(beats_data)
            ],
            genre=concept.get("genre", project.genre),
            tone=concept.get("mood", project.tone),
        )

        project.beat_sheet = beat_sheet.to_dict()
        project.status = "beat_sheet_created"
        logger.info(f"Beat sheet created: {beat_sheet.title} with {len(beat_sheet.beats)} beats")
        return project
