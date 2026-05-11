"""RuleEngine — evaluates emails against rules and returns matching actions."""

from __future__ import annotations

import logging
from typing import Any

from rule_engine.models import Action, Condition, Rule
from rule_engine.operators import evaluate_condition

logger = logging.getLogger(__name__)


class RuleEngine:
    """Evaluates incoming emails against a set of rules and returns matching actions.

    Rules are sorted by priority (highest first) before evaluation.
    Disabled rules are skipped.
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        """Initialize the engine with an optional list of rules.

        Args:
            rules: A list of Rule objects. If None, the engine starts with
                   no rules (use add_rule or set_rules to populate).
        """
        self._rules: list[Rule] = list(rules) if rules else []

    @property
    def rules(self) -> list[Rule]:
        """Return a copy of the current rules list."""
        return list(self._rules)

    def add_rule(self, rule: Rule) -> None:
        """Add a single rule to the engine."""
        self._rules.append(rule)

    def set_rules(self, rules: list[Rule]) -> None:
        """Replace all rules with a new list."""
        self._rules = list(rules)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID. Returns True if found and removed."""
        for i, rule in enumerate(self._rules):
            if rule.id == rule_id:
                self._rules.pop(i)
                return True
        return False

    def evaluate(self, email: dict[str, Any]) -> list[Action]:
        """Evaluate an email against all rules and return matching actions.

        Actions are sorted by rule priority (highest first). If multiple
        rules have the same priority, they are evaluated in the order they
        were added.

        Args:
            email: A dictionary representing an email with fields like
                   'subject', 'from', 'body', 'has_attachment', 'priority_header'.

        Returns:
            A list of Action objects from all matching rules, sorted by
            priority (highest first).
        """
        # Filter to enabled rules only
        enabled_rules = [r for r in self._rules if r.enabled]

        # Sort by priority descending (highest first)
        sorted_rules = sorted(enabled_rules, key=lambda r: r.priority, reverse=True)

        all_actions: list[Action] = []

        for rule in sorted_rules:
            if self._matches(rule, email):
                all_actions.extend(rule.actions)

        return all_actions

    def evaluate_batch(
        self, emails: list[dict[str, Any]]
    ) -> list[list[Action]]:
        """Evaluate multiple emails against all rules.

        Args:
            emails: A list of email dictionaries.

        Returns:
            A list of action lists, one per email, in the same order.
        """
        return [self.evaluate(email) for email in emails]

    def _matches(self, rule: Rule, email: dict[str, Any]) -> bool:
        """Check if all conditions in a rule match the email."""
        for condition in rule.conditions:
            field_value = self._get_email_field(email, condition.field)
            if not evaluate_condition(field_value, condition.operator, condition.value):
                return False
        return True

    @staticmethod
    def _get_email_field(email: dict[str, Any], field: str) -> Any:
        """Retrieve a field value from an email dict.

        Handles special fields like 'has_attachment' and 'priority_header'.
        """
        if field == "has_attachment":
            return email.get("has_attachment", False)
        if field == "priority_header":
            return email.get("priority_header")
        return email.get(field)
