"""Tests for condition operators."""

import pytest
from rule_engine.operators import evaluate_condition


class TestContainsOperator:
    def test_contains_match(self):
        assert evaluate_condition("Hello invoice world", "contains", "invoice") is True

    def test_contains_no_match(self):
        assert evaluate_condition("Hello world", "contains", "invoice") is False

    def test_contains_unicode(self):
        assert evaluate_condition("Привет мир", "contains", "Привет") is True

    def test_contains_empty_value(self):
        assert evaluate_condition("Hello", "contains", "") is True


class TestNotContainsOperator:
    def test_not_contains_match(self):
        assert evaluate_condition("Hello world", "not_contains", "invoice") is True

    def test_not_contains_no_match(self):
        assert evaluate_condition("Hello invoice", "not_contains", "invoice") is False


class TestEqualsOperator:
    def test_equals_match(self):
        assert evaluate_condition("invoice", "equals", "invoice") is True

    def test_equals_no_match(self):
        assert evaluate_condition("Invoice", "equals", "invoice") is False

    def test_equals_unicode(self):
        assert evaluate_condition("日本語", "equals", "日本語") is True


class TestRegexOperator:
    def test_regex_match(self):
        assert evaluate_condition("invoice-123", "regex", r"\d+") is True

    def test_regex_no_match(self):
        assert evaluate_condition("invoice", "regex", r"\d+") is False

    def test_regex_unicode(self):
        assert evaluate_condition("こんにちは世界", "regex", r"世界") is True


class TestIsEmptyOperator:
    def test_is_empty_none(self):
        assert evaluate_condition(None, "is_empty", None) is True

    def test_is_empty_empty_string(self):
        assert evaluate_condition("", "is_empty", None) is True

    def test_is_empty_whitespace_string(self):
        assert evaluate_condition("   ", "is_empty", None) is True

    def test_is_empty_false(self):
        assert evaluate_condition(False, "is_empty", None) is True

    def test_is_empty_non_empty(self):
        assert evaluate_condition("hello", "is_empty", None) is False

    def test_is_empty_zero(self):
        assert evaluate_condition(0, "is_empty", None) is False


class TestGtOperator:
    def test_gt_match(self):
        assert evaluate_condition(10, "gt", 5) is True

    def test_gt_no_match(self):
        assert evaluate_condition(3, "gt", 5) is False

    def test_gt_float(self):
        assert evaluate_condition(3.5, "gt", 2.1) is True

    def test_gt_string_coerce(self):
        assert evaluate_condition("10", "gt", "5") is True

    def test_gt_invalid(self):
        assert evaluate_condition("abc", "gt", "5") is False


class TestLtOperator:
    def test_lt_match(self):
        assert evaluate_condition(3, "lt", 5) is True

    def test_lt_no_match(self):
        assert evaluate_condition(10, "lt", 5) is False

    def test_lt_float(self):
        assert evaluate_condition(2.1, "lt", 3.5) is True

    def test_lt_string_coerce(self):
        assert evaluate_condition("3", "lt", "5") is True

    def test_lt_invalid(self):
        assert evaluate_condition("abc", "lt", "5") is False


class TestUnsupportedOperator:
    def test_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported operator"):
            evaluate_condition("hello", "invalid_op", "world")
