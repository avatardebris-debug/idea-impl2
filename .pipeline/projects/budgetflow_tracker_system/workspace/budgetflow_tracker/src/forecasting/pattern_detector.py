"""Recurring pattern detection engine for BudgetFlow Tracker."""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from src.core.database import Database
from src.forecasting.models import RecurringPattern

logger = logging.getLogger(__name__)


@dataclass
class _RawOccurrence:
    """A single occurrence of a recurring transaction."""
    date: date
    amount: float
    category_name: Optional[str] = None


class PatternDetector:
    """Detect recurring transaction patterns from historical data."""

    # Pattern type heuristics
    _SALARY_KEYWORDS = {"payroll", "salary", "direct deposit", "paycheck", "wages"}
    _RENT_KEYWORDS = {"rent", "apartment", "mortgage", "lease"}
    _SUBSCRIPTION_KEYWORDS = {
        "netflix", "spotify", "hulu", "amazon prime", "apple",
        "google play", "subscription", "membership", "premium",
        "adobe", "microsoft", "dropbox", "icloud", "youtube",
    }
    _UTILITY_KEYWORDS = {"electric", "water", "gas", "internet", "phone", "utility"}
    _INSURANCE_KEYWORDS = {"insurance", "premium", "health", "auto", "life"}

    def __init__(self, db: Database):
        self.db = db

    def detect_patterns(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_occurrences: int = 3,
        min_confidence: float = 0.5,
    ) -> list[RecurringPattern]:
        """Detect recurring transaction patterns.

        Args:
            start_date: Start of analysis window. Defaults to 365 days ago.
            end_date: End of analysis window. Defaults to today.
            min_occurrences: Minimum occurrences to qualify as a pattern.
            min_confidence: Minimum confidence threshold.

        Returns:
            List of RecurringPattern objects sorted by confidence descending.
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        # Fetch all transactions in range
        transactions = self.db.fetchall(
            """SELECT date, description, amount, category_name
               FROM transactions
               WHERE date >= ? AND date <= ?
               ORDER BY date ASC""",
            (start_date.isoformat(), end_date.isoformat()),
        )

        if not transactions:
            logger.info("No transactions found for pattern detection.")
            return []

        # Group by normalized description
        groups = self._group_transactions(transactions)

        # Detect patterns for each group
        patterns: list[RecurringPattern] = []
        for description, occurrences in groups.items():
            if len(occurrences) < min_occurrences:
                continue

            pattern = self._analyze_pattern(description, occurrences)
            if pattern and pattern.confidence >= min_confidence:
                patterns.append(pattern)

        # Sort by confidence descending, then by occurrence count
        patterns.sort(key=lambda p: (p.confidence, p.occurrence_count), reverse=True)

        logger.info("Detected %d recurring patterns (min_occ=%d, min_conf=%.2f)",
                     len(patterns), min_occurrences, min_confidence)
        return patterns

    def _group_transactions(
        self,
        transactions: list[dict],
    ) -> dict[str, list[_RawOccurrence]]:
        """Group transactions by normalized description."""
        groups: dict[str, list[_RawOccurrence]] = defaultdict(list)

        for txn in transactions:
            desc = txn.get("description") or ""
            if not desc.strip():
                continue

            # Normalize: lowercase, strip extra spaces, remove common prefixes
            normalized = self._normalize_description(desc)
            if normalized:
                groups[normalized].append(_RawOccurrence(
                    date=date.fromisoformat(txn["date"]),
                    amount=txn["amount"],
                    category_name=txn.get("category_name"),
                ))

        return groups

    def _normalize_description(self, description: str) -> Optional[str]:
        """Normalize a transaction description for grouping."""
        if not description:
            return None

        # Lowercase and strip
        text = description.lower().strip()

        # Remove common prefixes/suffixes
        for prefix in ["paid to", "payment to", "via", "from", "at", "by"]:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()

        # Replace multiple spaces with single
        while "  " in text:
            text = text.replace("  ", " ")

        # Remove punctuation for better matching
        text = "".join(c for c in text if c.isalnum() or c.isspace())

        return text if text else None

    def _analyze_pattern(
        self,
        description: str,
        occurrences: list[_RawOccurrence],
    ) -> Optional[RecurringPattern]:
        """Analyze a group of occurrences to detect a recurring pattern."""
        if len(occurrences) < 3:
            return None

        # Sort by date
        occurrences.sort(key=lambda o: o.date)

        # Calculate intervals between occurrences
        intervals: list[int] = []
        for i in range(1, len(occurrences)):
            delta = (occurrences[i].date - occurrences[i - 1].date).days
            if delta > 0:
                intervals.append(delta)

        if not intervals:
            return None

        # Calculate statistics
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_interval = math.sqrt(variance)

        # Coefficient of variation for interval regularity
        cv = std_interval / mean_interval if mean_interval > 0 else float('inf')

        # Calculate amount statistics
        amounts = [o.amount for o in occurrences]
        mean_amount = sum(amounts) / len(amounts)
        variance_amount = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
        std_amount = math.sqrt(variance_amount)

        # Determine pattern type
        pattern_type = self._classify_pattern_type(description, mean_interval)

        # Calculate confidence
        # Factors: interval regularity (lower CV = higher confidence),
        # amount consistency, occurrence count
        interval_confidence = max(0, 1.0 - cv) if cv < 1.0 else 0.0
        amount_confidence = max(0, 1.0 - (std_amount / abs(mean_amount))) if mean_amount != 0 else 0.0
        count_confidence = min(1.0, len(occurrences) / 12.0)  # Max confidence at 12 occurrences

        confidence = (interval_confidence * 0.4 +
                      amount_confidence * 0.3 +
                      count_confidence * 0.3)

        # Determine tolerance (± days)
        tolerance = max(1, int(std_interval))

        return RecurringPattern(
            description=description,
            category_name=occurrences[0].category_name,
            frequency_days=round(mean_interval),
            interval_tolerance_days=tolerance,
            amount_mean=round(mean_amount, 2),
            amount_std=round(std_amount, 2),
            occurrence_count=len(occurrences),
            first_seen=occurrences[0].date,
            last_seen=occurrences[-1].date,
            pattern_type=pattern_type,
            confidence=round(confidence, 2),
        )

    def _classify_pattern_type(
        self,
        description: str,
        mean_interval_days: float,
    ) -> str:
        """Classify the pattern type based on description and interval."""
        desc_lower = description.lower()

        # Check for salary patterns
        if any(kw in desc_lower for kw in self._SALARY_KEYWORDS):
            return "salary"

        # Check for rent patterns
        if any(kw in desc_lower for kw in self._RENT_KEYWORDS):
            return "rent"

        # Check for subscription patterns
        if any(kw in desc_lower for kw in self._SUBSCRIPTION_KEYWORDS):
            return "subscription"

        # Check for utility patterns
        if any(kw in desc_lower for kw in self._UTILITY_KEYWORDS):
            return "utility"

        # Check for insurance patterns
        if any(kw in desc_lower for kw in self._INSURANCE_KEYWORDS):
            return "insurance"

        # Classify by interval
        if 25 <= mean_interval_days <= 35:
            return "salary"  # Monthly-ish
        elif 6 <= mean_interval_days <= 10:
            return "subscription"  # Weekly-ish
        elif 28 <= mean_interval_days <= 32:
            return "rent"  # Monthly
        elif 90 <= mean_interval_days <= 100:
            return "insurance"  # Quarterly
        elif 180 <= mean_interval_days <= 190:
            return "insurance"  # Semi-annual
        elif 360 <= mean_interval_days <= 370:
            return "insurance"  # Annual

        return "other"

    def get_next_occurrence(
        self,
        pattern: RecurringPattern,
        from_date: Optional[date] = None,
    ) -> date:
        """Predict the next occurrence of a pattern.

        Args:
            pattern: The recurring pattern.
            from_date: Start date for prediction. Defaults to today.

        Returns:
            Predicted next occurrence date.
        """
        if from_date is None:
            from_date = date.today()

        # Find the last occurrence
        last_seen = pattern.last_seen or from_date

        # Calculate how many intervals have passed
        days_since_last = (from_date - last_seen).days
        intervals_passed = days_since_last // pattern.frequency_days

        # Predict next occurrence
        next_occurrence = last_seen + timedelta(days=pattern.frequency_days * (intervals_passed + 1))

        return next_occurrence

    def get_expected_occurrences(
        self,
        pattern: RecurringPattern,
        start_date: date,
        end_date: date,
    ) -> list[tuple[date, float]]:
        """Get expected occurrences within a date range.

        Args:
            pattern: The recurring pattern.
            start_date: Start of range.
            end_date: End of range.

        Returns:
            List of (date, amount) tuples.
        """
        occurrences: list[tuple[date, float]] = []

        # Start from last_seen or earlier
        current = pattern.last_seen or start_date

        while current <= end_date:
            if current >= start_date:
                occurrences.append((current, pattern.amount_mean))
            current += timedelta(days=pattern.frequency_days)

        return occurrences
