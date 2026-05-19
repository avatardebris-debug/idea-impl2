"""
scheduler.py — SM-2 spaced repetition scheduler.

Implements the SM-2 algorithm (from SuperMemo) adapted for clip-based
language learning. Each clip (flashcard) has:
    - interval: days until next review
    - repetition: how many times reviewed successfully
    - ease_factor: how easy/hard the card is (starts at 2.5)
    - due_date: when it's next due

Algorithm (per review):
    If quality >= 3 (correct):
        repetition += 1
        if repetition == 1: interval = 1 day
        elif repetition == 2: interval = 6 days
        else: interval = interval * ease_factor
    If quality < 3 (incorrect):
        repetition = 0
        interval = 1 day
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(1.3, ease_factor)
    due_date = now + interval
"""
from __future__ import annotations
import math
from datetime import datetime, timedelta
from typing import Any


def _next_review_date(
    ease_factor: float,
    repetition: int,
    interval_days: float,
    quality: int,
) -> tuple[float, int, float]:
    """Compute next ease_factor, repetition, and interval_days after a review.

    Args:
        ease_factor: Current ease factor (SM-2 EF).
        repetition: Current number of successful repetitions.
        interval_days: Current interval in days.
        quality: Self-rated quality (0-5).

    Returns:
        (new_ease_factor, new_repetition, new_interval_days)
    """
    if quality >= 3:
        new_repetition = repetition + 1
        if new_repetition == 1:
            new_interval = 1.0
        elif new_repetition == 2:
            new_interval = 6.0
        else:
            new_interval = interval_days * ease_factor
    else:
        new_repetition = 0
        new_interval = 1.0

    # Update ease factor
    ef_change = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    new_ease = ease_factor + ef_change
    new_ease = max(1.3, new_ease)

    return new_ease, new_repetition, new_interval


def schedule_review(
    card: dict[str, Any],
    quality: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Update a card's scheduling data after a review.

    Args:
        card: Card dict with keys: ease_factor, repetition, interval_days, due_date.
        quality: Quality rating 0-5 (0=blackout, 5=perfect).
        now: Current datetime (default: datetime.now()).

    Returns:
        Updated card dict.
    """
    if now is None:
        now = datetime.now()

    ef = card.get("ease_factor", 2.5)
    rep = card.get("repetition", 0)
    interval = card.get("interval_days", 0.0)

    new_ef, new_rep, new_interval = _next_review_date(ef, rep, interval, quality)

    card["ease_factor"] = round(new_ef, 2)
    card["repetition"] = new_rep
    card["interval_days"] = round(new_interval, 1)
    card["due_date"] = (now + timedelta(days=new_interval)).isoformat()
    card["last_review"] = now.isoformat()
    card["last_quality"] = quality

    return card


def get_due_cards(
    cards: list[dict[str, Any]],
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return cards that are due for review (due_date <= now).

    Sorts by: due_date ascending, then ease_factor descending (hardest first among same date).
    """
    if now is None:
        now = datetime.now()

    due = []
    for card in cards:
        due_date_str = card.get("due_date")
        if due_date_str is None:
            due.append(card)  # never reviewed → due now
            continue
        due_date = datetime.fromisoformat(due_date_str)
        if due_date <= now:
            due.append(card)

    # Sort: earliest due first, then hardest (lowest ease_factor) first
    # Use empty string for None due_dates (sorts first)
    due.sort(key=lambda c: (
        "" if c.get("due_date") is None else c["due_date"],
        -c.get("ease_factor", 2.5)
    ))
    return due


def get_new_cards(
    cards: list[dict[str, Any]],
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return cards that have never been reviewed (no due_date or due_date is None).

    These are "new" cards that should be introduced.
    """
    new = []
    for card in cards:
        due_date_str = card.get("due_date")
        if due_date_str is None:
            new.append(card)
    return new[:limit]


def get_stats(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute summary statistics for a set of cards."""
    total = len(cards)
    new = sum(1 for c in cards if c.get("due_date") is None)
    due = sum(1 for c in cards if c.get("due_date") and datetime.fromisoformat(c["due_date"]) <= datetime.now())
    mastered = sum(1 for c in cards if c.get("repetition", 0) >= 5)
    avg_ef = sum(c.get("ease_factor", 2.5) for c in cards) / total if total else 0

    return {
        "total": total,
        "new": new,
        "due": due,
        "mastered": mastered,
        "avg_ease_factor": round(avg_ef, 2),
    }
