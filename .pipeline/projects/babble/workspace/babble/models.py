"""
Phrase data model for babble.

Defines the Phrase dataclass and PhraseDatabase class that stores
common phrases across multiple languages with usage-frequency metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Phrase:
    """Represents a single phrase in a language with metadata."""
    text: str
    language: str
    frequency_rank: int
    translation: str = ""
    context: str = ""

    def __repr__(self):
        return f"Phrase(text={self.text!r}, language={self.language!r}, freq={self.frequency_rank})"


class PhraseDatabase:
    """Stores and queries phrases across multiple languages."""

    def __init__(self):
        self._phrases: List[Phrase] = []
        self._by_language: Dict[str, List[Phrase]] = {}
        self._by_rank: Dict[int, Phrase] = {}

    def add_phrase(self, phrase: Phrase) -> None:
        """Add a phrase to the database."""
        self._phrases.append(phrase)
        # Index by language
        if phrase.language not in self._by_language:
            self._by_language[phrase.language] = []
        self._by_language[phrase.language].append(phrase)
        # Index by frequency rank
        self._by_rank[phrase.frequency_rank] = phrase

    def add_phrases(self, phrases: List[Phrase]) -> None:
        """Add multiple phrases to the database."""
        for p in phrases:
            self.add_phrase(p)

    def get_by_language(self, language: str) -> List[Phrase]:
        """Get all phrases for a given language."""
        return list(self._by_language.get(language, []))

    def get_by_frequency_rank(self, rank: int) -> Optional[Phrase]:
        """Get a phrase by its frequency rank."""
        return self._by_rank.get(rank)

    def get_phrases_by_rank_range(self, min_rank: int, max_rank: int) -> List[Phrase]:
        """Get phrases within a frequency rank range (inclusive)."""
        return [p for p in self._phrases if min_rank <= p.frequency_rank <= max_rank]

    def get_all_phrases(self) -> List[Phrase]:
        """Get all phrases, sorted by frequency rank."""
        return sorted(self._phrases, key=lambda p: p.frequency_rank)

    def get_languages(self) -> List[str]:
        """Get list of all languages in the database."""
        return list(self._by_language.keys())

    def get_phrases_for_language(self, language: str) -> List[Phrase]:
        """Alias for get_by_language."""
        return self.get_by_language(language)

    def __len__(self) -> int:
        return len(self._phrases)

    def __repr__(self):
        return f"PhraseDatabase(languages={self.get_languages()}, total={len(self._phrases)})"
