"""Stage 2: Character Registry Generator.

Takes a beat sheet and generates a character registry with detailed profiles.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.models import CharacterProfile, CharacterRegistry, Project

from .base import BaseStageGenerator

logger = logging.getLogger(__name__)

CHARACTER_PROMPT = """\
You are an expert character designer for screenplays. Your task is to create a \
comprehensive character registry based on the beat sheet.

Project Title: {title}
Genre: {genre}
Tone: {tone}

Beat Sheet Summary:
{beat_sheet_summary}

Create a character registry with all major characters in the story. For each character, \
provide:
- name: Character name
- role: Their role (protagonist, antagonist, supporting, mentor, etc.)
- age: Character age (optional, use null if unknown)
- gender: Character gender (optional, use null if unknown)
- description: Physical and personality description (2-4 sentences)
- motivation: What drives this character
- arc: Character arc / transformation throughout the story
- relationships: Dict of relationships to other characters (e.g., {"Alice": "best friend"})

Respond with a JSON object matching this schema:
{{
  "characters": [
    {{
      "name": "string",
      "role": "string",
      "age": number or null,
      "gender": "string" or null,
      "description": "string",
      "motivation": "string",
      "arc": "string",
      "relationships": {{}}
    }}
  ]
}}

Ensure characters are diverse, well-motivated, and serve the story. Include at least \
the protagonist, antagonist, and key supporting characters.
"""


class Stage2CharacterGenerator(BaseStageGenerator):
    """Stage 2: Generate character registry from beat sheet.

    This stage takes a beat sheet and produces detailed character profiles.
    """

    def execute(self, project: Project) -> Project:
        """Execute Stage 2: Generate the character registry.

        Args:
            project: Project with beat_sheet populated.

        Returns:
            Updated project with characters populated.

        Raises:
            ValueError: If beat_sheet is missing.
        """
        self._validate_project_data(project, ["beat_sheet"])

        beat_sheet = project.beat_sheet
        beats_summary = "\n".join(
            f"Beat {b['number']}: {b['name']} - {b['description']}"
            for b in beat_sheet.get("beats", [])
        )

        prompt = CHARACTER_PROMPT.format(
            title=beat_sheet.get("title", project.title),
            genre=beat_sheet.get("genre", project.genre),
            tone=beat_sheet.get("tone", project.tone),
            beat_sheet_summary=beats_summary,
        )

        messages = self._get_messages(prompt)
        response = self.client.chat(messages)
        data = self._parse_json_response(response.content)

        # Validate and store character registry
        registry = CharacterRegistry(**data)
        project.characters = registry.to_dict()
        project.status = "stage2_characters_complete"
        logger.info(f"Stage 2 complete: {len(registry.characters)} characters created")
        return project
