"""
Unit tests for LearningSession (learner.py).
"""
import pytest
from datetime import datetime, timedelta
from babble.models import Phrase
from babble.learner import (
    MasteryLevel,
    PhraseProgress,
    SessionStats,
    LearningSession,
)


# ---------------------------------------------------------------------------
# MasteryLevel tests
# ---------------------------------------------------------------------------

class TestMasteryLevel:
    def test_mastery_level_values(self):
        assert MasteryLevel.NEW.value == "new"
        assert MasteryLevel.PARTIALLY_KNOWN.value == "partially_known"
        assert MasteryLevel.KNOWN.value == "known"
        assert MasteryLevel.MASTERED.value == "mastered"

    def test_mastery_level_equality(self):
        assert MasteryLevel.NEW == MasteryLevel.NEW
        assert MasteryLevel.NEW != MasteryLevel.KNOWN


# ---------------------------------------------------------------------------
# PhraseProgress tests
# ---------------------------------------------------------------------------

class TestPhraseProgress:
    def test_phrase_progress_initial_state(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        progress = PhraseProgress(phrase=phrase)
        assert progress.mastery == MasteryLevel.NEW
        assert progress.last_reviewed is None
        assert progress.next_review is None
        assert progress.review_count == 0
        assert progress.streak == 0

    def test_mark_known(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        progress = PhraseProgress(phrase=phrase)
        progress.mark_known()
        assert progress.mastery == MasteryLevel.KNOWN
        assert progress.last_reviewed is not None
        assert progress.next_review is not None
        assert progress.review_count == 1
        assert progress.streak == 1

    def test_mark_partially_known(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        progress = PhraseProgress(phrase=phrase)
        progress.mark_partially_known()
        assert progress.mastery == MasteryLevel.PARTIALLY_KNOWN
        assert progress.last_reviewed is not None
        assert progress.next_review is not None
        assert progress.review_count == 1
        assert progress.streak == 0

    def test_mark_new_resets_state(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        progress = PhraseProgress(phrase=phrase)
        progress.mark_known()
        progress.mark_new()
        assert progress.mastery == MasteryLevel.NEW
        assert progress.last_reviewed is None
        assert progress.next_review is None
        assert progress.review_count == 1  # review_count is not reset
        assert progress.streak == 0

    def test_next_review_known(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        progress = PhraseProgress(phrase=phrase)
        progress.mark_known()
        # Should be approximately 1 day from now
        assert progress.next_review > datetime.now()
        assert progress.next_review < datetime.now() + timedelta(days=2)

    def test_next_review_partially_known(self):
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        progress = PhraseProgress(phrase=phrase)
        progress.mark_partially_known()
        # Should be approximately 4 hours from now
        assert progress.next_review > datetime.now()
        assert progress.next_review < datetime.now() + timedelta(hours=5)


# ---------------------------------------------------------------------------
# SessionStats tests
# ---------------------------------------------------------------------------

class TestSessionStats:
    def test_session_stats_summary(self):
        stats = SessionStats(
            total_phrases=10,
            phrases_known=5,
            phrases_partially_known=3,
            phrases_new=2,
            phrases_mastered=0,
            total_reviews=15,
            average_streak=2.5,
        )
        summary = stats.summary()
        assert "Learning Session Summary" in summary
        assert "Total phrases: 10" in summary
        assert "Known: 5" in summary
        assert "Partially known: 3" in summary
        assert "New: 2" in summary
        assert "Mastered: 0" in summary
        assert "Total reviews: 15" in summary
        assert "Average streak: 2.5" in summary

    def test_session_stats_with_dates(self):
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 10, 30, 0)
        stats = SessionStats(
            session_start=start,
            session_end=end,
        )
        summary = stats.summary()
        assert "2024-01-01 10:00:00" in summary
        assert "2024-01-01 10:30:00" in summary


# ---------------------------------------------------------------------------
# LearningSession tests
# ---------------------------------------------------------------------------

class TestLearningSession:
    def test_create_session(self):
        session = LearningSession()
        assert session.language is None
        assert session.get_session_stats().total_phrases == 0

    def test_create_session_with_language(self):
        session = LearningSession(language="English")
        assert session.language == "English"

    def test_add_phrase(self):
        session = LearningSession()
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        session.add_phrase(phrase)
        stats = session.get_session_stats()
        assert stats.total_phrases == 1

    def test_add_phrases(self):
        session = LearningSession()
        phrases = [
            Phrase(text="Hello", language="English", frequency_rank=1),
            Phrase(text="Hola", language="Spanish", frequency_rank=2),
        ]
        session.add_phrases(phrases)
        stats = session.get_session_stats()
        assert stats.total_phrases == 2

    def test_add_phrase_language_filter(self):
        session = LearningSession(language="English")
        session.add_phrase(Phrase(text="Hello", language="English", frequency_rank=1))
        session.add_phrase(Phrase(text="Hola", language="Spanish", frequency_rank=2))
        stats = session.get_session_stats()
        assert stats.total_phrases == 1

    def test_get_next_phrase(self):
        session = LearningSession()
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        session.add_phrase(phrase)
        next_phrase = session.get_next_phrase()
        assert next_phrase is not None
        assert next_phrase.text == "Hello"

    def test_get_next_phrase_empty(self):
        session = LearningSession()
        next_phrase = session.get_next_phrase()
        assert next_phrase is None

    def test_mark_known(self):
        session = LearningSession()
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        session.add_phrase(phrase)
        result = session.mark_known("Hello")
        assert result is True
        mastery = session.get_phrase_mastery("Hello")
        assert mastery == MasteryLevel.KNOWN

    def test_mark_known_unknown_phrase(self):
        session = LearningSession()
        result = session.mark_known("Unknown")
        assert result is False

    def test_mark_partially_known(self):
        session = LearningSession()
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        session.add_phrase(phrase)
        result = session.mark_partially_known("Hello")
        assert result is True
        mastery = session.get_phrase_mastery("Hello")
        assert mastery == MasteryLevel.PARTIALLY_KNOWN

    def test_mark_new(self):
        session = LearningSession()
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        session.add_phrase(phrase)
        session.mark_known("Hello")
        result = session.mark_new("Hello")
        assert result is True
        mastery = session.get_phrase_mastery("Hello")
        assert mastery == MasteryLevel.NEW

    def test_session_stats_after_reviews(self):
        session = LearningSession()
        phrase1 = Phrase(text="Hello", language="English", frequency_rank=1)
        phrase2 = Phrase(text="Hola", language="Spanish", frequency_rank=2)
        session.add_phrases([phrase1, phrase2])
        session.mark_known("Hello")
        session.mark_partially_known("Hola")
        stats = session.get_session_stats()
        assert stats.total_phrases == 2
        assert stats.phrases_known == 1
        assert stats.phrases_partially_known == 1
        assert stats.phrases_new == 0
        assert stats.total_reviews == 2

    def test_get_phrase_mastery(self):
        session = LearningSession()
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        session.add_phrase(phrase)
        mastery = session.get_phrase_mastery("Hello")
        assert mastery == MasteryLevel.NEW

    def test_get_phrase_mastery_unknown(self):
        session = LearningSession()
        mastery = session.get_phrase_mastery("Unknown")
        assert mastery is None

    def test_get_remaining_phrases(self):
        session = LearningSession()
        phrase1 = Phrase(text="Hello", language="English", frequency_rank=1)
        phrase2 = Phrase(text="Hola", language="Spanish", frequency_rank=2)
        session.add_phrases([phrase1, phrase2])
        session.mark_known("Hello")
        remaining = session.get_remaining_phrases()
        assert len(remaining) == 1
        assert remaining[0].text == "Hola"

    def test_end_session(self):
        session = LearningSession()
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        session.add_phrase(phrase)
        stats = session.end_session()
        assert stats.session_end is not None
        assert stats.session_start is not None

    def test_study_queue_prioritization(self):
        session = LearningSession()
        new_phrase = Phrase(text="New", language="English", frequency_rank=10)
        known_phrase = Phrase(text="Known", language="English", frequency_rank=1)
        session.add_phrases([new_phrase, known_phrase])
        session.mark_known("Known")
        # Next phrase should be the new one (higher priority)
        next_phrase = session.get_next_phrase()
        assert next_phrase.text == "New"

    def test_duplicate_phrase_not_added_twice(self):
        session = LearningSession()
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        session.add_phrase(phrase)
        session.add_phrase(phrase)
        stats = session.get_session_stats()
        assert stats.total_phrases == 1

    def test_session_stats_average_streak(self):
        session = LearningSession()
        phrase1 = Phrase(text="Hello", language="English", frequency_rank=1)
        phrase2 = Phrase(text="Hola", language="Spanish", frequency_rank=2)
        session.add_phrases([phrase1, phrase2])
        session.mark_known("Hello")  # streak = 1
        session.mark_known("Hola")   # streak = 1
        stats = session.get_session_stats()
        assert stats.average_streak == 1.0

    def test_session_stats_new_phrases_count(self):
        session = LearningSession()
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        session.add_phrase(phrase)
        stats = session.get_session_stats()
        assert stats.phrases_new == 1

    def test_session_stats_mastered_count(self):
        session = LearningSession()
        phrase = Phrase(text="Hello", language="English", frequency_rank=1)
        session.add_phrase(phrase)
        progress = session._progress["Hello"]
        progress.mastery = MasteryLevel.MASTERED
        stats = session.get_session_stats()
        assert stats.phrases_mastered == 1
