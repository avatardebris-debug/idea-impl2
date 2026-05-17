"""
Core module for babble — provides high-level convenience functions
and re-exports key classes for easy access.
"""

from babble.models import Phrase
from babble.phrases import PhraseDatabase
from babble.learner import LearningSession
from babble.mnemonics import generate_mnemonic, assign_phrase_to_palace

__all__ = [
    "Phrase",
    "PhraseDatabase",
    "LearningSession",
    "generate_mnemonic",
    "assign_phrase_to_palace",
]


def create_session(phrases=None, language=None):
    """Convenience function to create a new learning session with optional phrases or language."""
    session = LearningSession(language=language)
    if phrases:
        for p in phrases:
            session.add_phrase(p)
    return session
