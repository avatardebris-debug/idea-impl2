"""Scene stage generator for the AI Movie Generation Suite.

Generates detailed scene descriptions for a movie project.
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


class SceneStageGenerator(BaseStageGenerator):
    """Generates detailed scene descriptions for a movie project.

    This stage takes a project with a script and generates detailed scene
    descriptions including visual directions, camera work, lighting, etc.
    """

    def execute(self, project: Project) -> Project:
        """Execute the scene generation stage.

        Args:
            project: The project to generate scenes for.

        Returns:
            The updated project with scene data.

        Raises:
            ValueError: If required input data is missing.
        """
        logger.info(f"Generating scenes for project: {project.title}")

        # Validate input data
        self._validate_project_data(project, ["script"])
        if not project.script or not project.script.get("scenes"):
            raise ValueError("Project must have script scenes for scene generation")

        # Generate scenes
        scenes_data = self._generate_scenes(project)

        # Update the project
        project.scenes = scenes_data
        logger.info(f"Scene generation complete for project: {project.title}")

        return project

    def _generate_scenes(self, project: Project) -> List[Dict[str, Any]]:
        """Generate detailed scene descriptions.

        Args:
            project: The project to generate scenes for.

        Returns:
            List of scene description dictionaries.

        Raises:
            ValueError: If the scene generation fails.
        """
        scenes_data = []

        for i, scene in enumerate(project.script.get("scenes", [])):
            logger.info(f"Generating scene {i + 1}/{len(project.script['scenes'])}")

            # Get the prompt template
            template = prompt_library.get_template("scene_generator")
            if not template:
                raise ValueError("Scene generator template not found")

            # Prepare the prompt
            prompt = template.render(
                scene_number=scene.get("number", i + 1),
                location=scene.get("location", "Unknown"),
                description=scene.get("description", ""),
                genre=project.genre,
                tone=project.tone,
            )

            # Get messages
            messages = self._get_messages(prompt)

            # Call the LLM
            response = self.client.chat(messages)

            # Parse the response
            try:
                scene_data = self._parse_json_response(response.content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse scene response: {e}")
                raise ValueError(f"Failed to parse scene response: {e}") from e

            scenes_data.append(scene_data)

        logger.info(f"Generated {len(scenes_data)} scenes")

        return scenes_data
