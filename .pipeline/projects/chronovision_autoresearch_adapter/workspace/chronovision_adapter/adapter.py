"""Main adapter — ties together sources, funding, and prediction into a unified API."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from chronovision_adapter.models import Paper, FundingEvent, ResearchTrend
from chronovision_adapter.sources import MultiSourceSearch, PaperSource
from chronovision_adapter.funding import FundingTracker, FundingSignal
from chronovision_adapter.predictor import ImpactPredictor, PaperImpact

logger = logging.getLogger(__name__)


class ChronovisionAdapter:
    """Unified adapter combining research paper tracking and funding signal analysis.

    This is the main entry point for the Chronovision Autoresearch system.
    """

    def __init__(
        self,
        sources: Optional[List[PaperSource]] = None,
        funding_tracker: Optional[FundingTracker] = None,
        predictor: Optional[ImpactPredictor] = None,
    ):
        self.search = MultiSourceSearch(sources)
        self.funding = funding_tracker or FundingTracker()
        self.predictor = predictor or ImpactPredictor()

    def research(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Run a full research query — papers + funding signals + predictions.

        Args:
            query: The research topic to investigate.
            max_results: Max papers per source.

        Returns:
            Dict with 'papers', 'impacts', 'trends', 'funding_signals', 'summary'.
        """
        # Search papers
        papers = self.search.search_all(query, max_per_source=max_results)

        # Predict impact
        impacts = self.predictor.rank_papers(papers)

        # Detect research trends
        trends = self.predictor.detect_trends(papers)

        # Get funding signals for relevant sectors
        funding_signals = self.funding.get_top_funded_sectors(top_n=5)

        # Build summary
        summary = self._build_summary(query, papers, impacts, trends, funding_signals)

        return {
            "query": query,
            "papers": [p.to_dict() for p in papers],
            "impacts": [i.to_dict() for i in impacts],
            "trends": [t.to_dict() for t in trends],
            "funding_signals": [s.to_dict() for s in funding_signals],
            "summary": summary,
        }

    def predict_paper_impact(self, paper: Paper) -> PaperImpact:
        """Predict impact for a single paper."""
        return self.predictor.predict(paper)

    def get_funding_signal(self, sector: str) -> FundingSignal:
        """Get funding signal for a sector."""
        return self.funding.get_sector_signal(sector)

    def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Retrieve a specific paper by ID."""
        return self.search.get_paper(paper_id)

    def dashboard(self) -> Dict[str, Any]:
        """Generate a dashboard overview of current research and funding landscape.

        Returns:
            Dict with sector signals, top trends, and key papers.
        """
        sectors = self.funding.get_all_sectors()
        sector_signals = {s: self.funding.get_sector_signal(s).to_dict() for s in sectors}

        # Get all papers and rank
        all_papers = self.search.search_all("", max_per_source=10)
        top_impacts = self.predictor.rank_papers(all_papers)[:5]

        return {
            "total_papers_tracked": len(all_papers),
            "total_funding_events": len(self.funding.events),
            "sectors": sector_signals,
            "top_papers": [i.to_dict() for i in top_impacts],
            "sources": self.search.source_names,
        }

    def to_json(self, data: Dict[str, Any]) -> str:
        """Serialize any result dict to JSON."""
        return json.dumps(data, indent=2, default=str)

    def _build_summary(
        self,
        query: str,
        papers: List[Paper],
        impacts: List[PaperImpact],
        trends: List[ResearchTrend],
        funding_signals: List[FundingSignal],
    ) -> str:
        """Build a human-readable summary of research results."""
        lines = [f"Research Summary: {query}", f"Papers found: {len(papers)}"]

        if impacts:
            top = impacts[0]
            lines.append(f"Top paper: {top.title} (impact: {top.impact_score}/100)")

        if trends:
            trend_names = [t.topic for t in trends[:3]]
            lines.append(f"Key trends: {', '.join(trend_names)}")

        critical_sectors = [s for s in funding_signals if s.alert_level in ("critical", "high")]
        if critical_sectors:
            lines.append(f"Hot funding sectors: {', '.join(s.sector for s in critical_sectors)}")

        return " | ".join(lines)
