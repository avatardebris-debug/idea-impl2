"""Tests for forensic scoring module."""

import pytest
from forensic.models import RedFlag, RedFlagSeverity, RiskLevel
from forensic.scoring import (
    compute_fraud_score,
    get_risk_level,
    generate_report,
)


class TestComputeFraudScore:
    """Tests for compute_fraud_score function."""

    def test_no_flags(self):
        """Test score with no red flags."""
        score = compute_fraud_score([])
        assert score == 0.0

    def test_low_severity_flags(self):
        """Test score with low severity flags."""
        flags = [
            RedFlag(category="text_pattern", severity=RedFlagSeverity.INFO, evidence="test"),
            RedFlag(category="disclosure", severity=RedFlagSeverity.INFO, evidence="test"),
        ]
        score = compute_fraud_score(flags)
        assert score > 0
        assert score < 20

    def test_medium_severity_flags(self):
        """Test score with medium severity flags."""
        flags = [
            RedFlag(category="text_pattern", severity=RedFlagSeverity.WARNING, evidence="test"),
            RedFlag(category="financial_ratio", severity=RedFlagSeverity.WARNING, evidence="test"),
        ]
        score = compute_fraud_score(flags)
        assert score >= 20
        assert score < 50

    def test_high_severity_flags(self):
        """Test score with high severity flags."""
        flags = [
            RedFlag(category="text_pattern", severity=RedFlagSeverity.CRITICAL, evidence="test"),
            RedFlag(category="financial_ratio", severity=RedFlagSeverity.CRITICAL, evidence="test"),
        ]
        score = compute_fraud_score(flags)
        assert score >= 50
        assert score < 100

    def test_mixed_severity_flags(self):
        """Test score with mixed severity flags."""
        flags = [
            RedFlag(category="text_pattern", severity=RedFlagSeverity.CRITICAL, evidence="test"),
            RedFlag(category="disclosure", severity=RedFlagSeverity.WARNING, evidence="test"),
            RedFlag(category="cash_flow", severity=RedFlagSeverity.INFO, evidence="test"),
        ]
        score = compute_fraud_score(flags)
        assert score > 0
        assert score < 100

    def test_many_flags(self):
        """Test score with many flags."""
        flags = [
            RedFlag(category="text_pattern", severity=RedFlagSeverity.CRITICAL, evidence="test")
            for _ in range(10)
        ]
        score = compute_fraud_score(flags)
        assert score >= 80

    def test_empty_list(self):
        """Test score with empty list."""
        score = compute_fraud_score([])
        assert score == 0.0

    def test_single_flag(self):
        """Test score with single flag."""
        flags = [RedFlag(category="text_pattern", severity=RedFlagSeverity.WARNING, evidence="test")]
        score = compute_fraud_score(flags)
        assert score > 0
        assert score < 50

    def test_score_bounds(self):
        """Test that score is always between 0 and 100."""
        for severity in [RedFlagSeverity.INFO, RedFlagSeverity.WARNING, RedFlagSeverity.CRITICAL]:
            flags = [RedFlag(category="text_pattern", severity=severity, evidence="test")]
            score = compute_fraud_score(flags)
            assert 0 <= score <= 100

    def test_different_categories(self):
        """Test that different categories contribute to score."""
        categories = ["text_pattern", "financial_ratio", "cash_flow", "disclosure"]
        for cat in categories:
            flags = [RedFlag(category=cat, severity=RedFlagSeverity.WARNING, evidence="test")]
            score = compute_fraud_score(flags)
            assert score > 0


