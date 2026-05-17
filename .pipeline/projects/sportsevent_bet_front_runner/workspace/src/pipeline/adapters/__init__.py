"""
Adapters module for the Sports/Event Bet Front Runner Pipeline.
"""

from __future__ import annotations

from src.pipeline.adapters.mock_nfl_feed import MockNFLFeed
from src.pipeline.adapters.mock_nba_feed import MockNBAGameFeed

__all__ = ["MockNFLFeed", "MockNBAGameFeed"]
