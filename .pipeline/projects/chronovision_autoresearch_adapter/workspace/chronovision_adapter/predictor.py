"""Impact predictor — estimates the impact a paper will have and predicts trends."""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from chronovision_adapter.models import Paper, ResearchTrend

logger = logging.getLogger(__name__)


@dataclass
class PaperImpact:
    """Predicted impact assessment for a paper."""
    paper_id: str
    title: str
    impact_score: float  # 0-100
    citation_velocity: float  # predicted citations/year
    industry_relevance: float  # 0-1
    novelty_score: float  # 0-1
    category: str  # "breakthrough", "incremental", "survey", "application"
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "impact_score": self.impact_score,
            "citation_velocity": self.citation_velocity,
            "industry_relevance": self.industry_relevance,
            "novelty_score": self.novelty_score,
            "category": self.category,
            "reasoning": self.reasoning,
        }


# Keywords that signal high-impact papers
BREAKTHROUGH_SIGNALS = [
    "novel", "first", "state-of-the-art", "sota", "breakthrough", "outperforms",
    "surpasses", "unprecedented", "paradigm", "revolutionary", "fundamental",
]

APPLICATION_SIGNALS = [
    "deploy", "production", "real-world", "applied", "industrial", "commercial",
    "system", "platform", "tool", "framework", "library",
]

SURVEY_SIGNALS = [
    "survey", "review", "overview", "comprehensive", "tutorial", "meta-analysis",
]


class ImpactPredictor:
    """Predicts the impact and category of research papers.

    Uses heuristic scoring based on citation count, keyword signals,
    author reputation proxy (citation count), and publication venue.
    """

    def predict(self, paper: Paper) -> PaperImpact:
        """Predict the impact of a single paper.

        Args:
            paper: The paper to assess.

        Returns:
            PaperImpact with scores and category.
        """
        # Citation velocity (annualized)
        citation_velocity = self._estimate_velocity(paper)

        # Novelty score
        novelty = self._score_novelty(paper)

        # Industry relevance
        industry = self._score_industry_relevance(paper)

        # Category
        category = self._categorize(paper)

        # Overall impact score (0-100)
        impact = self._compute_impact(paper, citation_velocity, novelty, industry)

        reasoning = self._build_reasoning(paper, impact, category, novelty, industry)

        return PaperImpact(
            paper_id=paper.paper_id,
            title=paper.title,
            impact_score=round(impact, 1),
            citation_velocity=round(citation_velocity, 1),
            industry_relevance=round(industry, 3),
            novelty_score=round(novelty, 3),
            category=category,
            reasoning=reasoning,
        )

    def predict_batch(self, papers: List[Paper]) -> List[PaperImpact]:
        """Predict impact for multiple papers."""
        return [self.predict(p) for p in papers]

    def rank_papers(self, papers: List[Paper]) -> List[PaperImpact]:
        """Rank papers by predicted impact (highest first)."""
        impacts = self.predict_batch(papers)
        impacts.sort(key=lambda i: i.impact_score, reverse=True)
        return impacts

    def detect_trends(self, papers: List[Paper]) -> List[ResearchTrend]:
        """Detect research trends from a batch of papers.

        Groups papers by primary keyword overlap and returns trend signals.
        """
        # Group by primary category/keyword
        topic_papers: Dict[str, List[Paper]] = {}
        for paper in papers:
            topic = paper.categories[0] if paper.categories else "general"
            topic_papers.setdefault(topic, []).append(paper)

        trends: List[ResearchTrend] = []
        for topic, topic_group in topic_papers.items():
            total_citations = sum(p.citation_count for p in topic_group)
            momentum = min(len(topic_group) / 3.0, 1.0) * 0.4 + min(total_citations / 5000, 1.0) * 0.6

            trends.append(ResearchTrend(
                topic=topic,
                paper_count=len(topic_group),
                momentum_score=round(momentum, 3),
                top_papers=[p.paper_id for p in sorted(topic_group, key=lambda p: p.citation_count, reverse=True)[:3]],
            ))

        trends.sort(key=lambda t: t.momentum_score, reverse=True)
        return trends

    def _estimate_velocity(self, paper: Paper) -> float:
        """Estimate annualized citation rate."""
        if paper.citation_count <= 0:
            return 0.0
        # Simple heuristic based on total citations
        return paper.citation_count * 0.15  # ~15% annual growth proxy

    def _score_novelty(self, paper: Paper) -> float:
        """Score novelty based on title/abstract keywords."""
        text = (paper.title + " " + paper.abstract).lower()
        hits = sum(1 for sig in BREAKTHROUGH_SIGNALS if sig in text)
        return min(hits / 3.0, 1.0)

    def _score_industry_relevance(self, paper: Paper) -> float:
        """Score industry relevance."""
        text = (paper.title + " " + paper.abstract).lower()
        hits = sum(1 for sig in APPLICATION_SIGNALS if sig in text)
        return min(hits / 3.0, 1.0)

    def _categorize(self, paper: Paper) -> str:
        """Categorize paper type."""
        text = (paper.title + " " + paper.abstract).lower()
        survey_hits = sum(1 for s in SURVEY_SIGNALS if s in text)
        if survey_hits >= 2:
            return "survey"
        breakthrough_hits = sum(1 for s in BREAKTHROUGH_SIGNALS if s in text)
        app_hits = sum(1 for s in APPLICATION_SIGNALS if s in text)
        if breakthrough_hits >= 2:
            return "breakthrough"
        if app_hits >= 2:
            return "application"
        return "incremental"

    def _compute_impact(self, paper: Paper, velocity: float, novelty: float, industry: float) -> float:
        """Compute composite impact score 0-100."""
        citation_score = min(math.log1p(paper.citation_count) / 10.0, 1.0) * 40
        velocity_score = min(velocity / 500, 1.0) * 20
        novelty_score = novelty * 25
        industry_score = industry * 15
        return min(citation_score + velocity_score + novelty_score + industry_score, 100.0)

    def _build_reasoning(self, paper: Paper, impact: float, category: str, novelty: float, industry: float) -> str:
        """Build a human-readable reasoning string."""
        parts = [f"Category: {category}"]
        if paper.citation_count > 1000:
            parts.append(f"Highly cited ({paper.citation_count} citations)")
        if novelty > 0.5:
            parts.append("Contains breakthrough language")
        if industry > 0.5:
            parts.append("Strong industry relevance signals")
        parts.append(f"Overall impact: {impact:.0f}/100")
        return "; ".join(parts)
