"""Rule-based categorization engine for BudgetFlow Tracker."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

from src.core.database import Database

logger = logging.getLogger(__name__)


@dataclass
class CategorizationResult:
    """Result of categorizing a single transaction."""
    category_name: str
    category_id: Optional[int]
    confidence: float
    matched_rule_name: Optional[str] = None

    def __getitem__(self, key: str):
        """Support dict-style access for compatibility."""
        return getattr(self, key)


class Categorizer:
    """Deterministic rule-based categorization engine."""

    def __init__(self, db: Database):
        self.db = db

    def _load_rules(self) -> list[dict]:
        """Load all active rules from the database, ordered by priority descending."""
        rules = self.db.fetchall(
            """SELECT id, name, pattern, pattern_type, category_id, category_name, priority, confidence
               FROM transaction_rules
               WHERE is_active = 1
               ORDER BY priority DESC, id ASC"""
        )
        return [dict(r) for r in rules]

    def _match_rule(self, description: str, rule: dict) -> bool:
        """Check if a description matches a rule's pattern."""
        text = description.lower()
        pattern = rule["pattern"].lower()

        if rule["pattern_type"] == "exact":
            return text == pattern
        elif rule["pattern_type"] == "regex":
            try:
                return bool(re.search(pattern, text, re.IGNORECASE))
            except re.error:
                return False
        else:  # contains
            return pattern in text

    def categorize(self, description: str, amount: float = 0.0) -> CategorizationResult:
        """Categorize a single transaction description.

        Args:
            description: Transaction description/merchant name.
            amount: Transaction amount (positive = credit/income, negative = debit/expense).

        Returns:
            CategorizationResult with category info and confidence.
        """
        if not description or not description.strip():
            return CategorizationResult(
                category_name="Other",
                category_id=None,
                confidence=0.0,
            )

        rules = self._load_rules()

        # If amount is positive (income), prioritize income rules
        if amount > 0:
            income_rules = [r for r in rules if r["category_name"] == "Income"]
            non_income_rules = [r for r in rules if r["category_name"] != "Income"]
            # Try income rules first
            for rule in income_rules:
                if self._match_rule(description, rule):
                    return CategorizationResult(
                        category_name=rule["category_name"],
                        category_id=rule["category_id"],
                        confidence=rule["confidence"],
                        matched_rule_name=rule["name"],
                    )
            # Fall through to other rules
            rules = non_income_rules

        # Apply rules in priority order (first-match-wins)
        for rule in rules:
            if self._match_rule(description, rule):
                return CategorizationResult(
                    category_name=rule["category_name"],
                    category_id=rule["category_id"],
                    confidence=rule["confidence"],
                    matched_rule_name=rule["name"],
                )

        # No rule matched - default to Other
        return CategorizationResult(
            category_name="Other",
            category_id=None,
            confidence=0.0,
        )

    def bulk_categorize(self, transactions: list[tuple[str, float]]) -> list[CategorizationResult]:
        """Categorize multiple transactions.

        Args:
            transactions: List of (description, amount) tuples.

        Returns:
            List of CategorizationResult objects.
        """
        return [self.categorize(desc, amt) for desc, amt in transactions]

    def add_rule(
        self,
        name: str,
        keywords: list[str],
        category_name: str,
        priority: int = 5,
        confidence: float = 0.8,
        pattern_type: str = "contains",
    ) -> int:
        """Add a new categorization rule.

        Args:
            name: Rule name.
            keywords: List of keywords to match.
            category_name: Target category name.
            priority: Rule priority (higher = more important).
            confidence: Confidence score for this rule.
            pattern_type: Type of pattern matching ('contains', 'exact', 'regex').

        Returns:
            ID of the newly created rule.
        """
        # Combine keywords into a single pattern
        pattern = "|".join(keywords) if len(keywords) > 1 else keywords[0]
        if pattern_type == "regex":
            pattern = f"(?i)({pattern})"

        # Look up the category_id
        cat_row = self.db.fetchone(
            "SELECT id FROM categories WHERE name = ?", (category_name,)
        )
        if cat_row is None:
            raise ValueError(f"Category '{category_name}' not found")
        category_id = cat_row["id"]

        self.db.execute(
            """INSERT INTO transaction_rules
               (name, description, pattern, pattern_type, category_id, category_name, priority, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, f"Custom rule: {pattern}", pattern, pattern_type, category_id, category_name, priority, confidence),
        )
        rule_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
        logger.info("Added rule '%s' with ID %d", name, rule_id)
        return rule_id

    def remove_rule(self, rule_name: str) -> bool:
        """Deactivate a rule by name.

        Args:
            rule_name: Name of the rule to remove.

        Returns:
            True if a rule was deactivated, False otherwise.
        """
        result = self.db.execute(
            "UPDATE transaction_rules SET is_active = 0 WHERE name = ?",
            (rule_name,),
        )
        return result.rowcount > 0

    def get_all_rules(self) -> list[dict]:
        """Get all rules (active and inactive).

        Returns:
            List of rule dictionaries.
        """
        rules = self.db.fetchall(
            """SELECT id, name, pattern, pattern_type, category_id, category_name, priority, confidence, is_active
               FROM transaction_rules
               ORDER BY priority DESC, id ASC"""
        )
        result = []
        for r in rules:
            row = dict(r)
            # Convert pattern to keywords for consistency
            if row.get("pattern_type") == "regex":
                # Extract keywords from regex pattern
                row["keywords"] = [row["pattern"]]
            else:
                row["keywords"] = row["pattern"].split("|") if "|" in row["pattern"] else [row["pattern"]]
            result.append(row)
        return result

    def get_active_rules(self) -> list[dict]:
        """Get only active rules.

        Returns:
            List of active rule dictionaries.
        """
        rules = self.db.fetchall(
            """SELECT id, name, pattern, pattern_type, category_id, category_name, priority, confidence
               FROM transaction_rules
               WHERE is_active = 1
               ORDER BY priority DESC, id ASC"""
        )
        return [dict(r) for r in rules]
