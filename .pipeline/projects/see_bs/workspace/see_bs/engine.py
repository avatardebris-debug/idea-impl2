"""Scoring engine — runs all filters and aggregates results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from see_bs.models import NewsArticle
from see_bs.filters import ALL_FILTERS


@dataclass
class FilterBreakdown:
    """Result from a single filter."""
    name: str
    score: float
    explanation: str


@dataclass
class AnalysisResult:
    """Composite result from the scoring engine."""
    bs_score: float  # 0–100, higher = more BS
    breakdown: List[FilterBreakdown] = field(default_factory=list)
    summary: str = ""

    def __str__(self) -> str:
        lines = [
            "=" * 60,
            "  See BS — News Article Analysis",
            "=" * 60,
            f"  BS Score: {self.bs_score:.0f}/100",
            "-" * 60,
        ]
        for b in self.breakdown:
            lines.append(f"  [{b.name}]  Score: {b.score:.0f}/100")
            lines.append(f"    {b.explanation}")
            lines.append("")
        lines.append("-" * 60)
        lines.append(f"  Summary: {self.summary}")
        lines.append("=" * 60)
        return "\n".join(lines)


class ScoreEngine:
    """Run all BS detection filters on an article and aggregate."""

    @staticmethod
    def analyze(article: NewsArticle) -> AnalysisResult:
        """Analyze a single article and return structured results."""
        breakdown: List[FilterBreakdown] = []
        total_score = 0.0

        for filt in ALL_FILTERS:
            result = filt(article)
            name = filt.__name__.replace("filter_", "").replace("_", " ").title()
            breakdown.append(FilterBreakdown(
                name=name,
                score=result["score"],
                explanation=result["explanation"],
            ))
            total_score += result["score"]

        # Average across filters → 0–100
        bs_score = total_score / len(ALL_FILTERS) if ALL_FILTERS else 0
        bs_score = round(max(0, min(100, bs_score)), 1)

        # Generate summary
        if bs_score >= 70:
            verdict = "High BS — treat with extreme skepticism."
        elif bs_score >= 45:
            verdict = "Moderate BS — cross-reference with opposing sources."
        elif bs_score >= 25:
            verdict = "Low BS — some caution advised."
        else:
            verdict = "Very low BS — appears relatively trustworthy."

        summary = (
            f"BS Score {bs_score}/100. {verdict} "
            f"Analyzed {len(breakdown)} filters."
        )

        return AnalysisResult(
            bs_score=bs_score,
            breakdown=breakdown,
            summary=summary,
        )
