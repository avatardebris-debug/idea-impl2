"""Matcher module for rule matching against email messages."""

from typing import List
from email_tool.models import Email, Rule, RuleMatch, RuleType, RuleMatchStrategy
from email_tool.rules import RuleEngine


class RuleMatcher:
    """
    Matcher for evaluating rules against email messages.
    
    This class provides a high-level interface for matching emails against rules,
    delegating to the RuleEngine for actual rule evaluation.
    """
    
    def __init__(self, match_strategy: RuleMatchStrategy = RuleMatchStrategy.ALL_MATCH):
        """
        Initialize the rule matcher.
        
        Args:
            match_strategy: Strategy for matching multiple rules.
        """
        self.match_strategy = match_strategy
        self.rule_engine = RuleEngine(match_strategy=match_strategy)
    
    def match(self, email: Email, rules: List[Rule]) -> List[RuleMatch]:
        """
        Match an email against a list of rules.
        
        Args:
            email: The email to match.
            rules: List of rules to evaluate against the email.
        
        Returns:
            List of RuleMatch objects representing matched rules.
        """
        self.rule_engine.rules = rules
        return self.rule_engine.evaluate(email)
    
    def match_single(self, email: Email, rule: Rule) -> List[RuleMatch]:
        """
        Match an email against a single rule.
        
        Args:
            email: The email to match.
            rule: The rule to evaluate.
        
        Returns:
            List of RuleMatch objects (0 or 1).
        """
        return self.rule_engine.evaluate_rule(rule, email)
    
    def find_best_match(self, email: Email, rules: List[Rule]) -> RuleMatch:
        """
        Find the best matching rule for an email.
        
        Args:
            email: The email to match.
            rules: List of rules to evaluate.
        
        Returns:
            The best matching RuleMatch, or None if no match.
        """
        matches = self.match(email, rules)
        if matches:
            return max(matches, key=lambda m: m.priority)
        return None
    
    def find_first_match(self, email: Email, rules: List[Rule]) -> RuleMatch:
        """
        Find the first matching rule for an email.
        
        Args:
            email: The email to match.
            rules: List of rules to evaluate.
        
        Returns:
            The first matching RuleMatch, or None if no match.
        """
        matches = self.match(email, rules)
        if matches:
            return matches[0]
        return None
    
    def find_all_matches(self, email: Email, rules: List[Rule]) -> List[RuleMatch]:
        """
        Find all matching rules for an email.
        
        Args:
            email: The email to match.
            rules: List of rules to evaluate.
        
        Returns:
            List of all matching RuleMatch objects.
        """
        return self.match(email, rules)
    
    def set_match_strategy(self, strategy: RuleMatchStrategy):
        """
        Set the match strategy.
        
        Args:
            strategy: The match strategy to use.
        """
        self.match_strategy = strategy
        self.rule_engine.match_strategy = strategy


# Export the main class
__all__ = ['RuleMatcher']
