"""Stage 1: Beat Sheet Generator.

Takes a project idea (title + logline) and generates a Save-the-Cat beat sheet
with 15 beats, plus genre and tone suggestions.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from ai_movie_gen_suite.models import Beat, BeatSheet, Project

from .base import BaseStageGenerator

logger = logging.getLogger(__name__)

BEAT_SHEET_PROMPT = """\
You are an expert screenwriter and story architect. Your task is to create a complete \
Save-the-Cat beat sheet for a screenplay.

Project Title: {title}
Logline: {logline}
Genre: {genre}
Tone: {tone}

The Save-the-Cat structure has 15 beats. For each beat, provide:
- number: The beat number (1-15)
- name: The standard beat name
- description: A detailed description of what happens in this beat (2-4 sentences)
- scene_numbers: A list of scene numbers that will correspond to this beat (leave empty for now)

The 15 beats are:
1. Opening Image
2. Theme Stated
3. Set-up
4. Catalyst
5. Debate
6. Break into Two
7. B Story
8. Fun and Games
9. Midpoint
10. Bad Guys Close In
11. All Is Lost
12. Dark Night of the Soul
13. Break into Three
14. Finale
15. Final Image

Respond with a JSON object matching this schema:
{{
  "title": "string",
  "logline": "string",
  "beats": [
    {{
      "number": 1,
      "name": "string",
      "description": "string",
      "scene_numbers": []
    }}
  ],
  "genre": "string",
  "tone": "string"
}}

Ensure the story is coherent, the beats follow proper narrative structure, and the \
genre/tone are appropriate for the logline.
"""


class Stage1BeatSheetGenerator(BaseStageGenerator):
    """Stage 1: Generate a beat sheet from a project idea.

    This stage takes a title and logline and produces a complete Save-the-Cat
    beat sheet with 15 beats.
    """

    stage_name = "Stage1BeatSheetGenerator"

    def get_stage_name(self) -> str:
        """Return the name of this stage."""
        return "Stage 1: Beat Sheet Generator"

    def execute(self, project: Project) -> Project:
        """Execute Stage 1: Generate the beat sheet.

        Args:
            project: Project with title and logline (and optionally genre/tone).

        Returns:
            Updated project with beat_sheet populated.

        Raises:
            ValueError: If title or logline is missing.
        """
        if not project.title:
            raise ValueError("Project must have a title for Stage 1")
        if not project.logline:
            raise ValueError("Project must have a logline for Stage 1")

        prompt = BEAT_SHEET_PROMPT.format(
            title=project.title,
            logline=project.logline,
            genre=project.genre or "Drama",
            tone=project.tone or "Serious",
        )

        messages = self._get_messages(prompt)
        response = self.client.chat(messages)
        data = self._parse_json_response(response.content)

        beat_sheet = BeatSheet(
            title=data["title"],
            logline=data["logline"],
            beats=[Beat(**b) for b in data["beats"]],
            genre=data.get("genre", project.genre or "Drama"),
            tone=data.get("tone", project.tone or "Serious"),
        )

        project.beat_sheet = beat_sheet.to_dict()
        project.genre = beat_sheet.genre
        project.tone = beat_sheet.tone
        project.update_status("beat_sheet_complete")

        logger.info(
            f"Stage 1 complete: Beat sheet generated for '{project.title}' "
            f"with {len(beat_sheet.beats)} beats."
        )
        return project
