"""Stage 5: Music Composition Generator.

Takes the script and generates music composition data for each scene,
including mood, instrumentation, tempo, and musical themes.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.models import Project

from .base import BaseStageGenerator

logger = logging.getLogger(__name__)

MUSIC_PROMPT = """\
You are an expert film composer. Your task is to create music composition plans \
for each scene of a screenplay.

Project Title: {title}
Genre: {genre}
Tone: {tone}

Script Summary:
{script_summary}

For each scene, provide music composition details:
- scene_number: Corresponding scene number
- mood: Emotional mood the music should convey (e.g., "tense", "joyful", "melancholic")
- instrumentation: Instruments to use (e.g., "strings", "piano", "synthesizer")
- tempo: Tempo description (e.g., "slow and deliberate", "fast and energetic")
- musical_theme: Description of the main musical theme or motif
- dynamics: Dynamic range (e.g., "soft to loud", "consistent volume")
- transitions: How the music transitions between scenes

Respond with a JSON object matching this schema:
{{
  "music_compositions": [
    {{
      "scene_number": 1,
      "mood": "string",
      "instrumentation": "string",
      "tempo": "string",
      "musical_theme": "string",
      "dynamics": "string",
      "transitions": "string"
    }}
  ]
}}

Make the music complement the visual style and emotional arc of the story. \
Consider how the score evolves throughout the film.
"""


class Stage5MusicComposer(BaseStageGenerator):
    """Stage 5: Generate music composition data for the script.

    This stage takes a script and produces music composition plans for each scene.
    """

    stage_name = "Stage5MusicComposer"

    def get_stage_name(self) -> str:
        """Return the name of this stage."""
        return "Stage 5: Music Composer"

    def execute(self, project: Project) -> Project:
        """Execute Stage 5: Generate music compositions.

        Args:
            project: Project with script populated.

        Returns:
            Updated project with music populated.

        Raises:
            ValueError: If script is missing.
        """
        self._validate_project_data(project, ["script"])

        script = project.script
        scenes = script.get("scenes", [])

        script_summary = "\n".join(
            f"Scene {s['number']}: {s['location']} - {s['description'][:200]}"
            for s in scenes
        )

        prompt = MUSIC_PROMPT.format(
            title=script.get("title", project.title),
            genre=script.get("genre", project.genre),
            tone=script.get("tone", project.tone),
            script_summary=script_summary,
        )

        messages = self._get_messages(prompt)
        response = self.client.chat(messages)
        data = self._parse_json_response(response.content)

        project.music = {
            "compositions": data["music_compositions"],
            "overall_theme": "Epic orchestral score with leitmotifs for main characters",
        }
        project.status = "stage5_music_complete"

        logger.info(
            f"Stage 5 complete: Music compositions generated for '{project.title}' "
            f"with {len(data['music_compositions'])} scenes."
        )
        return project
