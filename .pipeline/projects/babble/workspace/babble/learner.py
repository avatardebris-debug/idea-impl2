"""
Learning session engine for babble.

Implements the core learning loop that presents phrases to the user
in order of usage value, tracks progress, and implements spaced
repetition basics.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime, timedelta

from babble.models import Phrase


class MasteryLevel(Enum):
    """Mastery level for a phrase."""
    NEW = "new"
    PARTIALLY_KNOWN = "partially_known"
    KNOWN = "known"
    MASTERED = "mastered"


@dataclass
class PhraseProgress:
    """Tracks progress for a single phrase."""
    phrase: Phrase
    mastery: MasteryLevel = MasteryLevel.NEW
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    review_count: int = 0
    streak: int = 0

    def mark_known(self) -> None:
        """Mark phrase as known."""
        self.mastery = MasteryLevel.KNOWN
        self.last_reviewed = datetime.now()
        self.review_count += 1
        self.streak += 1
        self.next_review = self._calculate_next_review()

    def mark_partially_known(self) -> None:
        """Mark phrase as partially known."""
        self.mastery = MasteryLevel.PARTIALLY_KNOWN
        self.last_reviewed = datetime.now()
        self.review_count += 1
        self.next_review = self._calculate_next_review()

    def mark_new(self) -> None:
        """Reset phrase to new."""
        self.mastery = MasteryLevel.NEW
        self.last_reviewed = None
        self.next_review = None
        self.streak = 0

    def _calculate_next_review(self) -> datetime:
        """Calculate next review time using spaced repetition."""
        if self.mastery == MasteryLevel.KNOWN:
            # Review in 1 day
            return datetime.now() + timedelta(days=1)
        elif self.mastery == MasteryLevel.PARTIALLY_KNOWN:
            # Review in 4 hours
            return datetime.now() + timedelta(hours=4)
        elif self.mastery == MasteryLevel.MASTERED:
            # Review in 7 days
            return datetime.now() + timedelta(days=7)
        else:
            # Review immediately
            return datetime.now()


@dataclass
class SessionStats:
    """Statistics for a learning session."""
    total_phrases: int = 0
    phrases_known: int = 0
    phrases_partially_known: int = 0
    phrases_new: int = 0
    phrases_mastered: int = 0
    total_reviews: int = 0
    average_streak: float = 0.0
    session_start: Optional[datetime] = None
    session_end: Optional[datetime] = None

    def summary(self) -> str:
        """Return a human-readable summary of session statistics."""
        lines = [
            "=== Learning Session Summary ===",
            f"Total phrases: {self.total_phrases}",
            f"Known: {self.phrases_known}",
            f"Partially known: {self.phrases_partially_known}",
            f"New: {self.phrases_new}",
            f"Mastered: {self.phrases_mastered}",
            f"Total reviews: {self.total_reviews}",
            f"Average streak: {self.average_streak:.1f}",
        ]
        if self.session_start:
            lines.append(f"Session start: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.session_end:
            lines.append(f"Session end: {self.session_end.strftime('%Y-%m-%d %H:%M:%S')}")
        return "\n".join(lines)


class LearningSession:
    """Core learning loop that presents phrases and tracks progress."""

    def __init__(self, language: Optional[str] = None, num_phrases: int = 10):
        self.language = language
        self._progress: Dict[str, PhraseProgress] = {}  # keyed by phrase text
        self._study_queue: List[Phrase] = []
        self._stats = SessionStats()
        self._stats.session_start = datetime.now()
        self._num_phrases = num_phrases

    def add_phrase(self, phrase: Phrase) -> None:
        """Add a phrase to the session."""
        if self.language and phrase.language != self.language:
            return
        if phrase.text not in self._progress:
            self._progress[phrase.text] = PhraseProgress(phrase=phrase)
            self._study_queue.append(phrase)

    def add_phrases(self, phrases: List[Phrase]) -> None:
        """Add multiple phrases to the session."""
        for p in phrases:
            self.add_phrase(p)

    def get_next_phrase(self) -> Optional[Phrase]:
        """Get the next phrase to study, prioritized by frequency rank and mastery."""
        if not self._study_queue:
            return None

        # Prioritize: NEW > PARTIALLY_KNOWN > KNOWN > MASTERED
        priority_order = {
            MasteryLevel.NEW: 0,
            MasteryLevel.PARTIALLY_KNOWN: 1,
            MasteryLevel.KNOWN: 2,
            MasteryLevel.MASTERED: 3,
        }

        # Sort by priority, then by frequency rank
        self._study_queue.sort(
            key=lambda p: (
                priority_order.get(self._progress[p.text].mastery, 0),
                p.frequency_rank,
            )
        )

        # Return the highest priority phrase and remove it from the queue
        next_phrase = self._study_queue.pop(0)
        return next_phrase

    def mark_known(self, phrase_text: str) -> bool:
        """Mark a phrase as known."""
        if phrase_text not in self._progress:
            return False
        progress = self._progress[phrase_text]
        progress.mark_known()
        self._stats.total_reviews += 1
        return True

    def mark_partially_known(self, phrase_text: str) -> bool:
        """Mark a phrase as partially known."""
        if phrase_text not in self._progress:
            return False
        progress = self._progress[phrase_text]
        progress.mark_partially_known()
        self._stats.total_reviews += 1
        return True

    def mark_new(self, phrase_text: str) -> bool:
        """Reset a phrase to new."""
        if phrase_text not in self._progress:
            return False
        progress = self._progress[phrase_text]
        progress.mark_new()
        return True

    def get_session_stats(self) -> SessionStats:
        """Get current session statistics."""
        self._update_stats()
        return self._stats

    def _update_stats(self) -> None:
        """Update session statistics from progress data."""
        self._stats.total_phrases = len(self._progress)
        self._stats.phrases_known = sum(
            1 for p in self._progress.values() if p.mastery == MasteryLevel.KNOWN
        )
        self._stats.phrases_partially_known = sum(
            1 for p in self._progress.values() if p.mastery == MasteryLevel.PARTIALLY_KNOWN
        )
        self._stats.phrases_new = sum(
            1 for p in self._progress.values() if p.mastery == MasteryLevel.NEW
        )
        self._stats.phrases_mastered = sum(
            1 for p in self._progress.values() if p.mastery == MasteryLevel.MASTERED
        )
        if self._progress:
            self._stats.average_streak = sum(p.streak for p in self._progress.values()) / len(self._progress)

    def get_phrase_mastery(self, phrase_text: str) -> Optional[MasteryLevel]:
        """Get the mastery level of a phrase."""
        if phrase_text in self._progress:
            return self._progress[phrase_text].mastery
        return None

    def get_remaining_phrases(self) -> List[Phrase]:
        """Get phrases that still need to be studied."""
        return [
            p.phrase for p in self._progress.values()
            if p.mastery in (MasteryLevel.NEW, MasteryLevel.PARTIALLY_KNOWN)
        ]

    def end_session(self) -> SessionStats:
        """End the session and return final statistics."""
        self._stats.session_end = datetime.now()
        self._update_stats()
        return self._stats
