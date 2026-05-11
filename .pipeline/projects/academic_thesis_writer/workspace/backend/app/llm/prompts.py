"""Prompt templates for thesis generation."""

from __future__ import annotations

from typing import List, Optional

from ..models import CitationStyle, Source


# ── Citation format templates ────────────────────────────────

CITATION_FORMATS = {
    CitationStyle.APA: {
        "in_text": "[{author} ({year})]",
        "bibliography": "{author}. ({year}). {title}. {journal/volume}, {pages}. {url}",
    },
    CitationStyle.CHICAGO: {
        "in_text": "({author} {year})",
        "bibliography": "{author}. {year}. {title}. {journal/volume} {pages}. {url}",
    },
    CitationStyle.MLA: {
        "in_text": "({author} {page})",
        "bibliography": "{author}. \"{title}.\" {journal/volume}, {year}, {pages}. {url}.",
    },
    CitationStyle.IEEE: {
        "in_text": "[{ref_num}]",
        "bibliography": "[{ref_num}] {author}, \"{title},\" {journal/volume}, {year}.",
    },
}

# ── Section-specific prompts ────────────────────────────────

def build_section_prompt(
    section_name: str,
    topic: str,
    sources: List[Source],
    citation_style: CitationStyle,
    previous_sections: Optional[str] = None,
) -> tuple[str, str]:
    """Build system + user prompt for generating a section."""
    system = (
        f"You are an expert academic writer. Write a {section_name} section for a thesis "
        f"on the topic: \"{topic}\". Use {citation_style.value} citation style. "
        "Write in formal academic prose. Do not use bullet points or numbered lists. "
        "Integrate citations naturally into the text."
    )

    sources_text = "\n\n".join(
        f"- {s.title} ({s.year or 'n.d.'}): {s.abstract[:200]}" for s in sources
    )

    user = f"""Write the {section_name} section.

Topic: {topic}

Relevant sources:
{sources_text}
"""
    if previous_sections:
        user += f"\nPrevious sections summary:\n{previous_sections}\n"

    user += f"\nWrite in {citation_style.value} format. Include in-text citations where appropriate."
    return system, user


def build_citation_prompt(sources: List[Source], citation_style: CitationStyle) -> tuple[str, str]:
    """Build prompt for formatting citations."""
    system = f"You are a citation formatting expert. Format citations in {citation_style.value} style."
    user = "Format the following sources in " + citation_style.value + " style:\n\n"
    for i, s in enumerate(sources):
        user += f"{i+1}. {s.title} ({s.year or 'n.d.'}) by {', '.join(s.authors)}\n"
    return system, user


def build_bibliography_prompt(sources: List[Source], citation_style: CitationStyle) -> tuple[str, str]:
    """Build prompt for generating a bibliography."""
    system = f"You are an academic writer. Generate a bibliography in {citation_style.value} style."
    user = "Generate a bibliography in " + citation_style.value + " style for these sources:\n\n"
    for i, s in enumerate(sources):
        user += f"{i+1}. {s.title} ({s.year or 'n.d.'}) by {', '.join(s.authors)}\n"
    return system, user


def build_abstract_prompt(topic: str, sections: List[str]) -> tuple[str, str]:
    """Build prompt for generating an abstract."""
    system = "You are an academic writer. Write a concise, informative abstract."
    user = f"""Write an abstract for a thesis on the topic: "{topic}".

Section summaries:
{chr(10).join(sections)}

The abstract should be 150-250 words and include:
- Background/context
- Research question
- Methods
- Key findings
- Implications
"""
    return system, user


def build_literature_review_prompt(
    topic: str,
    sources: List[Source],
    citation_style: CitationStyle,
) -> tuple[str, str]:
    """Build prompt for literature review section."""
    system = (
        f"You are an expert academic writer. Write a comprehensive literature review "
        f"for a thesis on \"{topic}\". Use {citation_style.value} citation style. "
        "Synthesize sources thematically, not just summarise them individually."
    )
    user = f"Write a literature review for the topic: \"{topic}\".\n\n"
    user += "Use these sources:\n"
    for s in sources:
        user += f"- {s.title} ({s.year or 'n.d.'}): {s.abstract[:200]}\n"
    return system, user


def build_methodology_prompt(topic: str, sources: List[Source]) -> tuple[str, str]:
    """Build prompt for methodology section."""
    system = "You are an expert academic writer. Write a methodology section."
    user = f"""Write a methodology section for a thesis on the topic: "{topic}".

Relevant methodological sources:
{chr(10).join(f"- {s.title} ({s.year or 'n.d.'})" for s in sources)}

Include:
- Research design
- Data collection methods
- Analysis approach
- Limitations
"""
    return system, user


def build_results_prompt(topic: str, findings: List[str]) -> tuple[str, str]:
    """Build prompt for results section."""
    system = "You are an expert academic writer. Write a results section."
    user = f"""Write a results section for a thesis on the topic: "{topic}".

Key findings:
{chr(10).join(f"- {f}" for f in findings)}

Present findings clearly and objectively. Use academic language.
"""
    return system, user


def build_discussion_prompt(topic: str, findings: List[str], sources: List[Source]) -> tuple[str, str]:
    """Build prompt for discussion section."""
    system = "You are an expert academic writer. Write a discussion section."
    user = f"""Write a discussion section for a thesis on the topic: "{topic}".

Key findings:
{chr(10).join(f"- {f}" for f in findings)}

Relevant literature:
{chr(10).join(f"- {s.title} ({s.year or 'n.d.'})" for s in sources)}

Interpret the findings, compare with existing literature, and discuss implications.
"""
    return system, user


def build_conclusion_prompt(topic: str, key_findings: List[str]) -> tuple[str, str]:
    """Build prompt for conclusion section."""
    system = "You are an expert academic writer. Write a conclusion section."
    user = f"""Write a conclusion section for a thesis on the topic: "{topic}".

Key findings:
{chr(10).join(f"- {f}" for f in key_findings)}

Include:
- Summary of main findings
- Theoretical/practical implications
- Limitations
- Future research directions
"""
    return system, user


def build_introduction_prompt(topic: str, sources: List[Source]) -> tuple[str, str]:
    """Build prompt for introduction section."""
    system = "You are an expert academic writer. Write an introduction section."
    user = f"""Write an introduction section for a thesis on the topic: "{topic}".

Relevant background sources:
{chr(10).join(f"- {s.title} ({s.year or 'n.d.'}): {s.abstract[:200]}" for s in sources)}

Include:
- Background and context
- Problem statement
- Research questions
- Thesis structure overview
"""
    return system, user
