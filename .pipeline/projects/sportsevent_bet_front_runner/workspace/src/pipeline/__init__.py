"""
Pipeline module for the Sports/Event Bet Front Runner Pipeline.
"""

from __future__ import annotations

from src.pipeline.config import PipelineConfig
from src.pipeline.feed_adapter import FeedAdapter
from src.pipeline.latency_detector import LatencyDetector
from src.pipeline.models import (
    FeedRecord,
    LatencyGap,
    ProcessedSignal,
    Signal,
    SignalStats,
)

__all__ = ["Pipeline", "LatencyDetector", "SignalStats"]
