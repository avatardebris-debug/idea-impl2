"""LLM integration package."""

from .openai_client import OpenAIClient
from .local_client import LocalClient
from .prompts import (
    CITATION_FORMATS,
    build_section_prompt,
    build_citation_prompt,
    build_bibliography_prompt,
    build_abstract_prompt,
    build_literature_review_prompt,
    build_methodology_prompt,
    build_results_prompt,
    build_discussion_prompt,
    build_conclusion_prompt,
    build_introduction_prompt,
)

__all__ = [
    "OpenAIClient",
    "LocalClient",
    "CITATION_FORMATS",
    "build_section_prompt",
    "build_citation_prompt",
    "build_bibliography_prompt",
    "build_abstract_prompt",
    "build_literature_review_prompt",
    "build_methodology_prompt",
    "build_results_prompt",
    "build_discussion_prompt",
    "build_conclusion_prompt",
    "build_introduction_prompt",
]
