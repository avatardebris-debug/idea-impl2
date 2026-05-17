"""
Unit tests for __init__.py (create_session convenience function).
"""
import pytest
from babble import create_session
from babble.learner import LearningSession


class TestCreateSession:
    def test_returns_learning_session(self):
        session = create_session()
        assert isinstance(session, LearningSession)

    def test_returns_session_with_language(self):
        session = create_session(language="Spanish")
        assert isinstance(session, LearningSession)
        assert session.language == "Spanish"

    def test_returns_session_without_language(self):
        session = create_session()
        assert isinstance(session, LearningSession)
        assert session.language is None

    def test_returns_new_session_each_call(self):
        session1 = create_session()
        session2 = create_session()
        assert session1 is not session2

    def test_session_has_phrases(self):
        session = create_session()
        assert len(session._study_queue) > 0

    def test_session_has_progress(self):
        session = create_session()
        assert len(session._progress) > 0

    def test_session_language_filter(self):
        session = create_session(language="French")
        for phrase in session._study_queue:
            assert phrase.language == "French"

    def test_session_has_stats(self):
        session = create_session()
        stats = session.get_session_stats()
        assert stats is not None
        assert stats.total_phrases > 0

    def test_session_can_get_next_phrase(self):
        session = create_session()
        phrase = session.get_next_phrase()
        assert phrase is not None

    def test_session_with_num_phrases(self):
        session = create_session(num_phrases=5)
        assert len(session._study_queue) == 5

    def test_session_with_zero_phrases(self):
        session = create_session(num_phrases=0)
        assert len(session._study_queue) == 0

    def test_session_with_large_num_phrases(self):
        session = create_session(num_phrases=1000)
        # Should not exceed available phrases
        assert len(session._study_queue) <= 100

    def test_session_stats_initial_state(self):
        session = create_session()
        stats = session.get_session_stats()
        assert stats.total_phrases == len(session._study_queue)
        assert stats.phrases_known == 0
        assert stats.phrases_partially_known == 0
        assert stats.phrases_new == len(session._study_queue)
