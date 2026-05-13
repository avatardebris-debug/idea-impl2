"""Chronovision Autoresearch Adapter — tracks research papers and funding signals."""

from chronovision_adapter.sources import ArxivSource, OpenReviewSource, BioRxivSource
from chronovision_adapter.funding import FundingTracker, FundingSignal
from chronovision_adapter.predictor import ImpactPredictor, PaperImpact
from chronovision_adapter.models import Paper, FundingEvent, ResearchTrend
from chronovision_adapter.adapter import ChronovisionAdapter

__all__ = [
    "ArxivSource",
    "OpenReviewSource",
    "BioRxivSource",
    "FundingTracker",
    "FundingSignal",
    "ImpactPredictor",
    "PaperImpact",
    "Paper",
    "FundingEvent",
    "ResearchTrend",
    "ChronovisionAdapter",
]
