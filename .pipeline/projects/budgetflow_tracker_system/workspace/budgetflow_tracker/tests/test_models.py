"""Tests for the models module."""

import unittest
from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import ValidationError

from src.models import (
    Account,
    Budget,
    Category,
    Transaction,
    TransactionRule,
    TransactionType,
)


class TestTransactionType(unittest.TestCase):
    """Test suite for TransactionType enum."""

    def test_debit_value(self):
        """Test DEBIT enum value."""
        self.assertEqual(TransactionType.DEBIT, "debit")

    def test_credit_value(self):
        """Test CREDIT enum value."""
        self.assertEqual(TransactionType.CREDIT, "credit")

    def test_debit_name(self):
        """Test DEBIT enum name."""
        self.assertEqual(TransactionType.DEBIT.name, "DEBIT")

    def test_credit_name(self):
        """Test CREDIT enum name."""
        self.assertEqual(TransactionType.CREDIT.name, "CREDIT")

    def test_enum_iteration(self):
        """Test that enum has expected members."""
        members = list(TransactionType)
        self.assertEqual(len(members), 2)
        self.assertIn(TransactionType.DEBIT, members)
        self.assertIn(TransactionType.CREDIT, members)


class TestCategory(unittest.TestCase):
    """Test suite for Category model."""

    def test_create_minimal_category(self):
        """Test creating a category with minimal fields."""
        cat = Category(name="Test Category")
        self.assertEqual(cat.name, "Test Category")
        self.assertIsNone(cat.id)
        self.assertEqual(cat.description, "")
        self.assertFalse(cat.is_income)
        self.assertTrue(cat.is_active)
        self.assertIsNone(cat.parent_id)

    def test_create_full_category(self):
        """Test creating a category with all fields."""
        cat = Category(
            id=1,
            name="Full Category",
            description="A full category",
            is_income=True,
            is_active=False,
            parent_id=2,
        )
        self.assertEqual(cat.id, 1)
        self.assertEqual(cat.name, "Full Category")
        self.assertEqual(cat.description, "A full category")
        self.assertTrue(cat.is_income)
        self.assertFalse(cat.is_active)
        self.assertEqual(cat.parent_id, 2)

    def test_name_stripped(self):
        """Test that name is stripped of whitespace."""
        cat = Category(name="  Test  ")
        self.assertEqual(cat.name, "Test")

    def test_name_empty_raises(self):
        """Test that empty name raises ValidationError."""
        with self.assertRaises(ValidationError):
            Category(name="")

    def test_name_too_long_raises(self):
        """Test that name too long raises ValidationError."""
        with self.assertRaises(ValidationError):
            Category(name="A" * 101)

    def test_description_stripped(self):
        """Test that description is stripped of whitespace."""
        cat = Category(name="Test", description="  Desc  ")
        self.assertEqual(cat.description, "Desc")

    def test_is_income_default(self):
        """Test that is_income defaults to False."""
        cat = Category(name="Test")
        self.assertFalse(cat.is_income)

    def test_is_active_default(self):
        """Test that is_active defaults to True."""
        cat = Category(name="Test")
        self.assertTrue(cat.is_active)

    def test_parent_id_none_by_default(self):
        """Test that parent_id is None by default."""
        cat = Category(name="Test")
        self.assertIsNone(cat.parent_id)

    def test_parent_id_set(self):
        """Test setting parent_id."""
        cat = Category(name="Test", parent_id=5)
        self.assertEqual(cat.parent_id, 5)

    def test_model_dump(self):
        """Test model dump."""
        cat = Category(id=1, name="Test", description="Desc")
        dumped = cat.model_dump()
        self.assertEqual(dumped["id"], 1)
        self.assertEqual(dumped["name"], "Test")
        self.assertEqual(dumped["description"], "Desc")
        self.assertFalse(dumped["is_income"])
        self.assertTrue(dumped["is_active"])
        self.assertIsNone(dumped["parent_id"])

    def test_model_dump_json(self):
        """Test model dump to JSON."""
        cat = Category(id=1, name="Test")
        json_str = cat.model_dump_json()
        self.assertIn('"id": 1', json_str)
        self.assertIn('"name": "Test"', json_str)


