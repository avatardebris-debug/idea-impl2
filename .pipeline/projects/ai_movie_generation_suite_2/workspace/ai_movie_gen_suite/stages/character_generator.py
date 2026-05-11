"""Stage 3: Character Design generator.

Takes a movie concept and generates detailed character profiles.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from ai_movie_gen_suite.llm_client import LLMClient
from ai_movie_gen_suite.models import CharacterRegistry, Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator

logger = logging.getLogger(__name__)


class CharacterGenerator(BaseStageGenerator):
    """Generate character profiles from a movie concept.

    Uses the CHARACTER_DESIGN prompt template to create detailed character
    descriptions including physical appearance, personality, motivation, and arc.
    """

    def execute(self, project: Project) -> Project:
        """Execute character generation on the project.

        Args:
            project: Project with concept data.

        Returns:
            Updated project with characters populated.
        """
        concept = project.beat_sheet
        if not concept:
            raise ValueError("Project must have concept data for character generation")

        from ai_movie_gen_suite.prompts import prompt_library

        # Build character list from concept or use defaults
        characters_input = concept.get("characters", ["Protagonist", "Antagonist"])
        characters_str = "\n".join(f"- {c}" for c in characters_input)

        prompt = prompt_library.render_template(
            "character_design",
            title=concept.get("title", ""),
            genre=concept.get("genre", ""),
            synopsis=concept.get("synopsis", ""),
            characters=characters_str,
        )
        messages = self._get_messages(prompt)

        response = self.client.generate(messages)
        data = self._parse_json_response(response.content)

        # Convert to CharacterRegistry model
        characters_data = data.get("characters", [])
        registry = CharacterRegistry(
            characters=[
                {
                    "name": c.get("name", "Unknown"),
                    "role": c.get("role", "supporting"),
                    "age": c.get("age"),
                    "gender": c.get("gender"),
                    "description": c.get("physical_description", c.get("description", "")),
                    "motivation": c.get("motivation", ""),
                    "arc": c.get("arc", ""),
                    "relationships": c.get("relationships", {}),
                }
                for c in characters_data
            ]
        )

        project.characters = registry.to_dict()
        project.status = "characters_created"
        logger.info(f"Characters created: {len(registry.characters)} characters")
        return project
