"""Stage 4: Scene Description Generator.

Takes a script and generates detailed visual descriptions for each scene,
including camera directions, lighting, color palette, mood, and set design.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.models import Project, SceneDescription

from .base import BaseStageGenerator

logger = logging.getLogger(__name__)

SCENE_DESC_PROMPT = """\
You are an expert cinematographer and visual director. Your task is to create \
detailed visual descriptions for each scene of a screenplay.

Project Title: {title}
Genre: {genre}
Tone: {tone}

Script Summary:
{script_summary}

For each scene, provide detailed visual direction:
- scene_number: Corresponding scene number
- location: Scene location
- visual_description: Detailed visual description of what the audience sees (3-5 sentences)
- camera_directions: Camera movement and framing directions (e.g., "Close-up on face", "Tracking shot")
- lighting: Lighting description (e.g., "Warm golden hour light", "Harsh fluorescent")
- color_palette: Color palette for the scene (e.g., "Warm oranges and deep blues")
- mood: Mood/atmosphere description (e.g., "Tense and claustrophobic")
- props_and_set_design: Key props and set design elements

Respond with a JSON object matching this schema:
{{
  "scene_descriptions": [
    {{
      "scene_number": 1,
      "location": "string",
      "visual_description": "string",
      "camera_directions": "string",
      "lighting": "string",
      "color_palette": "string",
      "mood": "string",
      "props_and_set_design": "string"
    }}
  ]
}}

Make each scene visually distinct and cinematically compelling. Consider how the \
visual style supports the story and mood.
"""


class Stage4SceneDescriptionGenerator(BaseStageGenerator):
    """Stage 4: Generate visual scene descriptions from the script.

    This stage takes a script and produces detailed visual direction for each scene.
    """

    stage_name = "Stage4SceneDescriptionGenerator"

    def get_stage_name(self) -> str:
        """Return the name of this stage."""
        return "Stage 4: Scene Description Generator"

    def execute(self, project: Project) -> Project:
        """Execute Stage 4: Generate scene descriptions.

        Args:
            project: Project with script populated.

        Returns:
            Updated project with scene_descriptions populated.

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

        prompt = SCENE_DESC_PROMPT.format(
            title=script.get("title", project.title),
            genre=script.get("genre", project.genre),
            tone=script.get("tone", project.tone),
            script_summary=script_summary,
        )

        messages = self._get_messages(prompt)
        response = self.client.chat(messages)
        data = self._parse_json_response(response.content)

        scene_descriptions = [SceneDescription(**sd) for sd in data["scene_descriptions"]]
        project.scene_descriptions = [sd.to_dict() for sd in scene_descriptions]
        project.status = "stage4_scene_descriptions_complete"

        logger.info(
            f"Stage 4 complete: Scene descriptions generated for '{project.title}' "
            f"with {len(scene_descriptions)} scenes."
        )
        return project
