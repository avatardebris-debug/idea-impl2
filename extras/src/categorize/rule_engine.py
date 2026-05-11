"""Rule-based categorization engine for BudgetFlow Tracker."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.core.database import Database

logger = logging.getLogger(__name__)


@dataclass
class CategorizationResult:
    """Result of categorizing a transaction."""
    category_name: str
    confidence: float
    matched_rule: Optional[str] = None
    matched_keywords: list[str] = field(default_factory=list)


class Categorizer:
    """Rule-based transaction categorizer."""

    def __init__(self, db: Database):
        self.db = db

    def categorize(self, description: str, amount: float) -> CategorizationResult:
        """Categorize a transaction based on description and amount.

        Args:
            description: Transaction description.
            amount: Transaction amount (positive for income, negative for expense).

        Returns:
            CategorizationResult with category and confidence.
        """
        rules = self.get_all_rules()
        description_lower = description.lower()

        best_match = CategorizationResult(
            category_name="Uncategorized",
            confidence=0.0,
        )

        for rule in rules:
            if not rule["is_active"]:
                continue

            keywords = [k.lower().strip() for k in rule["keywords"].split(",")]
            matched_keywords = [k for k in keywords if k in description_lower]

            if matched_keywords:
                # Calculate confidence based on keyword match ratio and rule confidence
                keyword_confidence = len(matched_keywords) / len(keywords)
                final_confidence = rule["confidence"] * keyword_confidence

                if final_confidence > best_match.confidence:
                    best_match = CategorizationResult(
                        category_name=rule["category_name"],
                        confidence=final_confidence,
                        matched_rule=rule["name"],
                        matched_keywords=matched_keywords,
                    )

        # If no match found, check if it's income or expense
        if best_match.confidence < 0.3:
            if amount > 0:
                best_match.category_name = "Other Income"
                best_match.confidence = 0.3
            else:
                best_match.category_name = "Uncategorized"
                best_match.confidence = 0.1

        logger.debug(
            "Categorized '%s' as '%s' (confidence: %.2f)",
            description,
            best_match.category_name,
            best_match.confidence,
        )

        return best_match

    def get_all_rules(self) -> list[dict]:
        """Get all categorization rules."""
        return self.db.fetchall(
            """SELECT id, name, keywords, category_name, priority, confidence, is_active
               FROM categorization_rules
               ORDER BY priority DESC, id ASC"""
        )

    def add_rule(
        self,
        name: str,
        keywords: list[str],
        category_name: str,
        priority: int = 5,
        confidence: float = 0.8,
    ) -> None:
        """Add a new categorization rule."""
        keywords_str = ", ".join(keywords)
        self.db.execute(
            """INSERT INTO categorization_rules
               (name, keywords, category_name, priority, confidence)
               VALUES (?, ?, ?, ?, ?)""",
            (name, keywords_str, category_name, priority, confidence),
        )
        logger.info("Added categorization rule: %s", name)

    def remove_rule(self, name: str) -> None:
        """Remove a categorization rule."""
        self.db.execute("DELETE FROM categorization_rules WHERE name = ?", (name,))
        logger.info("Removed categorization rule: %s", name)

    def update_rule(
        self,
        name: str,
        keywords: Optional[list[str]] = None,
        category_name: Optional[str] = None,
        priority: Optional[int] = None,
        confidence: Optional[float] = None,
    ) -> None:
        """Update an existing categorization rule."""
        updates = []
        params = []

        if keywords is not None:
            updates.append("keywords = ?")
            params.append(", ".join(keywords))
        if category_name is not None:
            updates.append("category_name = ?")
            params.append(category_name)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if confidence is not None:
            updates.append("confidence = ?")
            params.append(confidence)

        if updates:
            params.append(name)
            self.db.execute(
                f"UPDATE categorization_rules SET {', '.join(updates)} WHERE name = ?",
                tuple(params),
            )
            logger.info("Updated categorization rule: %s", name)
