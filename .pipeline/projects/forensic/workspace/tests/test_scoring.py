"""Tests for forensic scoring module."""

import pytest
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
            {"category": "text_pattern", "severity": "info", "evidence": "test"},
            {"category": "disclosure", "severity": "info", "evidence": "test"},
        ]
        score = compute_fraud_score(flags)
        assert score > 0
        assert score < 20

    def test_medium_severity_flags(self):
        """Test score with medium severity flags."""
        flags = [
            {"category": "text_pattern", "severity": "warning", "evidence": "test"},
            {"category": "financial_ratio", "severity": "warning", "evidence": "test"},
        ]
        score = compute_fraud_score(flags)
        assert score >= 20
        assert score < 50

    def test_high_severity_flags(self):
        """Test score with high severity flags."""
        flags = [
            {"category": "text_pattern", "severity": "critical", "evidence": "test"},
            {"category": "financial_ratio", "severity": "critical", "evidence": "test"},
        ]
        score = compute_fraud_score(flags)
        assert score >= 50
        assert score < 100

    def test_mixed_severity_flags(self):
        """Test score with mixed severity flags."""
        flags = [
            {"category": "text_pattern", "severity": "critical", "evidence": "test"},
            {"category": "disclosure", "severity": "warning", "evidence": "test"},
            {"category": "cash_flow", "severity": "info", "evidence": "test"},
        ]
        score = compute_fraud_score(flags)
        assert score > 0
        assert score < 100

    def test_many_flags(self):
        """Test score with many flags."""
        flags = [
            {"category": "text_pattern", "severity": "critical", "evidence": "test"}
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
        flags = [{"category": "text_pattern", "severity": "warning", "evidence": "test"}]
        score = compute_fraud_score(flags)
        assert score > 0
        assert score < 50

    def test_score_bounds(self):
        """Test that score is always between 0 and 100."""
        for severity in ["info", "warning", "critical"]:
            flags = [{"category": "text_pattern", "severity": severity, "evidence": "test"}]
            score = compute_fraud_score(flags)
            assert 0 <= score <= 100

    def test_different_categories(self):
        """Test that different categories contribute to score."""
        categories = ["text_pattern", "financial_ratio", "cash_flow", "disclosure"]
        for cat in categories:
            flags = [{"category": cat, "severity": "warning", "evidence": "test"}]
            score = compute_fraud_score(flags)
            assert score > 0


class TestGetRiskLevel:
    """Tests for get_risk_level function."""

    def test_low_risk(self):
        """Test low risk level for low scores."""
        assert get_risk_level(0) == "low"
        assert get_risk_level(10) == "low"
        assert get_risk_level(25) == "low"
        assert get_risk_level(30) == "low"

    def test_medium_risk(self):
        """Test medium risk level for medium scores."""
        assert get_risk_level(31) == "medium"
        assert get_risk_level(40) == "medium"
        assert get_risk_level(50) == "medium"
        assert get_risk_level(60) == "medium"
        assert get_risk_level(69) == "medium"

    def test_high_risk(self):
        """Test high risk level for high scores."""
        assert get_risk_level(70) == "high"
        assert get_risk_level(75) == "high"
        assert get_risk_level(85) == "high"

    def test_critical_risk(self):
        """Test critical risk level for critical scores."""
        assert get_risk_level(90) == "critical"
        assert get_risk_level(95) == "critical"
        assert get_risk_level(100) == "critical"

    def test_boundary_values(self):
        """Test boundary values for risk levels."""
        assert get_risk_level(30) == "low"
        assert get_risk_level(31) == "medium"
        assert get_risk_level(70) == "high"
        assert get_risk_level(90) == "critical"

    def test_negative_score(self):
        """Test that negative scores return low risk."""
        assert get_risk_level(-10) == "low"

    def test_score_above_100(self):
        """Test that scores above 100 return critical risk."""
        assert get_risk_level(110) == "critical"
        assert get_risk_level(200) == "critical"


class TestGenerateReport:
    """Tests for generate_report function."""

    def test_basic_report(self):
        """Test basic report generation."""
        flags = [
            {"category": "text_pattern", "severity": "warning", "evidence": "test"},
        ]
        report = generate_report(
            ticker="AAPL",
            cik="0000320193",
            accession_no="0000320193-23-000076",
            flags=flags,
        )
        assert report["ticker"] == "AAPL"
        assert report["cik"] == "0000320193"
        assert report["accession_no"] == "0000320193-23-000076"
        assert "recommendations" in report
        assert len(report["recommendations"]) > 0

    def test_report_with_no_flags(self):
        """Test report generation with no flags."""
        report = generate_report(
            ticker="MSFT",
            cik="0000789019",
            accession_no="0000789019-23-000045",
            flags=[],
        )
        assert report["ticker"] == "MSFT"
        assert "recommendations" in report
        assert len(report["recommendations"]) > 0

    def test_report_with_multiple_flags(self):
        """Test report generation with multiple flags."""
        flags = [
            {"category": "text_pattern", "severity": "critical", "evidence": "test1"},
            {"category": "financial_ratio", "severity": "warning", "evidence": "test2"},
            {"category": "cash_flow", "severity": "info", "evidence": "test3"},
        ]
        report = generate_report(
            ticker="TSLA",
            cik="0001318605",
            accession_no="0001318605-23-000089",
            flags=flags,
        )
        assert report["ticker"] == "TSLA"
        assert "recommendations" in report
        assert len(report["recommendations"]) > 0

    def test_report_recommendations_content(self):
        """Test that report recommendations have expected content."""
        flags = [
            {"category": "text_pattern", "severity": "critical", "evidence": "test"},
        ]
        report = generate_report(
            ticker="GOOGL",
            cik="0001652044",
            accession_no="0001652044-23-000012",
            flags=flags,
        )
        assert "recommendations" in report
        assert isinstance(report["recommendations"], list)
        assert len(report["recommendations"]) > 0
        # Check that recommendations contain expected keywords
        all_recs = " ".join(report["recommendations"])
        assert "fraud" in all_recs.lower() or "investigation" in all_recs.lower() or "review" in all_recs.lower()

    def test_report_with_different_tickers(self):
        """Test report generation with different tickers."""
        for ticker in ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]:
            report = generate_report(
                ticker=ticker,
                cik="0000320193",
                accession_no="0000320193-23-000076",
                flags=[],
            )
            assert report["ticker"] == ticker
