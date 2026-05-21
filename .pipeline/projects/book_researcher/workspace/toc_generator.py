"""Generate Table of Contents from niche profiles."""

from __future__ import annotations

from typing import List, Optional

from book_researcher.models import NicheProfile, Chapter, Section


def generate_toc(
    niches: List[NicheProfile],
    target_audience: str = "intermediate practitioners",
    book_length: str = "standard",
    include_case_studies: bool = True,
) -> List[Chapter]:
    """Generate a structured Table of Contents from niche profiles.

    Args:
        niches: List of NicheProfile objects representing content gaps.
        target_audience: Description of the target reader.
        book_length: One of 'short', 'standard', 'comprehensive'.
        include_case_studies: Whether to include case study chapters.

    Returns:
        List of Chapter objects forming the TOC.
    """
    chapters: List[Chapter] = []

    # Determine chapter count based on book length
    if book_length == "short":
        num_chapters = min(3, len(niches))
    elif book_length == "standard":
        num_chapters = min(6, len(niches))
    else:  # comprehensive
        num_chapters = min(10, len(niches))

    # Generate chapters from top niches
    for i, niche in enumerate(niches[:num_chapters]):
        chapter = Chapter(
            title=f"Chapter {i+1}: {niche.topic.title()} Fundamentals",
            niche=niche,
            sections=[],
        )

        # Generate sections based on niche gaps
        gap_texts = [g.text for g in niche.gaps]
        for j, gap_text in enumerate(gap_texts[:4]):  # Max 4 sections per chapter
            section = Section(
                title=f"Section {j+1}: {gap_text.title()}",
                content_hint=gap_text,
                estimated_pages=8 if book_length == "comprehensive" else 5,
            )
            chapter.sections.append(section)

        chapters.append(chapter)

    # Add case study chapter if requested and there are enough niches
    if include_case_studies and len(niches) > 1:
        case_study_chapter = Chapter(
            title="Case Studies and Applications",
            niche=niches[-1] if niches else None,
            sections=[
                Section(
                    title="Real-World Implementation",
                    content_hint="Practical examples from the identified gaps",
                    estimated_pages=15,
                ),
                Section(
                    title="Common Pitfalls and Solutions",
                    content_hint="Addressing the most frequent challenges",
                    estimated_pages=12,
                ),
            ],
        )
        chapters.append(case_study_chapter)

    return chapters
