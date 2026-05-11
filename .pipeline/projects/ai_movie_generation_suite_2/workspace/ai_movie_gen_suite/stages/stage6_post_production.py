"""Stage 6: Post-Production Planner.

Takes the complete project data and generates a post-production plan including
video editing, VFX, sound design, and distribution strategy.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.models import Project

from .base import BaseStageGenerator

logger = logging.getLogger(__name__)

POST_PROD_PROMPT = """\
You are an expert film producer and post-production supervisor. Your task is to \
create a comprehensive post-production plan for a screenplay.

Project Title: {title}
Genre: {genre}
Tone: {tone}

Beat Sheet Summary:
{beat_sheet_summary}

Script Summary:
{script_summary}

Scene Descriptions:
{scene_descriptions}

Music Plan:
{music_plan}

Create a post-production plan covering:

1. VIDEO EDITING:
   - Overall editing style and approach
   - Pacing strategy for each act
   - Key editing techniques to use

2. VISUAL EFFECTS (VFX):
   - VFX requirements per scene
   - Complexity level (practical, CGI, compositing)
   - Priority VFX shots

3. SOUND DESIGN:
   - Ambient sound strategy
   - Foley requirements
   - Sound effects catalog
   - Audio mixing approach

4. COLOR GRADING:
   - Overall color grade approach
   - Per-scene color treatment
   - LUT recommendations

5. DISTRIBUTION STRATEGY:
   - Target platforms (theatrical, streaming, festival)
   - Marketing approach
   - Release strategy

Respond with a JSON object matching this schema:
{{
  "video_editing": {{
    "style": "string",
    "pacing_strategy": "string",
    "key_techniques": "string"
  }},
  "vfx": {{
    "requirements": "string",
    "complexity": "string",
    "priority_shots": "string"
  }},
  "sound_design": {{
    "ambient_strategy": "string",
    "foley_requirements": "string",
    "sound_effects": "string",
    "mixing_approach": "string"
  }},
  "color_grading": {{
    "overall_approach": "string",
    "per_scene_treatment": "string",
    "lut_recommendations": "string"
  }},
  "distribution": {{
    "target_platforms": "string",
    "marketing_approach": "string",
    "release_strategy": "string"
  }}
}}

Make the plan practical, detailed, and tailored to the specific story and genre.
"""


class Stage6PostProductionPlanner(BaseStageGenerator):
    """Stage 6: Generate post-production plan for the complete project.

    This stage takes all previous project data and produces a comprehensive
    post-production and distribution plan.
    """

    def execute(self, project: Project) -> Project:
        """Execute Stage 6: Generate post-production plan.

        Args:
            project: Project with all previous stages populated.

        Returns:
            Updated project with post_production populated.

        Raises:
            ValueError: If script is missing.
        """
        self._validate_project_data(project, ["script"])

        script = project.script
        scenes = script.get("scenes", [])

        beat_sheet_summary = ""
        if project.beat_sheet:
            beat_sheet_summary = "\n".join(
                f"Beat {b['number']}: {b['name']} - {b['description'][:100]}"
                for b in project.beat_sheet.get("beats", [])
            )

        script_summary = "\n".join(
            f"Scene {s['number']}: {s['location']} - {s['description'][:150]}"
            for s in scenes
        )

        scene_descriptions = ""
        if project.scene_descriptions:
            scene_descriptions = "\n".join(
                f"Scene {sd['scene_number']}: {sd['visual_description'][:100]}"
                for sd in project.scene_descriptions
            )

        music_plan = ""
        if project.music:
            music_plan = "\n".join(
                f"Scene {m.get('scene_number', '?')}: {m.get('mood', 'N/A')}"
                for m in project.music.get("compositions", [])
            )

        prompt = POST_PROD_PROMPT.format(
            title=script.get("title", project.title),
            genre=script.get("genre", project.genre),
            tone=script.get("tone", project.tone),
            beat_sheet_summary=beat_sheet_summary,
            script_summary=script_summary,
            scene_descriptions=scene_descriptions,
            music_plan=music_plan,
        )

        messages = self._get_messages(prompt)
        response = self.client.chat(messages)
        data = self._parse_json_response(response.content)

        project.post_production = data
        project.status = "stage6_post_production_complete"

        logger.info(
            f"Stage 6 complete: Post-production plan generated for '{project.title}'"
        )
        return project
