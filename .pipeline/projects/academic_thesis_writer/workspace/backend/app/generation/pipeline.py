"""Generation pipeline.

Orchestrates the step-by-step generation of thesis sections using
the LLM client and prompt templates.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from ..models import Draft, DraftSection, Source
from .llm_client import GenerationLLMClient
from .prompts import (
    build_abstract_prompt,
    build_conclusion_prompt,
    build_discussion_prompt,
    build_introduction_prompt,
    build_literature_review_prompt,
    build_methodology_prompt,
    build_results_prompt,
)

logger = logging.getLogger(__name__)

# Default section order
DEFAULT_SECTIONS = [
    "Introduction",
    "Literature Review",
    "Methodology",
    "Results",
    "Discussion",
    "Conclusion",
]


class GenerationPipeline:
    """Orchestrates thesis section generation."""

    def __init__(
        self,
        llm_client: GenerationLLMClient,
        sections: Optional[List[str]] = None,
    ):
        self.llm = llm_client
        self.sections = sections or DEFAULT_SECTIONS

    async def generate_all(
        self,
        topic: str,
        sources: List[Source],
        draft: Draft,
    ) -> Draft:
        """Generate all sections for a thesis draft."""
        logger.info("Starting generation pipeline for topic: %s", topic)

        previous_summary = None

        for section_name in self.sections:
            logger.info("Generating section: %s", section_name)
            content = await self._generate_section(
                section_name, topic, sources, previous_summary
            )
            draft.sections.append(DraftSection(name=section_name, content=content))
            previous_summary = content[:500] + "..." if len(content) > 500 else content

        # Generate abstract
        logger.info("Generating abstract")
        section_summaries = [s.content[:300] for s in draft.sections]
        abstract = await self._generate_abstract(topic, section_summaries)
        draft.abstract = abstract

        # Generate conclusion
        logger.info("Generating conclusion")
        conclusion = await self._generate_conclusion(topic, section_summaries)
        # Append conclusion if not already generated
        if not any(s.name == "Conclusion" for s in draft.sections):
            draft.sections.append(DraftSection(name="Conclusion", content=conclusion))

        logger.info("Generation pipeline complete: %d sections", len(draft.sections))
        return draft

    async def _generate_section(
        self,
        section_name: str,
        topic: str,
        sources: List[Source],
        previous_summary: Optional[str],
    ) -> str:
        """Generate a single section."""
        system, user = self._build_section_prompt(section_name, topic, sources, previous_summary)
        return await self.llm.generate(system, user)

    def _build_section_prompt(
        self,
        section_name: str,
        topic: str,
        sources: List[Source],
        previous_summary: Optional[str],
    ) -> tuple[str, str]:
        """Build system and user prompts for a section."""
        system = (
            f"You are an expert academic writer. Write a {section_name} section for a thesis "
            f"on the topic: \"{topic}\". Write in formal academic prose. "
            "Do not use bullet points or numbered lists. "
            "Integrate citations naturally into the text."
        )

        user = f"Write the {section_name} section for a thesis on: {topic}"

        if sources:
            source_list = "\n".join(
                f"- {s.title} ({s.year})" for s in sources[:10]
            )
            user += f"\n\nRelevant sources:\n{source_list}"

        if previous_summary:
            user += f"\n\nPrevious section summary: {previous_summary}"

        return system, user

    async def _generate_abstract(self, topic: str, section_summaries: List[str]) -> str:
        """Generate the abstract."""
        system = (
            "You are an expert academic writer. Write a concise abstract (150-250 words) "
            "for a thesis. Summarize the purpose, methods, key findings, and implications."
        )
        user = f"Topic: {topic}\n\nSection summaries:\n" + "\n".join(section_summaries)
        return await self.llm.generate(system, user)

    async def _generate_conclusion(self, topic: str, section_summaries: List[str]) -> str:
        """Generate the conclusion."""
        system = (
            "You are an expert academic writer. Write a conclusion section for a thesis. "
            "Summarize key findings, discuss implications, and suggest future research directions."
        )
        user = f"Topic: {topic}\n\nSection summaries:\n" + "\n".join(section_summaries)
        return await self.llm.generate(system, user)
