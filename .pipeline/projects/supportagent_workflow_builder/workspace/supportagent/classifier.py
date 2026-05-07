"""Core ticket classifier using keyword-based rules."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from supportagent.models import Ticket, Urgency


class Classifier:
    """Keyword-based ticket classifier."""

    def __init__(self, rules: Optional[Dict] = None):
        """Initialize with classification rules.

        Args:
            rules: Dict mapping category -> {keywords: [...], base_urgency: str, priority_base: int}
                   If None, uses default rules.
        """
        if rules is None:
            rules = self._default_rules()
        self.rules = rules

    @staticmethod
    def _default_rules() -> Dict:
        """Return default classification rules."""
        return {
            "billing": {
                "keywords": ["bill", "billing", "invoice", "payment", "charge", "charged",
                              "credit card", "subscription", "renewal", "plan", "upgrade",
                              "downgrade", "price", "pricing", "cost", "fee", "receipt",
                              "refund", "overcharge"],
                "base_urgency": "medium",
                "priority_base": 4,
            },
            "technical": {
                "keywords": ["bug", "error", "crash", "not working", "broken", "issue",
                              "problem", "fix", "troubleshoot", "login", "password", "access",
                              "permission", "api", "integration", "connect", "connection",
                              "timeout", "slow", "performance", "load", "data", "sync",
                              "export", "import"],
                "base_urgency": "medium",
                "priority_base": 4,
            },
            "account": {
                "keywords": ["account", "profile", "settings", "delete account", "deactivate",
                              "activate", "verify", "verification", "two factor", "2fa", "mfa",
                              "username", "email change", "update email", "update profile"],
                "base_urgency": "low",
                "priority_base": 2,
            },
            "general": {
                "keywords": ["hello", "hi", "help", "question", "info", "information",
                              "general", "other", "misc"],
                "base_urgency": "low",
                "priority_base": 1,
            },
            "urgent": {
                "keywords": ["urgent", "emergency", "critical", "asap", "immediately",
                              "down", "outage", "downtime", "production", "data loss",
                              "security", "breach", "hack", "compromised"],
                "base_urgency": "high",
                "priority_base": 7,
            },
        }

    def classify(self, ticket: Ticket) -> Dict[str, any]:
        """Classify a ticket and return category + urgency + priority.

        Args:
            ticket: The ticket to classify.

        Returns:
            Dict with keys: category, urgency, priority_score
        """
        text = f"{ticket.subject} {ticket.body}".lower()
        scores: Dict[str, float] = {}

        for category, rule in self.rules.items():
            score = 0.0
            for keyword in rule["keywords"]:
                if keyword.lower() in text:
                    score += 1.0
            if score > 0:
                scores[category] = score

        if not scores:
            category = "general"
            urgency = Urgency.LOW
            priority_score = 1
        else:
            category = max(scores, key=scores.get)
            rule = self.rules[category]
            urgency = Urgency(rule["base_urgency"])
            priority_score = rule["priority_base"]

            # Boost priority for urgent keywords
            if "urgent" in self.rules and scores.get("urgent", 0) > 0:
                priority_score = max(priority_score, self.rules["urgent"]["priority_base"])

            # Boost for multiple matches
            if len(scores) > 1:
                priority_score += 1

        # Clamp priority
        priority_score = max(1, min(10, priority_score))

        return {
            "category": category,
            "urgency": urgency,
            "priority_score": priority_score,
        }

    def add_rule(self, category: str, keywords: List[str], base_urgency: str = "low", priority_base: int = 1) -> None:
        """Add or update a classification rule.

        Args:
            category: Category name.
            keywords: List of keywords for this category.
            base_urgency: Default urgency for this category.
            priority_base: Base priority score for this category.
        """
        self.rules[category] = {
            "keywords": keywords,
            "base_urgency": base_urgency,
            "priority_base": priority_base,
        }

    def remove_rule(self, category: str) -> None:
        """Remove a classification rule."""
        self.rules.pop(category, None)

    def get_rules(self) -> Dict:
        """Return current classification rules."""
        return self.rules
