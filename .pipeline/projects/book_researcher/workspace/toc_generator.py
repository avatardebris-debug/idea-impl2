"""Table of contents generator that builds a TOC from niche profiles."""

from __future__ import annotations

import logging
from typing import List, Optional

from book_researcher.models import NicheProfile, TableOfContents, TOCChapter

logger = logging.getLogger(__name__)


def _generate_chapters(
    niches: list[NicheProfile],
    max_chapters: int = 12,
    book_title: str = "The Underserved Book",
    target_audience: str = "Practitioners seeking comprehensive coverage",
) -> list[TOCChapter]:
    """Generate TOC chapters from the top niche profiles.

    Each niche becomes a chapter. Chapters are ordered by niche score.

    Args:
        niches: List of NicheProfile objects.
        max_chapters: Maximum number of chapters to generate.
        book_title: Title for the generated book.
        target_audience: Target audience description.

    Returns:
        List of TOCChapter objects.
    """
    if not niches:
        logger.warning("No niches provided to generate chapters")
        return []

    # Take top niches up to max_chapters
    top_niches = niches[:max_chapters]

    chapters: list[TOCChapter] = []
    for i, niche in enumerate(top_niches, start=1):
        # Generate a descriptive chapter title from the niche topic
        chapter_title = f"Chapter {i}: {niche.topic.title()} - Addressing the Gap"

        # Estimate pages based on gap count
        estimated_pages = max(5, niche.gap_count * 10)

        chapter = TOCChapter(
            chapter_number=i,
            title=chapter_title,
            estimated_pages=estimated_pages,
            related_gaps=niche.sample_gaps,
        )
        chapters.append(chapter)

    logger.info("Generated %d chapters from %d niches", len(chapters), len(niches))
    return chapters


def generate_toc(
    niches: list[NicheProfile],
    max_chapters: int = 12,
    book_title: str = "The Underserved Book",
    target_audience: str = "Practitioners seeking comprehensive coverage",
) -> TableOfContents:
    """Generate a complete TableOfContents from niche profiles.

    Args:
        niches: List of NicheProfile objects.
        max_chapters: Maximum number of chapters.
        book_title: Title for the generated book.
        target_audience: Target audience description.

    Returns:
        A TableOfContents object.

    Raises:
        ValueError: If niches is empty.
    """
    if not niches:
        raise ValueError("Cannot generate TOC from empty niches list")

    chapters = _generate_chapters(
        niches=niches,
        max_chapters=max_chapters,
        book_title=book_title,
        target_audience=target_audience,
    )

    total_pages = sum(ch.estimated_pages for ch in chapters)

    toc = TableOfContents(
        book_title=book_title,
        target_audience=target_audience,
        chapters=chapters,
        total_chapters=len(chapters),
        estimated_total_pages=total_pages,
    )

    logger.info("Generated TOC: %s (%d chapters, %d pages)", book_title, len(chapters), total_pages)
    return toc
