"""Unit tests for the rule engine."""

import pytest
from email_tool.models import Email, Rule, RuleType, RuleMatchType, RuleMatchStrategy, RuleMatch
from email_tool.rules import RuleEngine


class TestRuleEvaluation:
    """Tests for rule evaluation logic."""

    def test_from_exact_match(self):
        """Test FROM_EXACT rule matching."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="sender@example.com",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1
        assert matches[0].rule_name == "test_rule"
        assert matches[0].match_type == RuleMatchType.EXACT

    def test_from_exact_no_match(self):
        """Test FROM_EXACT rule with no match."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="sender@example.com",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="other@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 0

    def test_from_pattern_match(self):
        """Test FROM_PATTERN rule matching."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.FROM_PATTERN,
            pattern=r".*@example\.com",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_from_pattern_no_match(self):
        """Test FROM_PATTERN rule with no match."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.FROM_PATTERN,
            pattern=r".*@example\.com",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@other.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 0

    def test_subject_exact_match(self):
        """Test SUBJECT_EXACT rule matching."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.SUBJECT_EXACT,
            pattern="Important Update",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Important Update",
            body_plain="Body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_subject_exact_no_match(self):
        """Test SUBJECT_EXACT rule with no match."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.SUBJECT_EXACT,
            pattern="Important Update",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Different Subject",
            body_plain="Body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 0

    def test_subject_pattern_match(self):
        """Test SUBJECT_PATTERN rule matching."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.SUBJECT_PATTERN,
            pattern=r"Important.*Update",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Important Update",
            body_plain="Body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_subject_pattern_no_match(self):
        """Test SUBJECT_PATTERN rule with no match."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.SUBJECT_PATTERN,
            pattern=r"Important.*Update",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Different Subject",
            body_plain="Body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 0

    def test_body_contains_exact_match(self):
        """Test BODY_CONTAINS_EXACT rule matching."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.BODY_CONTAINS_EXACT,
            pattern="Important keyword",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="This contains Important keyword in the body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_body_contains_exact_no_match(self):
        """Test BODY_CONTAINS_EXACT rule with no match."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.BODY_CONTAINS_EXACT,
            pattern="Important keyword",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="This does not contain the keyword"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 0

    def test_body_contains_pattern_match(self):
        """Test BODY_CONTAINS_PATTERN rule matching."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.BODY_CONTAINS_PATTERN,
            pattern=r"Important\s+keyword",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="This contains Important keyword in the body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_body_contains_pattern_no_match(self):
        """Test BODY_CONTAINS_PATTERN rule with no match."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.BODY_CONTAINS_PATTERN,
            pattern=r"Important\s+keyword",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="This contains important keyword (lowercase)"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 0

    def test_has_attachment_match(self):
        """Test HAS_ATTACHMENT rule matching."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.HAS_ATTACHMENT,
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body",
            attachments=["document.pdf"]
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_has_attachment_no_match(self):
        """Test HAS_ATTACHMENT rule with no match."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.HAS_ATTACHMENT,
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body",
            attachments=[]
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 0


