"""
babble — Duolingo-style language learning with memory palace techniques.

Find the most common phrases across multiple languages.
Learn in order of usage value. Use accelerating learning techniques.
"""

from babble.models import Phrase  # noqa: F401
from babble.phrases import PhraseDatabase, create_default_database  # noqa: F401
from babble.learner import LearningSession  # noqa: F401
from babble.mnemonics import generate_mnemonic, assign_phrase_to_palace  # noqa: F401


def create_session(language=None, num_phrases=10):
    """Create a new learning session with phrases from the default database."""
    db = create_default_database()
    if language:
        phrases = db.get_by_language(language)
    else:
        phrases = db.get_all_phrases()

    # Limit to num_phrases
    phrases = phrases[:num_phrases]

    session = LearningSession(language=language)
    session.add_phrases(phrases)
    return session


__version__ = "0.1.0"
__all__ = [
    "Phrase",
    "PhraseDatabase",
    "LearningSession",
    "generate_mnemonic",
    "assign_phrase_to_palace",
    "create_session",
]