class TestAccount(unittest.TestCase):
    """Test suite for Account model."""

    def test_create_minimal_account(self):
        """Test creating an account with minimal fields."""
        acc = Account(name="Test Account")
        self.assertEqual(acc.name, "Test Account")
        self.assertIsNone(acc.id)
        self.assertEqual(acc.account_type, "checking")
        self.assertTrue(acc.is_active)

    def test_create_full_account(self):
        """Test creating an account with all fields."""
        acc = Account(
            id=1,
            name="Full Account",
            account_type="savings",
            is_active=False,
            balance=1000.0,
            currency="USD",
        )
        self.assertEqual(acc.id, 1)
        self.assertEqual(acc.name, "Full Account")
        self.assertEqual(acc.account_type, "savings")
        self.assertFalse(acc.is_active)
        self.assertEqual(acc.balance, 1000.0)
        self.assertEqual(acc.currency, "USD")

    def test_name_stripped(self):
        """Test that name is stripped of whitespace."""
        acc = Account(name="  Test  ")
        self.assertEqual(acc.name, "Test")

    def test_name_empty_raises(self):
        """Test that empty name raises ValidationError."""
        with self.assertRaises(ValidationError):
            Account(name="")

    def test_name_too_long_raises(self):
        """Test that name too long raises ValidationError."""
        with self.assertRaises(ValidationError):
            Account(name="A" * 101)

    def test_account_type_default(self):
        """Test that account_type defaults to 'checking'."""
        acc = Account(name="Test")
        self.assertEqual(acc.account_type, "checking")

    def test_account_type_valid_values(self):
        """Test valid account_type values."""
        for acc_type in ["checking", "savings", "credit", "investment", "cash", "other"]:
            acc = Account(name="Test", account_type=acc_type)
            self.assertEqual(acc.account_type, acc_type)

    def test_account_type_invalid_raises(self):
        """Test that invalid account_type raises ValidationError."""
        with self.assertRaises(ValidationError):
            Account(name="Test", account_type="invalid")

    def test_is_active_default(self):
        """Test that is_active defaults to True."""
        acc = Account(name="Test")
        self.assertTrue(acc.is_active)

    def test_balance_default(self):
        """Test that balance defaults to 0.0."""
        acc = Account(name="Test")
        self.assertEqual(acc.balance, 0.0)

    def test_currency_default(self):
        """Test that currency defaults to 'USD'."""
        acc = Account(name="Test")
        self.assertEqual(acc.currency, "USD")

    def test_model_dump(self):
        """Test model dump."""
        acc = Account(id=1, name="Test", balance=500.0)
        dumped = acc.model_dump()
        self.assertEqual(dumped["id"], 1)
        self.assertEqual(dumped["name"], "Test")
        self.assertEqual(dumped["balance"], 500.0)


