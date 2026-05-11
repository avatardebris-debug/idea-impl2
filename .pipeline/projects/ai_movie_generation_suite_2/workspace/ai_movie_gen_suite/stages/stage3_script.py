"""Stage 3: Script Writer.

Takes a beat sheet and character registry and generates a full screenplay script
with scenes and dialogue.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.models import Project, Scene, Script

from .base import BaseStageGenerator

logger = logging.getLogger(__name__)

SCRIPT_PROMPT = """\
You are an expert screenwriter. Your task is to write a complete screenplay based on \
the beat sheet and character registry.

Project Title: {title}
Genre: {genre}
Tone: {tone}

Characters:
{characters}

Beat Sheet:
{beat_sheet}

Write a full screenplay with scenes and dialogue. For each scene, provide:
- number: Scene number (sequential)
- location: Scene location in standard format (e.g., "INT. COFFEE SHOP - DAY")
- description: Action/description text for the scene
- dialogue: List of dialogue lines, each with:
    - character: Character name
    - dialogue: The spoken line
    - action: Optional parenthetical or action description
- characters_present: List of character names present in the scene

Respond with a JSON object matching this schema:
{{
  "title": "string",
  "genre": "string",
  "tone": "string",
  "scenes": [
    {{
      "number": 1,
      "location": "string",
      "description": "string",
      "dialogue": [
        {{
          "character": "string",
          "dialogue": "string",
          "action": "string" or null
        }}
      ],
      "characters_present": ["string"]
    }}
  ]
}}

Write a complete screenplay with at least 10 scenes. Each scene should have vivid \
descriptions and natural dialogue. Characters should speak in distinct voices.
"""


class Stage3ScriptWriter(BaseStageGenerator):
    """Stage 3: Generate screenplay script from beat sheet and characters.

    This stage takes a beat sheet and character registry and produces a full screenplay.
    """

    def execute(self, project: Project) -> Project:
        """Execute Stage 3: Generate the screenplay script.

        Args:
            project: Project with beat_sheet and characters populated.

        Returns:
            Updated project with script populated.

        Raises:
            ValueError: If beat_sheet or characters is missing.
        """
        self._validate_project_data(project, ["beat_sheet", "characters"])

        beat_sheet = project.beat_sheet
        characters = project.characters

        characters_text = "\n".join(
            f"- {c['name']} ({c['role']}): {c['description']}"
            for c in characters.get("characters", [])
        )

        beats_text = "\n".join(
            f"Beat {b['number']}: {b['name']} - {b['description']}"
            for b in beat_sheet.get("beats", [])
        )

        prompt = SCRIPT_PROMPT.format(
            title=beat_sheet.get("title", project.title),
            genre=beat_sheet.get("genre", project.genre),
            tone=beat_sheet.get("tone", project.tone),
            characters=characters_text,
            beat_sheet=beats_text,
        )

        messages = self._get_messages(prompt)
        response = self.client.chat(messages)
        data = self._parse_json_response(response.content)

        scenes = [Scene(**s) for s in data.get("scenes", [])]
        script = Script(
            title=data.get("title", project.title),
            genre=data.get("genre", project.genre),
            tone=data.get("tone", project.tone),
            scenes=scenes,
        )

        project.script = script.to_dict()
        project.status = "stage3_script_complete"
        logger.info(f"Stage 3 complete: {len(scenes)} scenes written")
        return project
