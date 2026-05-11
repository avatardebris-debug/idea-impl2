"""Script stage generator for the AI Movie Generation Suite.

Generates the script content for a movie project.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.prompts.prompt_library import PromptLibrary
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)

prompt_library = PromptLibrary()


class ScriptStageGenerator(BaseStageGenerator):
    """Generates the script content for a movie project.

    This stage takes a project with a logline and generates a full script
    with scenes, dialogue, and character interactions.
    """

    def execute(self, project: Project) -> Project:
        """Execute the script generation stage.

        Args:
            project: The project to generate a script for.

        Returns:
            The updated project with script data.

        Raises:
            ValueError: If required input data is missing.
        """
        logger.info(f"Generating script for project: {project.title}")

        # Validate input data
        self._validate_project_data(project, ["logline"])
        if not project.logline:
            raise ValueError("Project must have a logline for script generation")

        # Generate the script
        script_data = self._generate_script(project)

        # Update the project
        project.script = script_data
        logger.info(f"Script generation complete for project: {project.title}")

        return project

    def _generate_script(self, project: Project) -> Dict[str, Any]:
        """Generate the script content.

        Args:
            project: The project to generate the script for.

        Returns:
            Dictionary containing the script data.

        Raises:
            ValueError: If the script generation fails.
        """
        # Get the prompt template
        template = prompt_library.get_template("script_generator")
        if not template:
            raise ValueError("Script generator template not found")

        # Prepare the prompt
        characters_str = json.dumps(project.characters, indent=2) if project.characters else "[]"
        prompt = template.render(
            title=project.title,
            genre=project.genre,
            tone=project.tone,
            logline=project.logline,
            characters=characters_str,
        )

        # Get messages
        messages = self._get_messages(prompt)

        # Call the LLM
        response = self.client.chat(messages)

        # Parse the response
        try:
            script_data = self._parse_json_response(response.content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse script response: {e}")
            raise ValueError(f"Failed to parse script response: {e}") from e

        # Validate the script data
        if not script_data.get("scenes"):
            raise ValueError("Generated script has no scenes")

        logger.info(f"Generated script with {len(script_data['scenes'])} scenes")

        return script_data
