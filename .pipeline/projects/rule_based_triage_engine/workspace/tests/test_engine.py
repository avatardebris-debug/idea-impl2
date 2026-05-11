"""Tests for RuleEngine evaluation logic."""

import pytest
from rule_engine.models import Action, Condition, Rule
from rule_engine.engine import RuleEngine


class TestRuleEngineBasic:
    def test_no_rules_returns_empty(self):
        engine = RuleEngine()
        result = engine.evaluate({"subject": "hello"})
        assert result == []

    def test_single_rule_matches(self):
        rule = Rule(
            id="r1",
            name="Test Rule",
            conditions=[Condition(field="subject", operator="contains", value="invoice")],
            actions=[Action(type="tag", target="billing")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"subject": "Please pay this invoice"})
        assert len(result) == 1
        assert result[0].type == "tag"
        assert result[0].target == "billing"

    def test_single_rule_no_match(self):
        rule = Rule(
            id="r1",
            name="Test Rule",
            conditions=[Condition(field="subject", operator="contains", value="invoice")],
            actions=[Action(type="tag", target="billing")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"subject": "Hello world"})
        assert result == []


class TestPriorityOrdering:
    def test_higher_priority_first(self):
        rule_low = Rule(
            id="r_low",
            name="Low Priority",
            conditions=[Condition(field="subject", operator="contains", value="test")],
            actions=[Action(type="tag", target="low")],
            priority=1,
            enabled=True,
        )
        rule_high = Rule(
            id="r_high",
            name="High Priority",
            conditions=[Condition(field="subject", operator="contains", value="test")],
            actions=[Action(type="tag", target="high")],
            priority=10,
            enabled=True,
        )
        engine = RuleEngine([rule_low, rule_high])
        result = engine.evaluate({"subject": "test email"})
        assert len(result) == 2
        assert result[0].target == "high"
        assert result[1].target == "low"

    def test_disabled_rule_skipped(self):
        rule_disabled = Rule(
            id="r_disabled",
            name="Disabled",
            conditions=[Condition(field="subject", operator="contains", value="test")],
            actions=[Action(type="tag", target="disabled")],
            priority=100,
            enabled=False,
        )
        rule_enabled = Rule(
            id="r_enabled",
            name="Enabled",
            conditions=[Condition(field="subject", operator="contains", value="test")],
            actions=[Action(type="tag", target="enabled")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule_disabled, rule_enabled])
        result = engine.evaluate({"subject": "test email"})
        assert len(result) == 1
        assert result[0].target == "enabled"


class TestMultipleActions:
    def test_multiple_actions_per_rule(self):
        rule = Rule(
            id="r1",
            name="Multi Action",
            conditions=[Condition(field="subject", operator="contains", value="urgent")],
            actions=[
                Action(type="tag", target="urgent"),
                Action(type="flag", target="high"),
                Action(type="route", target="sales-pipeline"),
            ],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"subject": "urgent request"})
        assert len(result) == 3
        assert result[0].type == "tag"
        assert result[1].type == "flag"
        assert result[2].type == "route"


class TestEvaluateBatch:
    def test_batch_processing(self):
        rule = Rule(
            id="r1",
            name="Test",
            conditions=[Condition(field="subject", operator="contains", value="hello")],
            actions=[Action(type="tag", target="greeting")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        emails = [
            {"subject": "hello world"},
            {"subject": "goodbye world"},
            {"subject": "hello there"},
        ]
        results = engine.evaluate_batch(emails)
        assert len(results) == 3
        assert len(results[0]) == 1
        assert len(results[1]) == 0
        assert len(results[2]) == 1


class TestEdgeCases:
    def test_empty_body_handling(self):
        rule = Rule(
            id="r1",
            name="Empty Body",
            conditions=[Condition(field="body", operator="is_empty", value=None)],
            actions=[Action(type="tag", target="no-body")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"subject": "test", "body": ""})
        assert len(result) == 1

    def test_unicode_subject(self):
        rule = Rule(
            id="r1",
            name="Unicode",
            conditions=[Condition(field="subject", operator="contains", value="日本語")],
            actions=[Action(type="tag", target="japanese")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"subject": "こんにちは 日本語 世界"})
        assert len(result) == 1

    def test_no_match_graceful_noop(self):
        rule = Rule(
            id="r1",
            name="No Match",
            conditions=[Condition(field="subject", operator="equals", value="xyz")],
            actions=[Action(type="tag", target="xyz")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"subject": "hello"})
        assert result == []

    def test_from_field_matching(self):
        rule = Rule(
            id="r1",
            name="From Match",
            conditions=[Condition(field="from", operator="equals", value="boss@company.com")],
            actions=[Action(type="flag", target="important")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"from": "boss@company.com"})
        assert len(result) == 1

    def test_has_attachment_field(self):
        rule = Rule(
            id="r1",
            name="Attachment",
            conditions=[Condition(field="has_attachment", operator="equals", value=True)],
            actions=[Action(type="tag", target="has-attachment")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"has_attachment": True})
        assert len(result) == 1

    def test_gt_condition(self):
        rule = Rule(
            id="r1",
            name="GT",
            conditions=[Condition(field="priority_header", operator="gt", value=5)],
            actions=[Action(type="flag", target="high-priority")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"priority_header": 10})
        assert len(result) == 1

    def test_lt_condition(self):
        rule = Rule(
            id="r1",
            name="LT",
            conditions=[Condition(field="priority_header", operator="lt", value=5)],
            actions=[Action(type="tag", target="low-priority")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"priority_header": 3})
        assert len(result) == 1

    def test_not_contains_condition(self):
        rule = Rule(
            id="r1",
            name="Not Contains",
            conditions=[Condition(field="subject", operator="not_contains", value="spam")],
            actions=[Action(type="tag", target="clean")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"subject": "Hello world"})
        assert len(result) == 1

    def test_regex_condition(self):
        rule = Rule(
            id="r1",
            name="Regex",
            conditions=[Condition(field="subject", operator="regex", value=r"\d{3}-\d{4}")],
            actions=[Action(type="tag", target="phone")],
            priority=1,
            enabled=True,
        )
        engine = RuleEngine([rule])
        result = engine.evaluate({"subject": "Call 555-1234 now"})
        assert len(result) == 1
