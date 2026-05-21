"""End-to-end pipeline: reviews -> gaps -> niches -> TOC."""

from __future__ import annotations

import logging
from typing import List, Optional

from book_researcher.aggregators.sample_reviews import get_sample_reviews
from book_researcher.aggregator import SampleReviewAggregator
from book_researcher.gap_extractor import extract_gaps
from book_researcher.models import Gap, NicheProfile, TableOfContents
from book_researcher.niche_profiler import profile_niches
from book_researcher.toc_generator import generate_toc

logger = logging.getLogger(__name__)


class PipelineResult:
    """Container for all pipeline outputs."""

    def __init__(
        self,
        reviews: list[dict],
        gaps: list[Gap],
        niches: list[NicheProfile],
        toc: TableOfContents,
    ) -> None:
        self.reviews = reviews
        self.gaps = gaps
        self.niches = niches
        self.toc = toc

    def summary(self) -> str:
        """Return a human-readable summary of the pipeline results."""
        lines = [
            f"Book Title: {self.toc.book_title}",
            f"Target Audience: {self.toc.target_audience}",
            f"Total Reviews Analyzed: {len(self.reviews)}",
            f"Content Gaps Found: {len(self.gaps)}",
            f"Market Niches Identified: {len(self.niches)}",
            f"Estimated Total Pages: {self.toc.estimated_total_pages}",
            "",
            "Table of Contents:",
        ]
        for ch in self.toc.chapters:
            lines.append(
                f"  Ch. {ch.chapter_number}: {ch.title} "
                f"(priority: {ch.priority_score:.2f}, est. {ch.estimated_pages} pages)"
            )
            for topic in ch.key_topics:
                lines.append(f"    - {topic}")
        lines.append("")
        lines.append("Market Niches:")
        for niche in self.niches:
            lines.append(
                f"  - {niche.topic} (score: {niche.score:.2f}, "
                f"gaps: {niche.gap_count}, avg rating: {niche.avg_rating:.2f})"
            )
        return "\n".join(lines)


class BookResearcherPipeline:
    """End-to-end pipeline for book research."""

    def __init__(
        self,
        book_title: str = "The Underserved Book",
        max_chapters: int = 12,
        target_audience: str = "Practitioners seeking comprehensive coverage",
    ) -> None:
        self.book_title = book_title
        self.max_chapters = max_chapters
        self.target_audience = target_audience

    def run(
        self,
        book_titles: Optional[List[str]] = None,
    ) -> List[TableOfContents]:
        """Run the full pipeline and return a list of TableOfContents.

        Args:
            book_titles: List of book titles to analyze. If None, uses sample reviews.

        Returns:
            A list of TableOfContents (one per book analyzed).
        """
        # Step 1: Fetch reviews
        aggregator = SampleReviewAggregator()
        all_reviews: list[dict] = []
        if book_titles:
            for title in book_titles:
                reviews = aggregator.fetch_reviews(title)
                all_reviews.extend(reviews)
        else:
            sample = get_sample_reviews()
            all_reviews = [
                {"text": r.text, "rating": r.rating, "book_id": r.book_id, "source": r.source}
                for r in sample
            ]

        if not all_reviews:
            # Return empty TOC when no reviews
            return [
                generate_toc(
                    niches=[],
                    max_chapters=self.max_chapters,
                    book_title=self.book_title,
                    target_audience=self.target_audience,
                )
            ]

        # Step 2: Extract gaps
        gaps = extract_gaps(all_reviews)

        # Step 3: Profile niches
        niches = profile_niches(gaps)

        # Step 4: Generate TOC
        toc = generate_toc(
            niches=niches,
            max_chapters=self.max_chapters,
            book_title=self.book_title,
            target_audience=self.target_audience,
        )

        # Return as list of one TOC (consistent with multi-book support)
        return [toc]


def run_pipeline(
    book_titles: Optional[List[str]] = None,
    book_title: str = "The Underserved Book",
    max_chapters: int = 12,
    target_audience: str = "Practitioners seeking comprehensive coverage",
) -> List[TableOfContents]:
    """Convenience function to run the full pipeline.

    Args:
        book_titles: List of book titles to analyze.
        book_title: Title for the generated book.
        max_chapters: Maximum number of chapters.
        target_audience: Target audience description.

    Returns:
        A list of TableOfContents.
    """
    if not book_titles:
        return []
    pipeline = BookResearcherPipeline(
        book_title=book_title,
        max_chapters=max_chapters,
        target_audience=target_audience,
    )
    return pipeline.run(book_titles=book_titles)
