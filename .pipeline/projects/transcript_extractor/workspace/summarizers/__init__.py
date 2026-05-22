"""
Summarizers package initialization.

Provides different summarization strategies.
"""

from .summary_strategies import (
    SummaryStrategy,
    ExtractiveSummarizer,
    AbstractiveSummarizer,
    SimpleLengthBasedSummarizer,
)

__all__ = [
    "SummaryStrategy",
    "ExtractiveSummarizer",
    "AbstractiveSummarizer",
    "SimpleLengthBasedSummarizer",
]
