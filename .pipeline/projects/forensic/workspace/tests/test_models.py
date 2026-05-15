"""Tests for forensic models."""

import json
import pytest
from forensic.models import (
    RedFlag,
    RedFlagSeverity,
    RiskLevel,
    IngestResult,
    AnalysisResult,
    FraudReport,
    Recommendation,
)


class TestRedFlagSeverity:
    """Tests for RedFlagSeverity enum."""

    def test_severity_values(self):
        """Test that severity enum has correct values."""
        assert RedFlagSeverity.CRITICAL.value == "critical"
        assert RedFlagSeverity.WARNING.value == "warning"
        assert RedFlagSeverity.INFO.value == "info"

    def test_severity_iteration(self):
        """Test that all severity levels are present."""
        severities = list(RedFlagSeverity)
        assert len(severities) == 4
        assert RedFlagSeverity.CRITICAL in severities
        assert RedFlagSeverity.HIGH in severities
        assert RedFlagSeverity.WARNING in severities
        assert RedFlagSeverity.INFO in severities


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_risk_level_values(self):
        """Test that risk level enum has correct values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_risk_level_iteration(self):
        """Test that all risk levels are present."""
        levels = list(RiskLevel)
        assert len(levels) == 4
        assert RiskLevel.LOW in levels
        assert RiskLevel.MEDIUM in levels
        assert RiskLevel.HIGH in levels
        assert RiskLevel.CRITICAL in levels


class TestRedFlag:
    """Tests for RedFlag model."""

    def test_creation(self):
        """Test creating a RedFlag with all fields."""
        flag = RedFlag(
            category="text_pattern",
            description="Suspicious language detected",
            severity=RedFlagSeverity.WARNING,
            evidence="Example evidence",
        )
        assert flag.category == "text_pattern"
        assert flag.description == "Suspicious language detected"
        assert flag.severity == RedFlagSeverity.WARNING
        assert flag.evidence == "Example evidence"

    def test_creation_with_string_severity(self):
        """Test creating a RedFlag with string severity."""
        flag = RedFlag(
            category="financial_ratio",
            description="Unusual ratio",
            severity="high",
            evidence="Evidence text",
        )
        assert flag.severity == RedFlagSeverity.HIGH

    def test_to_dict(self):
        """Test converting RedFlag to dictionary."""
        flag = RedFlag(
            category="disclosure",
            description="Missing disclosure",
            severity=RedFlagSeverity.INFO,
            evidence="Evidence",
        )
        d = flag.to_dict()
        assert d["category"] == "disclosure"
        assert d["description"] == "Missing disclosure"
        assert d["severity"] == "info"
        assert d["evidence"] == "Evidence"

    def test_from_dict(self):
        """Test creating RedFlag from dictionary."""
        data = {
            "category": "cash_flow",
            "description": "Cash flow anomaly",
            "severity": "warning",
            "evidence": "Cash flow evidence",
        }
        flag = RedFlag.from_dict(data)
        assert flag.category == "cash_flow"
        assert flag.description == "Cash flow anomaly"
        assert flag.severity == RedFlagSeverity.WARNING
        assert flag.evidence == "Cash flow evidence"

    def test_from_dict_with_string_severity(self):
        """Test creating RedFlag from dict with string severity."""
        data = {
            "category": "text_pattern",
            "description": "Test",
            "severity": "critical",
            "evidence": "Test evidence",
        }
        flag = RedFlag.from_dict(data)
        assert flag.severity == RedFlagSeverity.CRITICAL


class TestIngestResult:
    """Tests for IngestResult model."""

    def test_creation(self):
        """Test creating IngestResult."""
        result = IngestResult(
            ticker="AAPL",
            cik="0000320193",
            accession_no="0000320193-23-000076",
            filing_date="2023-11-03",
            filing_type="10-K",
            item_count=42,
        )
        assert result.ticker == "AAPL"
        assert result.cik == "0000320193"
        assert result.accession_no == "0000320193-23-000076"
        assert result.filing_date == "2023-11-03"
        assert result.filing_type == "10-K"
        assert result.item_count == 42

    def test_to_dict(self):
        """Test converting IngestResult to dictionary."""
        result = IngestResult(
            ticker="GOOGL",
            cik="0001652044",
            accession_no="0001652044-23-000012",
            filing_date="2023-12-01",
            filing_type="10-Q",
            item_count=20,
        )
        d = result.to_dict()
        assert d["ticker"] == "GOOGL"
        assert d["cik"] == "0001652044"
        assert d["accession_no"] == "0001652044-23-000012"
        assert d["filing_date"] == "2023-12-01"
        assert d["filing_type"] == "10-Q"
        assert d["item_count"] == 20

    def test_to_json(self, tmp_path):
        """Test serializing IngestResult to JSON file."""
        result = IngestResult(
            ticker="MSFT",
            cik="0000789019",
            accession_no="0000789019-23-000045",
            filing_date="2023-10-25",
            filing_type="10-K",
            item_count=35,
        )
        output_path = tmp_path / "ingest_result.json"
        result.to_json(str(output_path))
        with open(output_path) as f:
            data = json.load(f)
        assert data["ticker"] == "MSFT"
        assert data["item_count"] == 35


class TestAnalysisResult:
    """Tests for AnalysisResult model."""

    def test_creation(self):
        """Test creating AnalysisResult."""
        flags = [
            RedFlag(
                category="text_pattern",
                description="Suspicious language",
                severity=RedFlagSeverity.WARNING,
                evidence="Evidence 1",
            ),
            RedFlag(
                category="financial_ratio",
                description="Unusual ratio",
                severity=RedFlagSeverity.INFO,
                evidence="Evidence 2",
            ),
        ]
        result = AnalysisResult(
            ticker="TSLA",
            cik="0001318605",
            accession_no="0001318605-23-000089",
            fraud_risk_score=75.5,
            red_flags=flags,
        )
        assert result.ticker == "TSLA"
        assert result.fraud_risk_score == 75.5
        assert len(result.red_flags) == 2

    def test_to_dict(self):
        """Test converting AnalysisResult to dictionary."""
        flags = [
            RedFlag(
                category="disclosure",
                description="Missing disclosure",
                severity=RedFlagSeverity.INFO,
                evidence="Evidence",
            ),
        ]
        result = AnalysisResult(
            ticker="AMZN",
            cik="0001018724",
            accession_no="0001018724-23-000034",
            fraud_risk_score=45.0,
            red_flags=flags,
        )
        d = result.to_dict()
        assert d["ticker"] == "AMZN"
        assert d["fraud_risk_score"] == 45.0
        assert len(d["red_flags"]) == 1
        assert d["red_flags"][0]["category"] == "disclosure"

    def test_to_json(self, tmp_path):
        """Test serializing AnalysisResult to JSON file."""
        flags = [
            RedFlag(
                category="cash_flow",
                description="Cash flow issue",
                severity=RedFlagSeverity.WARNING,
                evidence="Evidence",
            ),
        ]
        result = AnalysisResult(
            ticker="META",
            cik="0001326801",
            accession_no="0001326801-23-000056",
            fraud_risk_score=60.0,
            red_flags=flags,
        )
        output_path = tmp_path / "analysis_result.json"
        result.to_json(str(output_path))
        with open(output_path) as f:
            data = json.load(f)
        assert data["ticker"] == "META"
        assert data["fraud_risk_score"] == 60.0


class TestFraudReport:
    """Tests for FraudReport model."""

    def test_creation(self):
        """Test creating FraudReport."""
        report = FraudReport(
            ticker="NVDA",
            cik="0001045810",
            filing_date="2023-11-03",
            risk_score=85.0,
            overall_risk=RiskLevel.CRITICAL,
            red_flags=[
                RedFlag(
                    category="text_pattern",
                    description="Critical fraud indicators",
                    severity=RedFlagSeverity.CRITICAL,
                    evidence="Critical evidence",
                ),
            ],
            recommendations=[
                Recommendation(
                    priority="high",
                    description="Immediate investigation required",
                    category="text_pattern",
                ),
            ],
        )
        assert report.ticker == "NVDA"
        assert report.risk_score == 85.0
        assert report.overall_risk == RiskLevel.CRITICAL
        assert len(report.red_flags) == 1
        assert len(report.recommendations) == 1
        assert report.recommendations[0].priority == "high"

    def test_to_dict(self):
        """Test converting FraudReport to dictionary."""
        report = FraudReport(
            ticker="JPM",
            cik="0000019617",
            filing_date="2023-11-03",
            risk_score=30.0,
            overall_risk=RiskLevel.LOW,
            red_flags=[],
            recommendations=[],
        )
        d = report.to_dict()
        assert d["ticker"] == "JPM"
        assert d["risk_score"] == 30.0
        assert d["overall_risk"] == "low"
        assert d["red_flags"] == []
        assert d["recommendations"] == []

    def test_to_json(self, tmp_path):
        """Test serializing FraudReport to JSON file."""
        report = FraudReport(
            ticker="BAC",
            cik="0000070858",
            filing_date="2023-11-03",
            risk_score=50.0,
            overall_risk=RiskLevel.MEDIUM,
            red_flags=[],
            recommendations=[],
        )
        output_path = tmp_path / "fraud_report.json"
        report.to_json(str(output_path))
        with open(output_path) as f:
            data = json.load(f)
        assert data["ticker"] == "BAC"
        assert data["risk_score"] == 50.0
        assert data["overall_risk"] == "medium"


class TestRecommendation:
    """Tests for Recommendation model."""

    def test_creation(self):
        """Test creating Recommendation."""
        rec = Recommendation(
            priority="high",
            description="Review revenue recognition",
            category="financial_ratio",
        )
        assert rec.priority == "high"
        assert rec.description == "Review revenue recognition"
        assert rec.category == "financial_ratio"

    def test_to_dict(self):
        """Test converting Recommendation to dictionary."""
        rec = Recommendation(
            priority="medium",
            description="Check disclosures",
            category="disclosure",
        )
        d = rec.to_dict()
        assert d["priority"] == "medium"
        assert d["description"] == "Check disclosures"
        assert d["category"] == "disclosure"
