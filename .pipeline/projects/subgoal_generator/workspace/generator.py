"""Core decomposition engine — wires prompt builder, LLM client, and parser."""

from __future__ import annotations

from subgoal_generator.models import Subgoal
from subgoal_generator.prompt_builder import build_prompt
from subgoal_generator.parser import parse_response
from subgoal_generator.llm_client import LLMClient
from subgoal_generator.output import write_pipeline_entries


class SubgoalGenerator:
    """Decomposes a high-level goal into ordered subgoals via an LLM."""

    def __init__(
        self,
        provider: str = "openai",
        llm_client: LLMClient | None = None,
        **llm_kwargs: object,
    ) -> None:
        if llm_client is not None:
            self.llm_client = llm_client
        else:
            self.llm_client = LLMClient(provider=provider, **llm_kwargs)

    def generate(
        self,
        goal: str,
        master_ideas_path: str | None = None,
        output_path: str | None = None,
    ) -> list[Subgoal]:
        """Decompose *goal* into a list of Subgoal objects.

        If *master_ideas_path* or *output_path* is provided, each subgoal is
        appended as a pipeline entry to that file.
        """
        prompt = build_prompt(goal)
        response_text = self.llm_client.complete(prompt)
        subgoals = parse_response(response_text)

        path = master_ideas_path or output_path
        if path is not None:
            write_pipeline_entries(subgoals, path)

        return subgoals
