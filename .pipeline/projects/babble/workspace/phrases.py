"""
Phrase database utilities for babble.

Provides helpers for loading, managing, and querying phrase databases.
"""

from typing import List, Optional
from babble.models import Phrase, PhraseDatabase


def create_default_database() -> PhraseDatabase:
    """Create and return a PhraseDatabase with common phrases."""
    from babble.data.default_phrases import DEFAULT_PHRASES
    db = PhraseDatabase()
    db.add_phrases(DEFAULT_PHRASES)
    return db


def load_phrases_from_list(phrases: List[Phrase]) -> PhraseDatabase:
    """Load a list of phrases into a PhraseDatabase."""
    db = PhraseDatabase()
    db.add_phrases(phrases)
    return db


def filter_phrases(
    db: PhraseDatabase,
    language: Optional[str] = None,
    max_rank: Optional[int] = None,
    min_rank: Optional[int] = None,
) -> List[Phrase]:
    """Filter phrases from a database by various criteria."""
    phrases = db.get_all_phrases()

    if language:
        phrases = [p for p in phrases if p.language == language]

    if min_rank is not None:
        phrases = [p for p in phrases if p.frequency_rank >= min_rank]

    if max_rank is not None:
        phrases = [p for p in phrases if p.frequency_rank <= max_rank]

    return phrases


def get_top_phrases(db: PhraseDatabase, language: Optional[str] = None, n: int = 10) -> List[Phrase]:
    """Get the top N most common phrases."""
    phrases = db.get_all_phrases()
    if language:
        phrases = [p for p in phrases if p.language == language]
    return sorted(phrases, key=lambda p: p.frequency_rank)[:n]
