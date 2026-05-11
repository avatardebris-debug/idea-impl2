"""Tests for the categorizer module."""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'budgetflow_tracker'))

from src.core.database import Database, reset_database
from src.categorize.rule_engine import Categorizer


@pytest.fixture
def db_path():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def categorizer(db_path):
    """Create a fresh categorizer with seeded database."""
    reset_database()
    db = Database(db_path)
    db.init_schema()
    db.seed_default_data()
    return Categorizer(db)


class TestCategorizerBasic:
    """Test basic categorization."""

    def test_categorize_grocery(self, categorizer):
        """Test categorizing a grocery transaction."""
        result = categorizer.categorize("Grocery Store", -50.0)
        assert result['category_name'] == 'Food & Drink'
        assert result['confidence'] > 0

    def test_categorize_starbucks(self, categorizer):
        """Test categorizing a Starbucks transaction."""
        result = categorizer.categorize("Starbucks Coffee", -5.0)
        assert result['category_name'] == 'Food & Drink'
        assert result['confidence'] > 0.9

    def test_categorize_uber(self, categorizer):
        """Test categorizing an Uber transaction."""
        result = categorizer.categorize("Uber Ride", -15.0)
        assert result['category_name'] == 'Transportation'
        assert result['confidence'] > 0.9

    def test_categorize_amazon(self, categorizer):
        """Test categorizing an Amazon transaction."""
        result = categorizer.categorize("Amazon Purchase", -30.0)
        assert result['category_name'] == 'Shopping'
        assert result['confidence'] > 0.9

    def test_categorize_netflix(self, categorizer):
        """Test categorizing a Netflix transaction."""
        result = categorizer.categorize("Netflix Subscription", -15.0)
        assert result['category_name'] == 'Bills & Utilities'
        assert result['confidence'] > 0.9

    def test_categorize_direct_deposit(self, categorizer):
        """Test categorizing income."""
        result = categorizer.categorize("Direct Deposit Payroll", 2000.0)
        assert result['category_name'] == 'Income'
        assert result['confidence'] > 0.9


class TestCategorizerEdgeCases:
    """Test edge cases in categorization."""

    def test_unknown_merchant(self, categorizer):
        """Test categorizing an unknown merchant."""
        result = categorizer.categorize("Unknown Merchant XYZ", -20.0)
        assert result['category_name'] == 'Other'
        assert result['confidence'] < 0.5

    def test_empty_merchant(self, categorizer):
        """Test categorizing with empty merchant."""
        result = categorizer.categorize("", -20.0)
        assert result['category_name'] == 'Other'

    def test_case_insensitive(self, categorizer):
        """Test that matching is case-insensitive."""
        result1 = categorizer.categorize("UBER RIDE", -15.0)
        result2 = categorizer.categorize("uber ride", -15.0)
        assert result1['category_name'] == result2['category_name']

    def test_partial_match(self, categorizer):
        """Test that partial matches work."""
        result = categorizer.categorize("Trader Joe's Market", -45.0)
        assert result['category_name'] == 'Food & Drink'


class TestCategorizerBulk:
    """Test bulk categorization."""

    def test_bulk_categorize(self, categorizer):
        """Test bulk categorization of multiple transactions."""
        transactions = [
            ("Grocery Store", -50.0),
            ("Uber Ride", -15.0),
            ("Netflix", -15.0),
            ("Amazon Purchase", -30.0),
        ]
        results = categorizer.bulk_categorize(transactions)
        assert len(results) == 4
        assert results[0]['category_name'] == 'Food & Drink'
        assert results[1]['category_name'] == 'Transportation'
        assert results[2]['category_name'] == 'Bills & Utilities'
        assert results[3]['category_name'] == 'Shopping'


class TestCategorizerRules:
    """Test rule management."""

    def test_add_rule(self, categorizer):
        """Test adding a custom rule."""
        categorizer.add_rule(
            name="Custom Rule",
            keywords=["custommerchant"],
            category_name="Shopping",
            priority=5,
            confidence=0.8
        )
        result = categorizer.categorize("CustomMerchant Store", -10.0)
        assert result['category_name'] == 'Shopping'

    def test_remove_rule(self, categorizer):
        """Test removing a rule."""
        # Add a rule
        categorizer.add_rule(
            name="Test Rule",
            keywords=["testmerchant"],
            category_name="Shopping",
            priority=5,
            confidence=0.8
        )
        # Remove it
        categorizer.remove_rule("Test Rule")
        result = categorizer.categorize("TestMerchant Store", -10.0)
        assert result['category_name'] != 'Shopping'

    def test_get_all_rules(self, categorizer):
        """Test getting all rules."""
        rules = categorizer.get_all_rules()
        assert len(rules) > 0
        assert 'name' in rules[0]
        assert 'keywords' in rules[0]
        assert 'category_name' in rules[0]
