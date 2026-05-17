"""
CLI entry point for babble.

Provides a command-line interface so users can start a learning session
from the terminal.
"""

import sys
from typing import Optional

from babble.models import Phrase
from babble.phrases import PhraseDatabase
from babble.learner import LearningSession, MasteryLevel
from babble.data.default_phrases import DEFAULT_PHRASES


def main(language: Optional[str] = None, num_phrases: int = 10):
    """Start a learning session from the CLI."""
    # Load default phrases
    db = PhraseDatabase()
    db.add_phrases(DEFAULT_PHRASES)

    # Filter by language if specified
    if language:
        phrases = db.get_by_language(language)
        if not phrases:
            print(f"Error: Language '{language}' not found in database.")
            print(f"Available languages: {', '.join(db.get_languages())}")
            sys.exit(1)
    else:
        phrases = db.get_all_phrases()

    # Limit to num_phrases
    phrases = phrases[:num_phrases]

    # Create learning session
    session = LearningSession(language=language)
    session.add_phrases(phrases)

    print("=" * 60)
    print("  Welcome to Babble - Language Learning")
    print("=" * 60)
    print(f"  {len(phrases)} phrases loaded.")
    if language:
        print(f"  Language: {language}")
    print("  Type 'quit' to end the session.")
    print("=" * 60)
    print()

    # Learning loop
    while True:
        next_phrase = session.get_next_phrase()
        if next_phrase is None:
            break

        # Display the phrase
        print("-" * 40)
        print(f"  [{next_phrase.language}] {next_phrase.text}")
        print(f"  Translation: {next_phrase.translation}")
        print(f"  Context: {next_phrase.context}")
        print("-" * 40)

        # Get user assessment
        try:
            response = input("  How well do you know this? (known/partially_known/new/quit): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if response in ("quit", "q", "exit"):
            break
        elif response in ("known", "k"):
            session.mark_known(next_phrase.text)
            print("  ✓ Marked as known!")
        elif response in ("partially_known", "partially", "p"):
            session.mark_partially_known(next_phrase.text)
            print("  ~ Marked as partially known!")
        elif response in ("new", "n"):
            session.mark_new(next_phrase.text)
            print("  → Reset to new.")
        else:
            print("  Unrecognized response. Phrase not updated.")

        print()

    # Session summary
    stats = session.end_session()
    print()
    print(stats.summary())
    print()
    print("Thanks for using Babble! See you next time. 👋")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Babble - Language Learning CLI")
    parser.add_argument(
        "-l", "--language",
        type=str,
        default=None,
        help="Language to study (e.g., Spanish, French, English)",
    )
    parser.add_argument(
        "-n", "--num-phrases",
        type=int,
        default=10,
        help="Number of phrases to study (default: 10)",
    )
    args = parser.parse_args()

    main(language=args.language, num_phrases=args.num_phrases)
