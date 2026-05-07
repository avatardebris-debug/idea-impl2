"""Rule-based ticket classifier.

Assigns a ticket to one of ~10 categories using keyword matching and
category-specific rules from a YAML config file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from supportagent.models import Ticket, Urgency


@dataclass
class CategoryRule:
    name: str
    keywords: List[str]
    base_urgency: str
    priority_base: int


class Classifier:
    """Rule-based classifier that assigns a category and urgency to a Ticket."""

    def __init__(self, rules_path: Optional[str] = None):
        if rules_path is None:
            # Default path relative to this module
            rules_path = str(Path(__file__).resolve().parent.parent / "config" / "classification_rules.yaml")
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, path: str) -> List[CategoryRule]:
        with open(path, "r") as f:
            config = yaml.safe_load(f)

        rules: List[CategoryRule] = []
        for name, cfg in config.get("categories", {}).items():
            rules.append(CategoryRule(
                name=name,
                keywords=[k.lower() for k in cfg.get("keywords", [])],
                base_urgency=cfg.get("base_urgency", "low"),
                priority_base=cfg.get("priority_base", 1),
            ))
        return rules

    def classify(self, ticket: Ticket) -> Dict[str, Any]:
        """Classify a ticket and return category, urgency, priority_score."""
        text = (ticket.subject + " " + ticket.body).lower()
        metadata_text = " ".join(str(v) for v in ticket.metadata.values()).lower()
        combined_text = text + " " + metadata_text

        best_category = "general"
        best_score = 0
        best_urgency = "low"
        best_priority = 1

        for rule in self.rules:
            score = 0
            for kw in rule.keywords:
                # Count keyword occurrences (simple substring match)
                count = combined_text.count(kw)
                if count > 0:
                    score += count

            if score > best_score:
                best_score = score
                best_category = rule.name
                best_urgency = rule.base_urgency
                best_priority = rule.priority_base

        # Boost urgency if multiple high-urgency keywords match
        if best_score >= 3:
            if best_urgency == "low":
                best_urgency = "medium"
                best_priority = max(best_priority, 3)
            elif best_urgency == "medium":
                best_urgency = "high"
                best_priority = max(best_priority, 6)

        # Cap priority at 10
        best_priority = min(best_priority + best_score, 10)

        return {
            "category": best_category,
            "urgency": best_urgency,
            "priority_score": best_priority,
        }

    def classify_ticket(self, ticket: Ticket) -> Ticket:
        """Classify a ticket in-place and return the updated Ticket."""
        result = self.classify(ticket)
        ticket.category = result["category"]
        urgency_str = result["urgency"]
        # Guard against unknown urgency values from config
        try:
            ticket.urgency = Urgency(urgency_str)
        except ValueError:
            ticket.urgency = Urgency.LOW  # safe fallback
        ticket.priority_score = result["priority_score"]
        return ticket
