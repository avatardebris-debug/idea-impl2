"""Base stage generator for the AI Movie Generation Suite.

Provides a common interface for all pipeline stages.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ai_movie_gen_suite.config import AppConfig
from ai_movie_gen_suite.llm_client import LLMClient, LLMMessage, LLMResponse
from ai_movie_gen_suite.models import Project

logger = logging.getLogger(__name__)


class BaseStageGenerator(ABC):
    """Abstract base class for all pipeline stages.

    Each stage takes a Project, processes it, and returns an updated Project.
    Stages are responsible for:
    - Validating input data
    - Generating prompts
    - Calling the LLM
    - Parsing and validating responses
    - Updating the project state
    """

    def __init__(self, config: AppConfig | None = None):
        """Initialize the stage generator.

        Args:
            config: Application configuration. If None, loads from environment.
        """
        self.config = config or AppConfig()
        self.client = LLMClient(self.config.llm)

    @abstractmethod
    def execute(self, project: Project) -> Project:
        """Execute the stage on the given project.

        Args:
            project: The project to process.

        Returns:
            The updated project.

        Raises:
            ValueError: If required input data is missing.
        """
        ...

    def _get_messages(self, prompt: str) -> List[LLMMessage]:
        """Create message list from a prompt string.

        Args:
            prompt: The prompt text.

        Returns:
            List of LLMMessage objects.
        """
        return [
            LLMMessage(
                role="system",
                content=(
                    "You are an expert AI assistant for movie generation. "
                    "Always respond with valid JSON. "
                    "Do not include markdown code fences in your response."
                ),
            ),
            LLMMessage(role="user", content=prompt),
        ]

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse a JSON response from the LLM.

        Args:
            content: The raw response content.

        Returns:
            Parsed JSON as a dictionary.

        Raises:
            json.JSONDecodeError: If the content is not valid JSON.
        """
        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first and last lines (code fence markers)
            content = "\n".join(lines[1:-1])

        return json.loads(content)

    def _validate_project_data(self, project: Project, required_keys: List[str]) -> None:
        """Validate that required data exists in the project.

        Args:
            project: The project to validate.
            required_keys: List of required data keys.

        Raises:
            ValueError: If any required key is missing.
        """
        for key in required_keys:
            data = getattr(project, key, None)
            if data is None or (isinstance(data, dict) and not data):
                raise ValueError(f"Project must have '{key}' data for this stage")