class TestRuleEngine:
    """Tests for RuleEngine class."""

    def test_engine_initialization(self):
        """Test RuleEngine initialization."""
        engine = RuleEngine()
        assert engine.rules == []
        assert engine.match_strategy == RuleMatchStrategy.FIRST_MATCH

    def test_engine_with_rules(self):
        """Test RuleEngine with rules."""
        rules = [
            Rule(
                id="test_rule_001",
            name="rule1",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=50,
                category="important"
            ),
            Rule(
                id="test_rule_001",
            name="rule2",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="Test",
                priority=30,
                category="test"
            )
        ]
        
        engine = RuleEngine(rules=rules)
        assert len(engine.rules) == 2

    def test_engine_evaluate_all_rules(self):
        """Test evaluating all rules against an email."""
        rules = [
            Rule(
                id="test_rule_001",
            name="rule1",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=50,
                category="important"
            ),
            Rule(
                id="test_rule_001",
            name="rule2",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="Test",
                priority=30,
                category="test"
            )
        ]
        
        engine = RuleEngine(rules=rules, match_strategy=RuleMatchStrategy.ALL_MATCH)
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = engine.evaluate(email)
        assert len(matches) == 2

    def test_engine_evaluate_no_matches(self):
        """Test evaluating rules with no matches."""
        rules = [
            Rule(
                id="test_rule_001",
            name="rule1",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=50,
                category="important"
            )
        ]
        
        engine = RuleEngine(rules=rules)
        email = Email(
            from_addr="other@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = engine.evaluate(email)
        assert len(matches) == 0

    def test_engine_first_match_strategy(self):
        """Test FIRST_MATCH strategy returns only first match."""
        rules = [
            Rule(
                id="test_rule_001",
            name="rule1",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=50,
                category="important"
            ),
            Rule(
                id="test_rule_001",
            name="rule2",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="Test",
                priority=30,
                category="test"
            )
        ]
        
        engine = RuleEngine(rules=rules, match_strategy=RuleMatchStrategy.FIRST_MATCH)
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = engine.evaluate(email)
        assert len(matches) == 1
        assert matches[0].rule_name == "rule1"

    def test_engine_best_match_strategy(self):
        """Test BEST_MATCH strategy returns highest priority match."""
        rules = [
            Rule(
                id="test_rule_001",
            name="rule1",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=30,
                category="important"
            ),
            Rule(
                id="test_rule_001",
            name="rule2",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="Test",
                priority=50,
                category="test"
            )
        ]
        
        engine = RuleEngine(rules=rules, match_strategy=RuleMatchStrategy.BEST_MATCH)
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = engine.evaluate(email)
        assert len(matches) == 1
        assert matches[0].rule_name == "rule2"

    def test_engine_all_match_strategy(self):
        """Test ALL_MATCH strategy returns all matches."""
        rules = [
            Rule(
                id="test_rule_001",
            name="rule1",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=50,
                category="important"
            ),
            Rule(
                id="test_rule_001",
            name="rule2",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="Test",
                priority=30,
                category="test"
            )
        ]
        
        engine = RuleEngine(rules=rules, match_strategy=RuleMatchStrategy.ALL_MATCH)
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = engine.evaluate(email)
        assert len(matches) == 2

    def test_engine_priority_ordering(self):
        """Test that matches are ordered by priority."""
        rules = [
            Rule(
                id="test_rule_001",
            name="rule1",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=30,
                category="important"
            ),
            Rule(
                id="test_rule_001",
            name="rule2",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="Test",
                priority=50,
                category="test"
            ),
            Rule(
                id="test_rule_001",
            name="rule3",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=70,
                category="urgent"
            )
        ]
        
        engine = RuleEngine(rules=rules, match_strategy=RuleMatchStrategy.ALL_MATCH)
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = engine.evaluate(email)
        assert len(matches) == 3
        # Should be ordered by priority (highest first)
        assert matches[0].priority == 70
        assert matches[1].priority == 50
        assert matches[2].priority == 30


class TestRuleMatchStrategy:
    """Tests for rule match strategies."""

    def test_first_match_returns_first(self):
        """Test FIRST_MATCH returns the first matching rule."""
        rules = [
            Rule(
                id="test_rule_001",
            name="rule1",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=30,
                category="important"
            ),
            Rule(
                id="test_rule_001",
            name="rule2",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="Test",
                priority=50,
                category="test"
            )
        ]
        
        engine = RuleEngine(rules=rules, match_strategy=RuleMatchStrategy.FIRST_MATCH)
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = engine.evaluate(email)
        assert len(matches) == 1
        assert matches[0].rule_name == "rule1"

    def test_best_match_returns_highest_priority(self):
        """Test BEST_MATCH returns the highest priority match."""
        rules = [
            Rule(
                id="test_rule_001",
            name="rule1",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=30,
                category="important"
            ),
            Rule(
                id="test_rule_001",
            name="rule2",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="Test",
                priority=50,
                category="test"
            )
        ]
        
        engine = RuleEngine(rules=rules, match_strategy=RuleMatchStrategy.BEST_MATCH)
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = engine.evaluate(email)
        assert len(matches) == 1
        assert matches[0].rule_name == "rule2"

    def test_all_match_returns_all(self):
        """Test ALL_MATCH returns all matching rules."""
        rules = [
            Rule(
                id="test_rule_001",
            name="rule1",
                rule_type=RuleType.FROM_EXACT,
                pattern="sender@example.com",
                priority=50,
                category="important"
            ),
            Rule(
                id="test_rule_001",
            name="rule2",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="Test",
                priority=30,
                category="test"
            )
        ]
        
        engine = RuleEngine(rules=rules, match_strategy=RuleMatchStrategy.ALL_MATCH)
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = engine.evaluate(email)
        assert len(matches) == 2


class TestRuleEvaluationEdgeCases:
    """Tests for edge cases in rule evaluation."""

    def test_empty_email(self):
        """Test rule evaluation with empty email."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="sender@example.com",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="",
            to_addrs=[],
            subject="",
            body_plain=""
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 0

    def test_rule_with_empty_pattern(self):
        """Test rule with empty pattern."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 0  # Empty pattern should not match

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="SENDER@EXAMPLE.COM",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_unicode_in_body(self):
        """Test rule matching with unicode in body."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.BODY_CONTAINS_EXACT,
            pattern="Hello 世界",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Hello 世界 and more"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_special_characters_in_pattern(self):
        """Test rule matching with special characters in pattern."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.BODY_CONTAINS_EXACT,
            pattern="Price: $100.00",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Price: $100.00 for this item"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_regex_special_characters(self):
        """Test regex special characters in pattern."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.BODY_CONTAINS_PATTERN,
            pattern=r"Price: \$100\.00",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Price: $100.00 for this item"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_multiline_body_matching(self):
        """Test rule matching with multiline body."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.BODY_CONTAINS_EXACT,
            pattern="Line 1\nLine 2",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Line 1\nLine 2\nLine 3"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1

    def test_html_body_matching(self):
        """Test rule matching with HTML body."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.BODY_CONTAINS_EXACT,
            pattern="Important text",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_html="<html><body><p>Important text</p></body></html>"
        )
        
        matches = RuleEngine.evaluate_rule(rule, email)
        assert len(matches) == 1


class TestRuleMatchObjects:
    """Tests for RuleMatch objects."""

    def test_rule_match_creation(self):
        """Test RuleMatch object creation."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="sender@example.com",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        match = RuleEngine.evaluate_rule(rule, email)[0]
        assert match.rule_name == "test_rule"
        assert match.rule_type == RuleType.FROM_EXACT
        assert match.match_type == RuleMatchType.EXACT
        assert match.priority == 50
        assert match.category == "important"

    def test_rule_match_with_pattern(self):
        """Test RuleMatch with pattern information."""
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.FROM_PATTERN,
            pattern=r".*@example\.com",
            priority=50,
            category="important"
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_plain="Body"
        )
        
        match = RuleEngine.evaluate_rule(rule, email)[0]
        assert match.rule_name == "test_rule"
        assert match.rule_type == RuleType.FROM_PATTERN
        assert match.match_type == RuleMatchType.REGEX
