"""
drill_cli.py — Interactive drill loop for spaced repetition flashcards.

Provides multiple practice modes:
    - translate: See L1, type L2, then reveal
    - reverse: See L2, type L1, then reveal
    - shadow: Read both aloud, matching original audio rhythm
    - mixed: Randomly alternate between modes

Usage:
    python -m video_babbel_enhanced drill --mode translate
    python -m video_babbel_enhanced drill --mode mixed --limit 20
    python -m video_babbel_enhanced drill --mode reverse --session "Morning drill"
"""
from __future__ import annotations
import argparse
import pathlib
import random
import sys
import textwrap
from datetime import datetime
from typing import Any

from video_babbel_enhanced import session_db


_MODES = ["translate", "reverse", "shadow", "mixed"]


class DrillCLI:
    """Interactive drill CLI for spaced repetition."""

    def __init__(
        self,
        mode: str = "translate",
        limit: int = 20,
        session_name: str | None = None,
        db_path: str | pathlib.Path = session_db._DEFAULT_DB,
    ):
        """Initialize the drill CLI.

        Args:
            mode: Practice mode.
            limit: Maximum cards to review.
            session_name: Name for this drill session.
            db_path: Path to SQLite database.
        """
        self.mode = mode
        self.limit = limit
        self.session_name = session_name
        self.db_path = pathlib.Path(db_path)

    def get_modes(self) -> list[str]:
        """Return list of available practice modes."""
        return list(_MODES)

    def validate_mode(self, mode: str) -> bool:
        """Check if a mode is valid."""
        return mode in _MODES

    def get_input(self, prompt: str) -> str:
        """Get user input with a prompt."""
        return input(prompt)

    def display_card(self, card: dict[str, Any], mode: str) -> None:
        """Display a flashcard to the user."""
        print("\n" + "=" * 50)
        print(f"  Clip: {card.get('clip_id', '?')}")
        print(f"  Score: {card.get('freq_score', 0):.4f}  |  "
              f"EF: {card.get('ease_factor', 2.5):.2f}  |  "
              f"Rep: {card.get('repetition', 0)}")
        print("-" * 50)

        if mode in ("translate", "reverse", "shadow", "mixed"):
            print(f"  L1 (source): {card.get('l1_text', '')}")
        if mode in ("reverse", "mixed"):
            print(f"  L2 (target): {card.get('l2_text', '')}")
        if mode in ("translate", "mixed"):
            print(f"  L2 (target): {card.get('l2_text', '')}")
        if mode == "shadow":
            print(f"  L1 (source): {card.get('l1_text', '')}")
            print(f"  L2 (target): {card.get('l2_text', '')}")
            print("  👄 SHADOWING MODE: Read both aloud, matching the original audio rhythm")
        print("-" * 50)

    def display_review_buttons(self) -> None:
        """Display review quality options."""
        print("\n  How well did you know this?")
        print("  0 = blackout, 1 = very hard, 2 = hard,")
        print("  3 = okay, 4 = good, 5 = perfect")
        print("  (0-5, or 'q' to quit): ")

    def get_quality(self) -> int:
        """Get quality rating from user (0-5)."""
        try:
            answer = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            return -1

        if answer == "q":
            return -1

        try:
            quality = int(answer)
            if 0 <= quality <= 5:
                return quality
        except ValueError:
            pass

        return 0

    def run(self) -> None:
        """Run the main drill loop."""
        # Get cards
        due = session_db.get_due_clips(self.db_path)
        new = session_db.get_new_clips(self.db_path, limit=self.limit)

        if not due and not new:
            print("\n  No cards to review! Import some clips first:")
            print("    python -m video_babbel_enhanced import-clips clips/")
            return

        # Build card pool
        pool: list[dict] = []
        if due:
            print(f"\n  Due for review: {len(due)} cards")
            pool.extend(due)
        if new:
            print(f"  New cards: {len(new)} cards")
            pool.extend(new)

        if self.mode == "mixed":
            random.shuffle(pool)

        # Create session if requested
        session_id = None
        if self.session_name:
            session_id = session_db.create_session(self.session_name, f"{self.mode} drill session", db_path=self.db_path)
            print(f"\n  Session '{self.session_name}' created (id={session_id})")

        # Show stats
        stats = session_db.get_session_stats(self.db_path)
        print(f"\n  Stats: {stats['total_clips']} total | {stats['due']} due | "
              f"{stats['new']} new | {stats['mastered']} mastered")
        print(f"  Mode: {self.mode} | Limit: {self.limit}")
        print("  Press Ctrl+C to quit\n")

        # Drill loop
        reviewed = 0
        for card in pool:
            if reviewed >= self.limit:
                break

            # Display card
            self.display_card(card, self.mode)

            # Get quality rating
            quality = self.get_quality()
            if quality == -1:
                break

            # Update card
            session_db.update_card(card["clip_id"], quality, db_path=self.db_path)

            # Log session if active
            if session_id is not None:
                session_db.log_review(session_id, card["clip_id"], quality, db_path=self.db_path)

            reviewed += 1

        # Final stats
        stats = session_db.get_session_stats(self.db_path)
        print(f"\n  ✓ Session complete! {reviewed} cards reviewed")
        print(f"  Total: {stats['total_clips']} | Due: {stats['due']} | "
              f"New: {stats['new']} | Mastered: {stats['mastered']}")


def main() -> None:
    """CLI entry point for the drill loop."""
    parser = argparse.ArgumentParser(description="Interactive drill loop")
    parser.add_argument("--mode", default="translate", choices=_MODES, help="Practice mode")
    parser.add_argument("--limit", type=int, default=20, help="Max cards to review")
    parser.add_argument("--session", help="Name for this drill session")
    parser.add_argument("--db", default=str(session_db._DEFAULT_DB), help="Database path")
    args = parser.parse_args()

    cli = DrillCLI(
        mode=args.mode,
        limit=args.limit,
        session_name=args.session,
        db_path=args.db,
    )
    cli.run()


if __name__ == "__main__":
    main()
