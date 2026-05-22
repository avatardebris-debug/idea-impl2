"""Rule engine for evaluating rules against email messages."""

import re
from typing import List
from email_tool.models import Email, Rule, RuleMatch, RuleType, RuleMatchStrategy, RuleMatchType


class RuleEngine:
    """Engine for evaluating rules against email messages."""

    def __init__(self, rules: List[Rule] = None, match_strategy: RuleMatchStrategy = RuleMatchStrategy.FIRST_MATCH):
        """
        Initialize the rule engine.

        Args:
            rules: List of rules to evaluate.
            match_strategy: Strategy for matching multiple rules (FIRST_MATCH, BEST_MATCH, or ALL_MATCH).
        """
        self.rules = rules or []
        self.match_strategy = match_strategy

    @staticmethod
    def _get_match_type(rule_type: RuleType) -> RuleMatchType:
        """Get the match type enum from rule type."""
        type_map = {
            RuleType.FROM_EXACT: RuleMatchType.EXACT,
            RuleType.FROM_PATTERN: RuleMatchType.REGEX,
            RuleType.SUBJECT_EXACT: RuleMatchType.EXACT,
            RuleType.SUBJECT_CONTAINS: RuleMatchType.CONTAINS,
            RuleType.SUBJECT_PATTERN: RuleMatchType.REGEX,
            RuleType.BODY_CONTAINS_EXACT: RuleMatchType.EXACT,
            RuleType.BODY_CONTAINS_CONTAINS: RuleMatchType.CONTAINS,
            RuleType.BODY_CONTAINS_PATTERN: RuleMatchType.REGEX,
            RuleType.HAS_ATTACHMENT: RuleMatchType.EXACT
        }
        return type_map.get(rule_type, RuleMatchType.EXACT)

    @staticmethod
    def evaluate_rule(rule: Rule, email: Email) -> List[RuleMatch]:
        """
        Evaluate a single rule against an email.

        Args:
            rule: The rule to evaluate.
            email: The email to evaluate against.

        Returns:
            List of RuleMatch objects (0 or 1).
        """
        matches: List[RuleMatch] = []
        match_type = rule.rule_type
        pattern = rule.pattern or ""

        if match_type == RuleType.FROM_EXACT:
            if email.from_addr.lower() == pattern.lower():
                matches.append(RuleMatch(
                    rule=rule,
                    match_type=RuleEngine._get_match_type(match_type),
                    matched_value=pattern,
                    confidence=1.0
                ))

        elif match_type == RuleType.FROM_PATTERN:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                if regex.search(email.from_addr):
                    matches.append(RuleMatch(
                        rule=rule,
                        match_type=RuleEngine._get_match_type(match_type),
                        matched_value=pattern,
                        confidence=1.0
                    ))
            except re.error:
                pass

        elif match_type == RuleType.SUBJECT_EXACT:
            if email.subject.lower() == pattern.lower():
                matches.append(RuleMatch(
                    rule=rule,
                    match_type=RuleEngine._get_match_type(match_type),
                    matched_value=pattern,
                    confidence=1.0
                ))

        elif match_type == RuleType.SUBJECT_CONTAINS:
            if pattern.lower() in email.subject.lower():
                matches.append(RuleMatch(
                    rule=rule,
                    match_type=RuleEngine._get_match_type(match_type),
                    matched_value=pattern,
                    confidence=1.0
                ))

        elif match_type == RuleType.SUBJECT_PATTERN:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                if regex.search(email.subject):
                    matches.append(RuleMatch(
                        rule=rule,
                        match_type=RuleEngine._get_match_type(match_type),
                        matched_value=pattern,
                        confidence=1.0
                    ))
            except re.error:
                pass

        elif match_type == RuleType.BODY_CONTAINS_EXACT:
            body_text = email.body_plain or ""
            # If plain body is empty, try HTML body
            if not body_text and email.body_html:
                body_text = email.body_html
            if pattern.lower() in body_text.lower():
                matches.append(RuleMatch(
                    rule=rule,
                    match_type=RuleEngine._get_match_type(match_type),
                    matched_value=pattern,
                    confidence=1.0
                ))

        elif match_type == RuleType.BODY_CONTAINS_CONTAINS:
            body_text = email.body_plain or ""
            # If plain body is empty, try HTML body
            if not body_text and email.body_html:
                body_text = email.body_html
            if pattern.lower() in body_text.lower():
                matches.append(RuleMatch(
                    rule=rule,
                    match_type=RuleEngine._get_match_type(match_type),
                    matched_value=pattern,
                    confidence=1.0
                ))

        elif match_type == RuleType.BODY_CONTAINS_PATTERN:
            try:
                regex = re.compile(pattern)  # No IGNORECASE - case sensitive
                body_text = email.body_plain or ""
                if regex.search(body_text):
                    matches.append(RuleMatch(
                        rule=rule,
                        match_type=RuleEngine._get_match_type(match_type),
                        matched_value=pattern,
                        confidence=1.0
                    ))
            except re.error:
                pass

        elif match_type == RuleType.HAS_ATTACHMENT:
            if email.attachments:
                matches.append(RuleMatch(
                    rule=rule,
                    match_type=RuleEngine._get_match_type(match_type),
                    matched_value="attachment",
                    confidence=1.0
                ))

        return matches

    def evaluate(self, email: Email) -> List[RuleMatch]:
        """
        Evaluate all rules against an email.

        Args:
            email: The email to evaluate.

        Returns:
            List of RuleMatch objects based on the match strategy.
        """
        all_matches: List[RuleMatch] = []

        for rule in self.rules:
            matches = self.evaluate_rule(rule, email)
            all_matches.extend(matches)

        # Apply match strategy
        if self.match_strategy == RuleMatchStrategy.FIRST_MATCH:
            return all_matches[:1] if all_matches else []
        elif self.match_strategy == RuleMatchStrategy.BEST_MATCH:
            if all_matches:
                return [max(all_matches, key=lambda m: m.rule.priority)]
            return []
        elif self.match_strategy == RuleMatchStrategy.ALL_MATCH:
            # Sort by priority (highest first)
            return sorted(all_matches, key=lambda m: m.rule.priority, reverse=True)

        return all_matches
