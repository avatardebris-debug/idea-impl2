"""Tests for Email Tool rules.

This module contains comprehensive tests for rule matching logic,
rule set management, and rule evaluation.
"""

import pytest
from datetime import datetime
from email_tool.rules import (
    RuleMatcher,
    RuleSet,
    RuleEvaluator,
    RuleMatch,
    RuleMatchType,
    RuleMatchStrategy,
    RuleType,
    Rule,
    Action,
    ActionType,
    Email,
    EmailMetadata
)


class TestRuleMatcher:
    """Tests for RuleMatcher class."""
    
    def test_match_from_exact(self):
        """Test matching FROM_EXACT rule."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 1
        assert matches[0].rule_name == "Test Rule"
        assert matches[0].matched_value == "test@example.com"
    
    def test_match_from_exact_no_match(self):
        """Test FROM_EXACT rule with no match."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com"
        )
        
        email = EmailMetadata(
            from_email="other@example.com",
            subject="Test Subject"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 0
    
    def test_match_from_pattern(self):
        """Test matching FROM_PATTERN rule."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_PATTERN,
            pattern=".*@example\\.com"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 1
        assert matches[0].matched_value == "test@example.com"
    
    def test_match_from_pattern_no_match(self):
        """Test FROM_PATTERN rule with no match."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_PATTERN,
            pattern=".*@example\\.com"
        )
        
        email = EmailMetadata(
            from_email="test@other.com",
            subject="Test Subject"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 0
    
    def test_match_subject_contains(self):
        """Test matching SUBJECT_CONTAINS rule."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject with test"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 1
        assert matches[0].matched_value == "test"
    
    def test_match_subject_contains_case_insensitive(self):
        """Test SUBJECT_CONTAINS rule is case insensitive."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="TEST SUBJECT"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 1
    
    def test_match_subject_pattern(self):
        """Test matching SUBJECT_PATTERN rule."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_PATTERN,
            pattern=".*test.*"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 1
    
    def test_match_body_contains(self):
        """Test matching BODY_CONTAINS rule."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.BODY_CONTAINS,
            pattern="test"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="This is a test body"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 1
    
    def test_match_body_pattern(self):
        """Test matching BODY_PATTERN rule."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.BODY_PATTERN,
            pattern=".*test.*"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="This is a test body"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 1
    
    def test_match_no_pattern_required(self):
        """Test rule without pattern requirement."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_EXACT
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = matcher.match(rule, email)
        
        # Should match because FROM_EXACT doesn't require pattern
        assert len(matches) == 1
    
    def test_match_with_labels(self):
        """Test matching rule with labels."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com",
            labels=["important", "work"]
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 1
        assert matches[0].labels == ["important", "work"]
    
    def test_match_with_description(self):
        """Test matching rule with description."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com",
            description="A test rule"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = matcher.match(rule, email)
        
        assert len(matches) == 1
        assert matches[0].description == "A test rule"


class TestRuleSet:
    """Tests for RuleSet class."""
    
    def test_rule_set_creation(self):
        """Test rule set creation."""
        rule_set = RuleSet(name="Test Rules")
        
        assert rule_set.name == "Test Rules"
        assert len(rule_set.rules) == 0
    
    def test_rule_set_add_rule(self):
        """Test adding rules to rule set."""
        rule_set = RuleSet(name="Test Rules")
        rule = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        
        rule_set.add_rule(rule)
        
        assert len(rule_set.rules) == 1
        assert rule_set.rules[0].name == "Rule 1"
    
    def test_rule_set_remove_rule(self):
        """Test removing rules from rule set."""
        rule_set = RuleSet(name="Test Rules")
        rule1 = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        rule2 = Rule(name="Rule 2", rule_type=RuleType.SUBJECT_CONTAINS)
        
        rule_set.add_rule(rule1)
        rule_set.add_rule(rule2)
        
        result = rule_set.remove_rule("Rule 1")
        
        assert result is True
        assert len(rule_set.rules) == 1
        assert rule_set.rules[0].name == "Rule 2"
    
    def test_rule_set_remove_rule_not_found(self):
        """Test removing non-existent rule."""
        rule_set = RuleSet(name="Test Rules")
        rule = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        rule_set.add_rule(rule)
        
        result = rule_set.remove_rule("Non-existent")
        
        assert result is False
        assert len(rule_set.rules) == 1
    
    def test_rule_set_get_rule(self):
        """Test getting a rule by name."""
        rule_set = RuleSet(name="Test Rules")
        rule1 = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        rule2 = Rule(name="Rule 2", rule_type=RuleType.SUBJECT_CONTAINS)
        
        rule_set.add_rule(rule1)
        rule_set.add_rule(rule2)
        
        result = rule_set.get_rule("Rule 1")
        
        assert result is not None
        assert result.name == "Rule 1"
        
        result = rule_set.get_rule("Non-existent")
        
        assert result is None
    
    def test_rule_set_get_rule_by_type(self):
        """Test getting rules by type."""
        rule_set = RuleSet(name="Test Rules")
        rule1 = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        rule2 = Rule(name="Rule 2", rule_type=RuleType.SUBJECT_CONTAINS)
        rule3 = Rule(name="Rule 3", rule_type=RuleType.FROM_EXACT)
        
        rule_set.add_rule(rule1)
        rule_set.add_rule(rule2)
        rule_set.add_rule(rule3)
        
        from_rules = rule_set.get_rules_by_type(RuleType.FROM_EXACT)
        
        assert len(from_rules) == 2
        assert from_rules[0].name == "Rule 1"
        assert from_rules[1].name == "Rule 3"
    
    def test_rule_set_get_enabled_rules(self):
        """Test getting enabled rules."""
        rule_set = RuleSet(name="Test Rules")
        rule1 = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT, enabled=True)
        rule2 = Rule(name="Rule 2", rule_type=RuleType.SUBJECT_CONTAINS, enabled=False)
        rule3 = Rule(name="Rule 3", rule_type=RuleType.FROM_EXACT, enabled=True)
        
        rule_set.add_rule(rule1)
        rule_set.add_rule(rule2)
        rule_set.add_rule(rule3)
        
        enabled_rules = rule_set.get_enabled_rules()
        
        assert len(enabled_rules) == 2
        assert enabled_rules[0].name == "Rule 1"
        assert enabled_rules[1].name == "Rule 3"
    
    def test_rule_set_get_rules_by_category(self):
        """Test getting rules by category."""
        rule_set = RuleSet(name="Test Rules")
        rule1 = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT, category="work")
        rule2 = Rule(name="Rule 2", rule_type=RuleType.SUBJECT_CONTAINS, category="personal")
        rule3 = Rule(name="Rule 3", rule_type=RuleType.FROM_EXACT, category="work")
        
        rule_set.add_rule(rule1)
        rule_set.add_rule(rule2)
        rule_set.add_rule(rule3)
        
        work_rules = rule_set.get_rules_by_category("work")
        
        assert len(work_rules) == 2
        assert work_rules[0].name == "Rule 1"
        assert work_rules[1].name == "Rule 3"
    
    def test_rule_set_to_dict(self):
        """Test rule set serialization."""
        rule_set = RuleSet(name="Test Rules")
        rule = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        rule_set.add_rule(rule)
        
        result = rule_set.to_dict()
        
        assert result["name"] == "Test Rules"
        assert len(result["rules"]) == 1
        assert result["rules"][0]["name"] == "Rule 1"


