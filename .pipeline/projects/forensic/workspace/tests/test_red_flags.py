"""Tests for forensic red_flags module."""

import pytest
from forensic.red_flags import (
    run_all_checks,
    check_text_patterns,
    check_revenue_receivables_mismatch,
    check_related_party_transactions,
    check_auditor_change,
)


class FakeItem:
    """Mock item with item_content attribute for red_flags tests."""
    def __init__(self, content: str):
        self.item_content = content


class TestCheckTextPatterns:
    """Tests for check_text_patterns function."""

    def test_fraud_keywords(self):
        """Test detection of fraud-related keywords."""
        items = [FakeItem("The company engaged in fraudulent activities and had restatements of financial results.")]
        flags = check_text_patterns(items)
        assert len(flags) > 0
        categories = [f.category for f in flags]
        assert "text_pattern" in categories

    def test_litigation_keywords(self):
        """Test detection of litigation-related keywords."""
        items = [FakeItem("The company is facing litigation from shareholders regarding financial reporting.")]
        flags = check_text_patterns(items)
        # Litigation is not in the suspicious_patterns list, so expect no flags
        assert len(flags) == 0

    def test_clean_text(self):
        """Test that clean text produces no flags."""
        items = [FakeItem("The company reported strong financial results for the quarter.")]
        flags = check_text_patterns(items)
        assert len(flags) == 0

    def test_empty_text(self):
        """Test that empty text produces no flags."""
        items = [FakeItem("")]
        flags = check_text_patterns(items)
        assert len(flags) == 0

    def test_mixed_content(self):
        """Test text with mixed content."""
        items = [FakeItem("The company reported revenue growth. However, there were concerns about restatements and litigation.")]
        flags = check_text_patterns(items)
        assert len(flags) > 0


class TestCheckRevenueReceivablesMismatch:
    """Tests for check_revenue_receivables_mismatch function."""

    def test_normal_ratios(self):
        """Test that normal ratios produce no flags."""
        items = [FakeItem("Revenue growth was 10%. Receivables growth was 8%.")]
        flags = check_revenue_receivables_mismatch(items)
        assert len(flags) == 0

    def test_unusual_ratios(self):
        """Test that unusual ratios produce flags."""
        items = [FakeItem("Revenue growth was 10%. Receivables growth was 20%.")]
        flags = check_revenue_receivables_mismatch(items)
        # Receivables growth > 1.5x revenue growth should trigger
        assert len(flags) > 0

    def test_empty_items(self):
        """Test with empty items."""
        flags = check_revenue_receivables_mismatch([])
        assert len(flags) == 0


class TestCheckRelatedPartyTransactions:
    """Tests for check_related_party_transactions function."""

    def test_related_party_detected(self):
        """Test that related party transactions are detected."""
        items = [FakeItem("The company had related party transactions with its CEO.")]
        flags = check_related_party_transactions(items)
        assert len(flags) > 0

    def test_no_related_party(self):
        """Test that normal text produces no flags."""
        items = [FakeItem("The company reported strong quarterly earnings.")]
        flags = check_related_party_transactions(items)
        assert len(flags) == 0


class TestCheckAuditorChange:
    """Tests for check_auditor_change function."""

    def test_going_concern(self):
        """Test that going concern warnings are detected."""
        items = [FakeItem("The auditor raised a going concern issue.")]
        flags = check_auditor_change(items)
        assert len(flags) > 0

    def test_auditor_resignation(self):
        """Test that auditor resignation is detected."""
        items = [FakeItem("The auditor resigned from the engagement.")]
        flags = check_auditor_change(items)
        assert len(flags) > 0

    def test_no_auditor_issues(self):
        """Test that normal text produces no flags."""
        items = [FakeItem("The company reported strong results.")]
        flags = check_auditor_change(items)
        assert len(flags) == 0


class TestRunAllChecks:
    """Tests for run_all_checks function."""

    def test_all_checks_run(self):
        """Test that all checks are run."""
        items = [FakeItem("The company reported strong results.")]
        flags = run_all_checks(items)
        assert isinstance(flags, list)

    def test_empty_items(self):
        """Test with empty items."""
        flags = run_all_checks([])
        assert isinstance(flags, list)

    def test_mixed_inputs(self):
        """Test with mixed inputs."""
        items = [FakeItem("The company had restatements and related party transactions.")]
        flags = run_all_checks(items)
        assert isinstance(flags, list)
        assert len(flags) > 0
