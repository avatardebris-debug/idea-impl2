"""Tests for analysis/risk module."""

import pytest
from osint_corp.analysis.risk import (
    RiskAnalyzer,
    RiskAssessment,
    RiskFactor,
)
from osint_corp.models.entities import Company, Filing


class TestRiskFactor:
    """Tests for RiskFactor."""

    def test_risk_factor_creation(self):
        """Test creating a RiskFactor."""
        factor = RiskFactor(
            name="Financial Risk",
            score=75,
            weight=0.3,
            description="High debt levels",
        )
        assert factor.name == "Financial Risk"
        assert factor.score == 75
        assert factor.weight == 0.3
        assert factor.severity == "High"

    def test_risk_factor_severity(self):
        """Test severity calculation."""
        low = RiskFactor(name="Low Risk", score=20)
        assert low.severity == "Low"

        medium = RiskFactor(name="Medium Risk", score=50)
        assert medium.severity == "Medium"

        high = RiskFactor(name="High Risk", score=80)
        assert high.severity == "High"

    def test_risk_factor_to_dict(self):
        """Test RiskFactor serialization."""
        factor = RiskFactor(
            name="Financial Risk",
            score=75,
            weight=0.3,
            description="High debt",
            recommendations=["Reduce debt"],
        )
        d = factor.to_dict()
        assert d["name"] == "Financial Risk"
        assert d["score"] == 75
        assert d["recommendations"][0] == "Reduce debt"

    def test_risk_factor_from_dict(self):
        """Test RiskFactor deserialization."""
        d = {
            "name": "Financial Risk",
            "score": 75,
            "weight": 0.3,
            "description": "High debt",
            "recommendations": ["Reduce debt"],
        }
        factor = RiskFactor.from_dict(d)
        assert factor.name == "Financial Risk"
        assert factor.score == 75


class TestRiskAssessment:
    """Tests for RiskAssessment."""

    def test_risk_assessment_creation(self):
        """Test creating a RiskAssessment."""
        assessment = RiskAssessment(
            overall_risk_score=65,
            risk_level="Medium",
            risk_factors=[
                RiskFactor(name="Financial Risk", score=75, weight=0.3),
            ],
            mitigations=["Monitor debt levels"],
        )
        assert assessment.overall_risk_score == 65
        assert assessment.risk_level == "Medium"
        assert len(assessment.risk_factors) == 1
        assert assessment.mitigations[0] == "Monitor debt levels"

    def test_risk_assessment_to_dict(self):
        """Test RiskAssessment serialization."""
        assessment = RiskAssessment(
            overall_risk_score=65,
            risk_level="Medium",
            risk_factors=[RiskFactor(name="Financial Risk", score=75)],
            mitigations=["Monitor debt"],
        )
        d = assessment.to_dict()
        assert d["overall_risk_score"] == 65
        assert d["risk_level"] == "Medium"
        assert d["risk_factors"][0]["name"] == "Financial Risk"

    def test_risk_assessment_from_dict(self):
        """Test RiskAssessment deserialization."""
        d = {
            "overall_risk_score": 65,
            "risk_level": "Medium",
            "risk_factors": [{"name": "Financial Risk", "score": 75}],
            "mitigations": ["Monitor debt"],
        }
        assessment = RiskAssessment.from_dict(d)
        assert assessment.overall_risk_score == 65
        assert assessment.risk_level == "Medium"


class TestRiskAnalyzer:
    """Tests for RiskAnalyzer."""

    def test_assess_risks_no_data(self):
        """Test risk assessment with no data."""
        analyzer = RiskAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")
        assessment = analyzer.assess_risks(company, [], [])
        assert assessment is not None
        # Should have some default risk factors
        assert len(assessment.risk_factors) > 0

    def test_assess_risks_with_financial_data(self):
        """Test risk assessment with financial data."""
        analyzer = RiskAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")

        filing = Filing(
            company_cik="0000000001",
            filing_type="10-K",
            filing_date="2024-01-15",
            content={
                "revenue": 1000000,
                "net_income": -50000,  # Loss
                "total_assets": 5000000,
                "total_equity": 100000,  # Low equity
                "total_debt": 4000000,  # High debt
                "current_assets": 200000,
                "current_liabilities": 300000,  # Current liabilities > current assets
                "inventory": 50000,
                "operating_income": -30000,
                "ebitda": -10000,
                "free_cash_flow": -40000,
                "eps": -2.0,
                "pe_ratio": None,
                "pb_ratio": 0.5,
            },
        )

        assessment = analyzer.assess_risks(company, [filing], [])
        assert assessment is not None
        assert assessment.overall_risk_score > 50  # Should be elevated due to losses and high debt

    def test_assess_risks_with_relationships(self):
        """Test risk assessment with relationship data."""
        analyzer = RiskAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")

        relationships = [
            {
                "source_name": "Test Corp",
                "target_name": "Related Party LLC",
                "relationship_type": "related_party",
                "strength": 0.9,
            },
        ]

        assessment = analyzer.assess_risks(company, [], relationships)
        assert assessment is not None
        # Should have related party risk factor
        related_party_risks = [
            f for f in assessment.risk_factors if "related party" in f.name.lower()
        ]
        assert len(related_party_risks) > 0

    def test_assess_risks_generates_mitigations(self):
        """Test that mitigations are generated."""
        analyzer = RiskAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")

        filing = Filing(
            company_cik="0000000001",
            filing_type="10-K",
            filing_date="2024-01-15",
            content={
                "revenue": 1000000,
                "net_income": -50000,
                "total_assets": 5000000,
                "total_equity": 100000,
                "total_debt": 4000000,
                "current_assets": 200000,
                "current_liabilities": 300000,
                "inventory": 50000,
                "operating_income": -30000,
                "ebitda": -10000,
                "free_cash_flow": -40000,
                "eps": -2.0,
                "pe_ratio": None,
                "pb_ratio": 0.5,
            },
        )

        assessment = analyzer.assess_risks(company, [filing], [])
        assert assessment is not None
        assert len(assessment.mitigations) > 0

    def test_assess_risks_deterministic(self):
        """Test that risk assessment is deterministic."""
        analyzer = RiskAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")

        filing = Filing(
            company_cik="0000000001",
            filing_type="10-K",
            filing_date="2024-01-15",
            content={
                "revenue": 1000000,
                "net_income": 100000,
                "total_assets": 5000000,
                "total_equity": 2000000,
                "total_debt": 1000000,
                "current_assets": 500000,
                "current_liabilities": 250000,
                "inventory": 100000,
                "operating_income": 200000,
                "ebitda": 300000,
                "free_cash_flow": 150000,
                "eps": 5.0,
                "pe_ratio": 20.0,
                "pb_ratio": 3.0,
            },
        )

        assessment1 = analyzer.assess_risks(company, [filing], [])
        assessment2 = analyzer.assess_risks(company, [filing], [])

        assert assessment1.overall_risk_score == assessment2.overall_risk_score
        assert len(assessment1.risk_factors) == len(assessment2.risk_factors)