class TestGetRiskLevel:
    """Tests for get_risk_level function."""

    def test_low_risk(self):
        """Test low risk level for low scores."""
        assert get_risk_level(0) == RiskLevel.LOW
        assert get_risk_level(10) == RiskLevel.LOW
        assert get_risk_level(25) == RiskLevel.LOW
        assert get_risk_level(30) == RiskLevel.LOW

    def test_medium_risk(self):
        """Test medium risk level for medium scores."""
        assert get_risk_level(31) == RiskLevel.MEDIUM
        assert get_risk_level(40) == RiskLevel.MEDIUM
        assert get_risk_level(50) == RiskLevel.MEDIUM
        assert get_risk_level(60) == RiskLevel.MEDIUM
        assert get_risk_level(69) == RiskLevel.MEDIUM

    def test_high_risk(self):
        """Test high risk level for high scores."""
        assert get_risk_level(70) == RiskLevel.HIGH
        assert get_risk_level(75) == RiskLevel.HIGH
        assert get_risk_level(85) == RiskLevel.HIGH

    def test_critical_risk(self):
        """Test critical risk level for critical scores."""
        assert get_risk_level(90) == RiskLevel.CRITICAL
        assert get_risk_level(95) == RiskLevel.CRITICAL
        assert get_risk_level(100) == RiskLevel.CRITICAL

    def test_boundary_values(self):
        """Test boundary values for risk levels."""
        assert get_risk_level(30) == RiskLevel.LOW
        assert get_risk_level(31) == RiskLevel.MEDIUM
        assert get_risk_level(70) == RiskLevel.HIGH
        assert get_risk_level(90) == RiskLevel.CRITICAL

    def test_negative_score(self):
        """Test that negative scores return low risk."""
        assert get_risk_level(-10) == RiskLevel.LOW

    def test_score_above_100(self):
        """Test that scores above 100 return critical risk."""
        assert get_risk_level(110) == RiskLevel.CRITICAL
        assert get_risk_level(200) == RiskLevel.CRITICAL


class TestGenerateReport:
    """Tests for generate_report function."""

    def test_basic_report(self):
        """Test basic report generation."""
        flags = [
            RedFlag(category="text_pattern", severity=RedFlagSeverity.WARNING, evidence="test"),
        ]
        report = generate_report(
            ticker="AAPL",
            cik="0000320193",
            accession_no="0000320193-23-000076",
            flags=flags,
        )
        assert report.ticker == "AAPL"
        assert report.cik == "0000320193"
        assert report.filing_date == "0000320193-23-000076"
        assert len(report.recommendations) > 0

    def test_report_with_no_flags(self):
        """Test report generation with no flags."""
        report = generate_report(
            ticker="MSFT",
            cik="0000789019",
            accession_no="0000789019-23-000045",
            flags=[],
        )
        assert report.ticker == "MSFT"
        assert len(report.recommendations) > 0

    def test_report_with_multiple_flags(self):
        """Test report generation with multiple flags."""
        flags = [
            RedFlag(category="text_pattern", severity=RedFlagSeverity.CRITICAL, evidence="test1"),
            RedFlag(category="financial_ratio", severity=RedFlagSeverity.WARNING, evidence="test2"),
            RedFlag(category="cash_flow", severity=RedFlagSeverity.INFO, evidence="test3"),
        ]
        report = generate_report(
            ticker="TSLA",
            cik="0001318605",
            accession_no="0001318605-23-000089",
            flags=flags,
        )
        assert report.ticker == "TSLA"
        assert len(report.recommendations) > 0

    def test_report_recommendations_content(self):
        """Test that report recommendations have expected content."""
        flags = [
            RedFlag(category="text_pattern", severity=RedFlagSeverity.CRITICAL, evidence="test"),
        ]
        report = generate_report(
            ticker="GOOGL",
            cik="0001652044",
            accession_no="0001652044-23-000012",
            flags=flags,
        )
        assert len(report.recommendations) > 0
        # Check that recommendations contain expected keywords
        all_recs = " ".join(rec.description.lower() for rec in report.recommendations)
        assert "fraud" in all_recs or "investigation" in all_recs or "review" in all_recs

    def test_report_with_different_tickers(self):
        """Test report generation with different tickers."""
        for ticker in ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]:
            report = generate_report(
                ticker=ticker,
                cik="0000320193",
                accession_no="0000320193-23-000076",
                flags=[],
            )
            assert report.ticker == ticker