class TestRuleEvaluator:
    """Tests for RuleEvaluator class."""
    
    def test_evaluate_single_rule(self):
        """Test evaluating a single rule."""
        evaluator = RuleEvaluator()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate(rule, email)
        
        assert len(matches) == 1
        assert matches[0].rule_name == "Test Rule"
    
    def test_evaluate_multiple_rules(self):
        """Test evaluating multiple rules."""
        evaluator = RuleEvaluator()
        
        rule1 = Rule(
            name="Rule 1",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com"
        )
        
        rule2 = Rule(
            name="Rule 2",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate([rule1, rule2], email)
        
        assert len(matches) == 2
        assert matches[0].rule_name == "Rule 1"
        assert matches[1].rule_name == "Rule 2"
    
    def test_evaluate_with_priority(self):
        """Test evaluating rules with priority."""
        evaluator = RuleEvaluator()
        
        rule1 = Rule(
            name="Rule 1",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com",
            priority=50
        )
        
        rule2 = Rule(
            name="Rule 2",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test",
            priority=75
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate([rule1, rule2], email)
        
        # Should be sorted by priority (descending)
        assert matches[0].rule_name == "Rule 2"
        assert matches[1].rule_name == "Rule 1"
    
    def test_evaluate_with_disabled_rules(self):
        """Test evaluating rules with disabled rules."""
        evaluator = RuleEvaluator()
        
        rule1 = Rule(
            name="Rule 1",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com",
            enabled=True
        )
        
        rule2 = Rule(
            name="Rule 2",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test",
            enabled=False
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate([rule1, rule2], email)
        
        assert len(matches) == 1
        assert matches[0].rule_name == "Rule 1"
    
    def test_evaluate_with_category_filter(self):
        """Test evaluating rules with category filter."""
        evaluator = RuleEvaluator()
        
        rule1 = Rule(
            name="Rule 1",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com",
            category="work"
        )
        
        rule2 = Rule(
            name="Rule 2",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test",
            category="personal"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate([rule1, rule2], email, category_filter="work")
        
        assert len(matches) == 1
        assert matches[0].rule_name == "Rule 1"
    
    def test_evaluate_no_matches(self):
        """Test evaluating rules with no matches."""
        evaluator = RuleEvaluator()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com"
        )
        
        email = EmailMetadata(
            from_email="other@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate([rule], email)
        
        assert len(matches) == 0
    
    def test_evaluate_with_labels(self):
        """Test evaluating rules with labels."""
        evaluator = RuleEvaluator()
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com",
            labels=["important", "work"]
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate([rule], email)
        
        assert len(matches) == 1
        assert matches[0].labels == ["important", "work"]


class TestRuleMatch:
    """Tests for RuleMatch class."""
    
    def test_rule_match_creation(self):
        """Test RuleMatch creation."""
        match = RuleMatch(
            rule_name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            matched_value="test@example.com"
        )
        
        assert match.rule_name == "Test Rule"
        assert match.rule_type == RuleType.FROM_EXACT
        assert match.matched_value == "test@example.com"
    
    def test_rule_match_with_labels(self):
        """Test RuleMatch with labels."""
        match = RuleMatch(
            rule_name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            matched_value="test@example.com",
            labels=["important", "work"]
        )
        
        assert match.labels == ["important", "work"]
    
    def test_rule_match_with_description(self):
        """Test RuleMatch with description."""
        match = RuleMatch(
            rule_name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            matched_value="test@example.com",
            description="A test rule"
        )
        
        assert match.description == "A test rule"
    
    def test_rule_match_to_dict(self):
        """Test RuleMatch serialization."""
        match = RuleMatch(
            rule_name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            matched_value="test@example.com",
            labels=["important"],
            description="A test rule"
        )
        
        result = match.to_dict()
        
        assert result["rule_name"] == "Test Rule"
        assert result["rule_type"] == "from_exact"
        assert result["matched_value"] == "test@example.com"
        assert result["labels"] == ["important"]
        assert result["description"] == "A test rule"


class TestRuleType:
    """Tests for RuleType enum."""
    
    def test_rule_type_values(self):
        """Test RuleType enum values."""
        assert RuleType.FROM_EXACT.value == "from_exact"
        assert RuleType.FROM_PATTERN.value == "from_pattern"
        assert RuleType.SUBJECT_CONTAINS.value == "subject_contains"
        assert RuleType.SUBJECT_PATTERN.value == "subject_pattern"
        assert RuleType.BODY_CONTAINS.value == "body_contains"
        assert RuleType.BODY_PATTERN.value == "body_pattern"
    
    def test_rule_type_from_string(self):
        """Test RuleType from string."""
        assert RuleType.from_string("from_exact") == RuleType.FROM_EXACT
        assert RuleType.from_string("from_pattern") == RuleType.FROM_PATTERN
        assert RuleType.from_string("subject_contains") == RuleType.SUBJECT_CONTAINS
        assert RuleType.from_string("subject_pattern") == RuleType.SUBJECT_PATTERN
        assert RuleType.from_string("body_contains") == RuleType.BODY_CONTAINS
        assert RuleType.from_string("body_pattern") == RuleType.BODY_PATTERN
    
    def test_rule_type_invalid_string(self):
        """Test RuleType from invalid string."""
        with pytest.raises(ValueError, match="Invalid rule type"):
            RuleType.from_string("invalid_type")


class TestAction:
    """Tests for Action class."""
    
    def test_action_creation(self):
        """Test Action creation."""
        action = Action(
            action_type=ActionType.CATEGORIZE,
            category="work"
        )
        
        assert action.action_type == ActionType.CATEGORIZE
        assert action.category == "work"
    
    def test_action_with_labels(self):
        """Test Action with labels."""
        action = Action(
            action_type=ActionType.CATEGORIZE,
            category="work",
            labels=["important"]
        )
        
        assert action.labels == ["important"]
    
    def test_action_to_dict(self):
        """Test Action serialization."""
        action = Action(
            action_type=ActionType.CATEGORIZE,
            category="work",
            labels=["important"]
        )
        
        result = action.to_dict()
        
        assert result["action_type"] == "categorize"
        assert result["category"] == "work"
        assert result["labels"] == ["important"]


class TestEmail:
    """Tests for Email class."""
    
    def test_email_creation(self):
        """Test Email creation."""
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        assert email.from_email == "test@example.com"
        assert email.subject == "Test Subject"
        assert email.body_text == "Test body"
    
    def test_email_with_metadata(self):
        """Test Email with metadata."""
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body",
            metadata=EmailMetadata(
                received_date=datetime.now(),
                message_id="<test@example.com>"
            )
        )
        
        assert email.metadata.received_date is not None
        assert email.metadata.message_id == "<test@example.com>"
    
    def test_email_to_dict(self):
        """Test Email serialization."""
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        result = email.to_dict()
        
        assert result["from_email"] == "test@example.com"
        assert result["subject"] == "Test Subject"
        assert result["body_text"] == "Test body"


class TestRuleMatchingScenarios:
    """Tests for various rule matching scenarios."""
    
    def test_email_matching_multiple_rules(self):
        """Test email matching multiple rules."""
        matcher = RuleMatcher()
        evaluator = RuleEvaluator()
        
        rules = [
            Rule(
                name="From Rule",
                rule_type=RuleType.FROM_EXACT,
                pattern="test@example.com"
            ),
            Rule(
                name="Subject Rule",
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern="test"
            ),
            Rule(
                name="Body Rule",
                rule_type=RuleType.BODY_CONTAINS,
                pattern="test"
            )
        ]
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        matches = evaluator.evaluate(rules, email)
        
        assert len(matches) == 3
        match_names = [m.rule_name for m in matches]
        assert "From Rule" in match_names
        assert "Subject Rule" in match_names
        assert "Body Rule" in match_names
    
    def test_email_matching_priority_order(self):
        """Test email matching with priority order."""
        matcher = RuleMatcher()
        evaluator = RuleEvaluator()
        
        rules = [
            Rule(
                name="Low Priority",
                rule_type=RuleType.FROM_EXACT,
                pattern="test@example.com",
                priority=25
            ),
            Rule(
                name="High Priority",
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern="test",
                priority=75
            )
        ]
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate(rules, email)
        
        assert matches[0].rule_name == "High Priority"
        assert matches[1].rule_name == "Low Priority"
    
    def test_email_matching_disabled_rules(self):
        """Test email matching with disabled rules."""
        matcher = RuleMatcher()
        evaluator = RuleEvaluator()
        
        rules = [
            Rule(
                name="Enabled Rule",
                rule_type=RuleType.FROM_EXACT,
                pattern="test@example.com",
                enabled=True
            ),
            Rule(
                name="Disabled Rule",
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern="test",
                enabled=False
            )
        ]
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate(rules, email)
        
        assert len(matches) == 1
        assert matches[0].rule_name == "Enabled Rule"
    
    def test_email_matching_category_filter(self):
        """Test email matching with category filter."""
        matcher = RuleMatcher()
        evaluator = RuleEvaluator()
        
        rules = [
            Rule(
                name="Work Rule",
                rule_type=RuleType.FROM_EXACT,
                pattern="test@example.com",
                category="work"
            ),
            Rule(
                name="Personal Rule",
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern="test",
                category="personal"
            )
        ]
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        # Filter by work category
        matches = evaluator.evaluate(rules, email, category_filter="work")
        
        assert len(matches) == 1
        assert matches[0].rule_name == "Work Rule"
    
    def test_email_matching_no_rules(self):
        """Test email matching with no rules."""
        matcher = RuleMatcher()
        evaluator = RuleEvaluator()
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate([], email)
        
        assert len(matches) == 0
    
    def test_email_matching_invalid_regex(self):
        """Test email matching with invalid regex pattern."""
        matcher = RuleMatcher()
        evaluator = RuleEvaluator()
        
        rule = Rule(
            name="Invalid Rule",
            rule_type=RuleType.FROM_PATTERN,
            pattern="[invalid(regex"
        )
        
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        # Should handle invalid regex gracefully
        matches = evaluator.evaluate([rule], email)
        
        assert len(matches) == 0


class TestRuleSetIntegration:
    """Integration tests for RuleSet class."""
    
    def test_rule_set_full_workflow(self):
        """Test complete rule set workflow."""
        rule_set = RuleSet(name="Test Rules")
        
        # Add rules
        rule1 = Rule(
            name="From Rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com",
            priority=50
        )
        rule2 = Rule(
            name="Subject Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test",
            priority=75
        )
        
        rule_set.add_rule(rule1)
        rule_set.add_rule(rule2)
        
        # Evaluate rules
        evaluator = RuleEvaluator()
        email = EmailMetadata(
            from_email="test@example.com",
            subject="Test Subject"
        )
        
        matches = evaluator.evaluate(rule_set.rules, email)
        
        assert len(matches) == 2
        assert matches[0].rule_name == "Subject Rule"
        assert matches[1].rule_name == "From Rule"
        
        # Remove rule
        rule_set.remove_rule("From Rule")
        
        matches = evaluator.evaluate(rule_set.rules, email)
        
        assert len(matches) == 1
        assert matches[0].rule_name == "Subject Rule"
    
    def test_rule_set_serialization_deserialization(self):
        """Test rule set serialization and deserialization."""
        rule_set = RuleSet(name="Test Rules")
        
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com",
            priority=50,
            category="work"
        )
        
        rule_set.add_rule(rule)
        
        # Serialize
        rule_set_dict = rule_set.to_dict()
        
        # Deserialize
        new_rule_set = RuleSet.from_dict(rule_set_dict)
        
        assert new_rule_set.name == "Test Rules"
        assert len(new_rule_set.rules) == 1
        assert new_rule_set.rules[0].name == "Test Rule"
        assert new_rule_set.rules[0].priority == 50
        assert new_rule_set.rules[0].category == "work"