class TestTransaction(unittest.TestCase):
    """Test suite for Transaction model."""

    def test_create_minimal_transaction(self):
        """Test creating a transaction with minimal fields."""
        txn = Transaction(
            date=date(2024, 1, 1),
            description="Test Transaction",
            amount=Decimal("100.00"),
            transaction_type=TransactionType.DEBIT,
            account_id=1,
        )
        self.assertEqual(txn.date, date(2024, 1, 1))
        self.assertEqual(txn.description, "Test Transaction")
        self.assertEqual(txn.amount, Decimal("100.00"))
        self.assertEqual(txn.transaction_type, TransactionType.DEBIT)
        self.assertEqual(txn.account_id, 1)
        self.assertIsNone(txn.id)
        self.assertIsNone(txn.category_id)
        self.assertIsNone(txn.category_name)
        self.assertIsNone(txn.notes)
        self.assertIsNone(txn.recurring_pattern)

    def test_create_full_transaction(self):
        """Test creating a transaction with all fields."""
        txn = Transaction(
            id=1,
            date=date(2024, 1, 1),
            description="Full Transaction",
            amount=Decimal("200.00"),
            transaction_type=TransactionType.CREDIT,
            account_id=1,
            category_id=2,
            category_name="Income",
            notes="Test notes",
            recurring_pattern="monthly",
        )
        self.assertEqual(txn.id, 1)
        self.assertEqual(txn.date, date(2024, 1, 1))
        self.assertEqual(txn.description, "Full Transaction")
        self.assertEqual(txn.amount, Decimal("200.00"))
        self.assertEqual(txn.transaction_type, TransactionType.CREDIT)
        self.assertEqual(txn.account_id, 1)
        self.assertEqual(txn.category_id, 2)
        self.assertEqual(txn.category_name, "Income")
        self.assertEqual(txn.notes, "Test notes")
        self.assertEqual(txn.recurring_pattern, "monthly")

    def test_date_required(self):
        """Test that date is required."""
        with self.assertRaises(ValidationError):
            Transaction(
                description="Test",
                amount=Decimal("100"),
                transaction_type=TransactionType.DEBIT,
                account_id=1,
            )

    def test_description_required(self):
        """Test that description is required."""
        with self.assertRaises(ValidationError):
            Transaction(
                date=date(2024, 1, 1),
                amount=Decimal("100"),
                transaction_type=TransactionType.DEBIT,
                account_id=1,
            )

    def test_amount_required(self):
        """Test that amount is required."""
        with self.assertRaises(ValidationError):
            Transaction(
                date=date(2024, 1, 1),
                description="Test",
                transaction_type=TransactionType.DEBIT,
                account_id=1,
            )

    def test_transaction_type_required(self):
        """Test that transaction_type is required."""
        with self.assertRaises(ValidationError):
            Transaction(
                date=date(2024, 1, 1),
                description="Test",
                amount=Decimal("100"),
                account_id=1,
            )

    def test_account_id_required(self):
        """Test that account_id is required."""
        with self.assertRaises(ValidationError):
            Transaction(
                date=date(2024, 1, 1),
                description="Test",
                amount=Decimal("100"),
                transaction_type=TransactionType.DEBIT,
            )

    def test_amount_decimal_conversion(self):
        """Test that amount is converted to Decimal."""
        txn = Transaction(
            date=date(2024, 1, 1),
            description="Test",
            amount=100,
            transaction_type=TransactionType.DEBIT,
            account_id=1,
        )
        self.assertEqual(txn.amount, Decimal("100"))

    def test_amount_float_conversion(self):
        """Test that float amount is converted to Decimal."""
        txn = Transaction(
            date=date(2024, 1, 1),
            description="Test",
            amount=100.50,
            transaction_type=TransactionType.DEBIT,
            account_id=1,
        )
        self.assertEqual(txn.amount, Decimal("100.50"))

    def test_description_stripped(self):
        """Test that description is stripped of whitespace."""
        txn = Transaction(
            date=date(2024, 1, 1),
            description="  Test  ",
            amount=Decimal("100"),
            transaction_type=TransactionType.DEBIT,
            account_id=1,
        )
        self.assertEqual(txn.description, "Test")

    def test_notes_stripped(self):
        """Test that notes is stripped of whitespace."""
        txn = Transaction(
            date=date(2024, 1, 1),
            description="Test",
            amount=Decimal("100"),
            transaction_type=TransactionType.DEBIT,
            account_id=1,
            notes="  Notes  ",
        )
        self.assertEqual(txn.notes, "Notes")

    def test_model_dump(self):
        """Test model dump."""
        txn = Transaction(
            id=1,
            date=date(2024, 1, 1),
            description="Test",
            amount=Decimal("100"),
            transaction_type=TransactionType.DEBIT,
            account_id=1,
        )
        dumped = txn.model_dump()
        self.assertEqual(dumped["id"], 1)
        self.assertEqual(dumped["date"], "2024-01-01")
        self.assertEqual(dumped["description"], "Test")
        self.assertEqual(dumped["amount"], "100.00")
        self.assertEqual(dumped["transaction_type"], "debit")
        self.assertEqual(dumped["account_id"], 1)

    def test_model_dump_json(self):
        """Test model dump to JSON."""
        txn = Transaction(
            date=date(2024, 1, 1),
            description="Test",
            amount=Decimal("100"),
            transaction_type=TransactionType.DEBIT,
            account_id=1,
        )
        json_str = txn.model_dump_json()
        self.assertIn('"date": "2024-01-01"', json_str)
        self.assertIn('"description": "Test"', json_str)


