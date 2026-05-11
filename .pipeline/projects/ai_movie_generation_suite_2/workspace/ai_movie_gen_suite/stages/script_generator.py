"""Stage 4: Script Writing generator.

Takes a beat sheet and character data to generate a full screenplay script.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import Project, Script, Scene, DialogueLine
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class ScriptGenerator(BaseStageGenerator):
    """Generate a screenplay script from beat sheet and characters.

    Uses the SCRIPT_WRITING prompt template to create a full screenplay
    with scenes, dialogue, and action descriptions.
    """

    def execute(self, project: Project) -> Project:
        """Execute script generation on the project.

        Args:
            project: Project with beat sheet and character data.

        Returns:
            Updated project with script populated.
        """
        beat_sheet = project.beat_sheet
        characters = project.characters

        if not beat_sheet:
            raise ValueError("Project must have beat sheet for script generation")

        from ai_movie_gen_suite.prompts import prompt_library

        # Extract beat descriptions
        beats = beat_sheet.get("beats", [])
        beats_str = "\n".join(
            f"Beat {b.get('number', i+1)}: {b.get('name', '')} - {b.get('description', '')}"
            for i, b in enumerate(beats)
        )

        # Extract character info
        chars = characters.get("characters", []) if characters else []
        chars_str = "\n".join(
            f"- {c.get('name', '')}: {c.get('description', '')}"
            for c in chars
        )

        prompt = prompt_library.render_template(
            "script_writing",
            title=beat_sheet.get("title", project.title),
            genre=beat_sheet.get("genre", project.genre),
            logline=beat_sheet.get("logline", project.logline),
            synopsis=beat_sheet.get("synopsis", ""),
            beats=beats_str,
            characters=chars_str,
            num_scenes=len(beats),
        )
        messages = self._get_messages(prompt)

        response = self.client.generate(messages)
        data = self._parse_json_response(response.content)

        # Convert to Script model
        scenes_data = data.get("scenes", [])
        scenes = [
            Scene(
                number=s.get("number", i + 1),
                location=s.get("location", ""),
                description=s.get("description", ""),
                dialogue=[
                    DialogueLine(
                        character=d.get("character", ""),
                        dialogue=d.get("dialogue", ""),
                        action=d.get("action"),
                    )
                    for d in s.get("dialogue", [])
                ],
                characters_present=s.get("characters_present", []),
            )
            for i, s in enumerate(scenes_data)
        ]

        script = Script(
            title=beat_sheet.get("title", project.title),
            genre=beat_sheet.get("genre", project.genre),
            tone=beat_sheet.get("tone", project.tone),
            scenes=scenes,
        )

        project.script = script.to_dict()
        project.status = "script_written"
        logger.info(f"Script written: {script.title} with {len(script.scenes)} scenes")
        return project
