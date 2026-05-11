"""Prompt templates for thesis generation."""

from __future__ import annotations

from typing import List

from ..models import Source


def build_introduction_prompt(topic: str, sources: List[Source]) -> tuple[str, str]:
    """Build system and user prompts for the Introduction section."""
    system = (
        "You are an expert academic writer. Write the Introduction section for a thesis. "
        "Include: background context, problem statement, research questions, objectives, "
        "and significance of the study. Write in formal academic prose."
    )
    user = f"Topic: {topic}\n\nWrite the Introduction section."
    if sources:
        user += f"\n\nRelevant sources:\n" + "\n".join(f"- {s.title} ({s.year})" for s in sources[:5])
    return system, user


def build_literature_review_prompt(topic: str, sources: List[Source]) -> tuple[str, str]:
    """Build system and user prompts for the Literature Review section."""
    system = (
        "You are an expert academic writer. Write the Literature Review section for a thesis. "
        "Synthesize existing research, identify gaps, and position the current study. "
        "Use thematic organization. Write in formal academic prose."
    )
    user = f"Topic: {topic}\n\nWrite the Literature Review section."
    if sources:
        user += f"\n\nRelevant sources:\n" + "\n".join(f"- {s.title} ({s.year})" for s in sources[:10])
    return system, user


def build_methodology_prompt(topic: str, sources: List[Source]) -> tuple[str, str]:
    """Build system and user prompts for the Methodology section."""
    system = (
        "You are an expert academic writer. Write the Methodology section for a thesis. "
        "Include: research design, data collection methods, sampling strategy, "
        "data analysis procedures, and ethical considerations. Write in formal academic prose."
    )
    user = f"Topic: {topic}\n\nWrite the Methodology section."
    if sources:
        user += f"\n\nRelevant sources:\n" + "\n".join(f"- {s.title} ({s.year})" for s in sources[:5])
    return system, user


def build_results_prompt(topic: str, sources: List[Source]) -> tuple[str, str]:
    """Build system and user prompts for the Results section."""
    system = (
        "You are an expert academic writer. Write the Results section for a thesis. "
        "Present findings clearly, objectively, and in logical order. "
        "Refer to tables/figures where appropriate. Write in formal academic prose."
    )
    user = f"Topic: {topic}\n\nWrite the Results section."
    if sources:
        user += f"\n\nRelevant sources:\n" + "\n".join(f"- {s.title} ({s.year})" for s in sources[:5])
    return system, user


def build_discussion_prompt(topic: str, sources: List[Source]) -> tuple[str, str]:
    """Build system and user prompts for the Discussion section."""
    system = (
        "You are an expert academic writer. Write the Discussion section for a thesis. "
        "Interpret results, compare with prior research, discuss implications, "
        "acknowledge limitations, and suggest future research. Write in formal academic prose."
    )
    user = f"Topic: {topic}\n\nWrite the Discussion section."
    if sources:
        user += f"\n\nRelevant sources:\n" + "\n".join(f"- {s.title} ({s.year})" for s in sources[:10])
    return system, user


def build_conclusion_prompt(topic: str, sources: List[Source]) -> tuple[str, str]:
    """Build system and user prompts for the Conclusion section."""
    system = (
        "You are an expert academic writer. Write the Conclusion section for a thesis. "
        "Summarize key findings, discuss implications, and suggest future research directions. "
        "Write in formal academic prose."
    )
    user = f"Topic: {topic}\n\nWrite the Conclusion section."
    if sources:
        user += f"\n\nRelevant sources:\n" + "\n".join(f"- {s.title} ({s.year})" for s in sources[:5])
    return system, user


def build_abstract_prompt(topic: str, section_summaries: List[str]) -> tuple[str, str]:
    """Build system and user prompts for the Abstract."""
    system = (
        "You are an expert academic writer. Write a concise abstract (150-250 words) "
        "for a thesis. Summarize the purpose, methods, key findings, and implications."
    )
    user = f"Topic: {topic}\n\nSection summaries:\n" + "\n".join(section_summaries)
    return system, user