class TestBudget(unittest.TestCase):
    """Test suite for Budget model."""

    def test_create_minimal_budget(self):
        """Test creating a budget with minimal fields."""
        budget = Budget(
            category_name="Food",
            amount=Decimal("500.00"),
            period="monthly",
        )
        self.assertEqual(budget.category_name, "Food")
        self.assertEqual(budget.amount, Decimal("500.00"))
        self.assertEqual(budget.period, "monthly")
        self.assertFalse(budget.is_active)
        self.assertFalse(budget.rollover)
        self.assertIsNone(budget.id)
        self.assertIsNone(budget.category_id)
        self.assertIsNone(budget.start_date)

    def test_create_full_budget(self):
        """Test creating a budget with all fields."""
        budget = Budget(
            id=1,
            category_id=2,
            category_name="Food",
            amount=Decimal("1000.00"),
            period="monthly",
            is_active=True,
            rollover=True,
            start_date=date(2024, 1, 1),
        )
        self.assertEqual(budget.id, 1)
        self.assertEqual(budget.category_id, 2)
        self.assertEqual(budget.category_name, "Food")
        self.assertEqual(budget.amount, Decimal("1000.00"))
        self.assertEqual(budget.period, "monthly")
        self.assertTrue(budget.is_active)
        self.assertTrue(budget.rollover)
        self.assertEqual(budget.start_date, date(2024, 1, 1))

    def test_category_name_required(self):
        """Test that category_name is required."""
        with self.assertRaises(ValidationError):
            Budget(amount=Decimal("500"), period="monthly")

    def test_amount_required(self):
        """Test that amount is required."""
        with self.assertRaises(ValidationError):
            Budget(category_name="Food", period="monthly")

    def test_period_required(self):
        """Test that period is required."""
        with self.assertRaises(ValidationError):
            Budget(category_name="Food", amount=Decimal("500"))

    def test_amount_decimal_conversion(self):
        """Test that amount is converted to Decimal."""
        budget = Budget(
            category_name="Food",
            amount=500,
            period="monthly",
        )
        self.assertEqual(budget.amount, Decimal("500"))

    def test_amount_float_conversion(self):
        """Test that float amount is converted to Decimal."""
        budget = Budget(
            category_name="Food",
            amount=500.50,
            period="monthly",
        )
        self.assertEqual(budget.amount, Decimal("500.50"))

    def test_period_default(self):
        """Test that period defaults to 'monthly'."""
        budget = Budget(category_name="Food", amount=Decimal("500"))
        self.assertEqual(budget.period, "monthly")

    def test_period_valid_values(self):
        """Test valid period values."""
        for period in ["monthly", "weekly"]:
            budget = Budget(category_name="Food", amount=Decimal("500"), period=period)
            self.assertEqual(budget.period, period)

    def test_period_invalid_raises(self):
        """Test that invalid period raises ValidationError."""
        with self.assertRaises(ValidationError):
            Budget(category_name="Food", amount=Decimal("500"), period="yearly")

    def test_is_active_default(self):
        """Test that is_active defaults to False."""
        budget = Budget(category_name="Food", amount=Decimal("500"))
        self.assertFalse(budget.is_active)

    def test_rollover_default(self):
        """Test that rollover defaults to False."""
        budget = Budget(category_name="Food", amount=Decimal("500"))
        self.assertFalse(budget.rollover)

    def test_category_id_none_by_default(self):
        """Test that category_id is None by default."""
        budget = Budget(category_name="Food", amount=Decimal("500"))
        self.assertIsNone(budget.category_id)

    def test_start_date_none_by_default(self):
        """Test that start_date is None by default."""
        budget = Budget(category_name="Food", amount=Decimal("500"))
        self.assertIsNone(budget.start_date)

    def test_model_dump(self):
        """Test model dump."""
        budget = Budget(
            id=1,
            category_id=2,
            category_name="Food",
            amount=Decimal("500"),
            period="monthly",
        )
        dumped = budget.model_dump()
        self.assertEqual(dumped["id"], 1)
        self.assertEqual(dumped["category_id"], 2)
        self.assertEqual(dumped["category_name"], "Food")
        self.assertEqual(dumped["amount"], "500.00")
        self.assertEqual(dumped["period"], "monthly")

    def test_model_dump_json(self):
        """Test model dump to JSON."""
        budget = Budget(category_name="Food", amount=Decimal("500"))
        json_str = budget.model_dump_json()
        self.assertIn('"category_name": "Food"', json_str)
        self.assertIn('"amount": "500.00"', json_str)


class TestTransactionRule(unittest.TestCase):
    """Test suite for TransactionRule model."""

    def test_create_minimal_rule(self):
        """Test creating a rule with minimal fields."""
        rule = TransactionRule(
            name="Test Rule",
            pattern="test",
            pattern_type="contains",
            category_name="Food",
        )
        self.assertEqual(rule.name, "Test Rule")
        self.assertEqual(rule.pattern, "test")
        self.assertEqual(rule.pattern_type, "contains")
        self.assertEqual(rule.category_name, "Food")
        self.assertFalse(rule.is_active)
        self.assertEqual(rule.priority, 10)
        self.assertEqual(rule.confidence, 0.9)
        self.assertIsNone(rule.id)
        self.assertIsNone(rule.category_id)

    def test_create_full_rule(self):
        """Test creating a rule with all fields."""
        rule = TransactionRule(
            id=1,
            category_id=2,
            name="Full Rule",
            pattern="full",
            pattern_type="regex",
            category_name="Income",
            is_active=True,
            priority=20,
            confidence=0.95,
        )
        self.assertEqual(rule.id, 1)
        self.assertEqual(rule.category_id, 2)
        self.assertEqual(rule.name, "Full Rule")
        self.assertEqual(rule.pattern, "full")
        self.assertEqual(rule.pattern_type, "regex")
        self.assertEqual(rule.category_name, "Income")
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.priority, 20)
        self.assertEqual(rule.confidence, 0.95)

    def test_name_required(self):
        """Test that name is required."""
        with self.assertRaises(ValidationError):
            TransactionRule(pattern="test", pattern_type="contains", category_name="Food")

    def test_pattern_required(self):
        """Test that pattern is required."""
        with self.assertRaises(ValidationError):
            TransactionRule(name="Test", pattern_type="contains", category_name="Food")

    def test_pattern_type_required(self):
        """Test that pattern_type is required."""
        with self.assertRaises(ValidationError):
            TransactionRule(name="Test", pattern="test", category_name="Food")

    def test_category_name_required(self):
        """Test that category_name is required."""
        with self.assertRaises(ValidationError):
            TransactionRule(name="Test", pattern="test", pattern_type="contains")

    def test_name_stripped(self):
        """Test that name is stripped of whitespace."""
        rule = TransactionRule(
            name="  Test  ",
            pattern="test",
            pattern_type="contains",
            category_name="Food",
        )
        self.assertEqual(rule.name, "Test")

    def test_pattern_stripped(self):
        """Test that pattern is stripped of whitespace."""
        rule = TransactionRule(
            name="Test",
            pattern="  test  ",
            pattern_type="contains",
            category_name="Food",
        )
        self.assertEqual(rule.pattern, "test")

    def test_category_name_stripped(self):
        """Test that category_name is stripped of whitespace."""
        rule = TransactionRule(
            name="Test",
            pattern="test",
            pattern_type="contains",
            category_name="  Food  ",
        )
        self.assertEqual(rule.category_name, "Food")

    def test_is_active_default(self):
        """Test that is_active defaults to False."""
        rule = TransactionRule(
            name="Test",
            pattern="test",
            pattern_type="contains",
            category_name="Food",
        )
        self.assertFalse(rule.is_active)

    def test_priority_default(self):
        """Test that priority defaults to 10."""
        rule = TransactionRule(
            name="Test",
            pattern="test",
            pattern_type="contains",
            category_name="Food",
        )
        self.assertEqual(rule.priority, 10)

    def test_confidence_default(self):
        """Test that confidence defaults to 0.9."""
        rule = TransactionRule(
            name="Test",
            pattern="test",
            pattern_type="contains",
            category_name="Food",
        )
        self.assertEqual(rule.confidence, 0.9)

    def test_category_id_none_by_default(self):
        """Test that category_id is None by default."""
        rule = TransactionRule(
            name="Test",
            pattern="test",
            pattern_type="contains",
            category_name="Food",
        )
        self.assertIsNone(rule.category_id)

    def test_model_dump(self):
        """Test model dump."""
        rule = TransactionRule(
            id=1,
            category_id=2,
            name="Test",
            pattern="test",
            pattern_type="contains",
            category_name="Food",
        )
        dumped = rule.model_dump()
        self.assertEqual(dumped["id"], 1)
        self.assertEqual(dumped["category_id"], 2)
        self.assertEqual(dumped["name"], "Test")
        self.assertEqual(dumped["pattern"], "test")
        self.assertEqual(dumped["pattern_type"], "contains")
        self.assertEqual(dumped["category_name"], "Food")

    def test_model_dump_json(self):
        """Test model dump to JSON."""
        rule = TransactionRule(
            name="Test",
            pattern="test",
            pattern_type="contains",
            category_name="Food",
        )
        json_str = rule.model_dump_json()
        self.assertIn('"name": "Test"', json_str)
        self.assertIn('"pattern": "test"', json_str)


if __name__ == "__main__":
    unittest.main()
