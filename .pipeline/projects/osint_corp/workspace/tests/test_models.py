"""Tests for the models module."""

import pytest
from osint_corp.models.entities import (
    Company,
    Filing,
    Relationship,
    FinancialRatio,
    FinancialSummary,
    RiskFactor,
    RiskAssessment,
    NetworkNode,
    NetworkEdge,
    NetworkAnalysis,
)


class TestCompany:
    """Tests for the Company model."""

    def test_create_company(self):
        company = Company(
            name="Test Corp",
            ticker="TEST",
            cik="0000000001",
            industry="Technology",
        )
        assert company.name == "Test Corp"
        assert company.ticker == "TEST"
        assert company.cik == "0000000001"
        assert company.industry == "Technology"
        assert company.metadata == {}

    def test_company_to_dict(self):
        company = Company(
            name="Test Corp",
            ticker="TEST",
            cik="0000000001",
            industry="Technology",
        )
        d = company.to_dict()
        assert d["name"] == "Test Corp"
        assert d["ticker"] == "TEST"
        assert d["cik"] == "0000000001"
        assert d["industry"] == "Technology"
        assert d["metadata"] == {}

    def test_company_to_dict_with_metadata(self):
        company = Company(
            name="Test Corp",
            ticker="TEST",
            cik="0000000001",
            metadata={"founded": 2000, "headquarters": "NYC"},
        )
        d = company.to_dict()
        assert d["metadata"]["founded"] == 2000
        assert d["metadata"]["headquarters"] == "NYC"


class TestFiling:
    """Tests for the Filing model."""

    def test_create_filing(self):
        filing = Filing(
            company_name="Test Corp",
            ticker="TEST",
            cik="0000000001",
            filing_type="10-K",
            filing_date="2023-12-31",
            accession_number="0001234567-23-000001",
            url="https://example.com/filing",
        )
        assert filing.company_name == "Test Corp"
        assert filing.filing_type == "10-K"
        assert filing.filing_date == "2023-12-31"
        assert filing.accession_number == "0001234567-23-000001"
        assert filing.metadata == {}

    def test_filing_to_dict(self):
        filing = Filing(
            company_name="Test Corp",
            ticker="TEST",
            cik="0000000001",
            filing_type="10-Q",
            filing_date="2023-09-30",
            accession_number="0001234567-23-000002",
        )
        d = filing.to_dict()
        assert d["company_name"] == "Test Corp"
        assert d["filing_type"] == "10-Q"
        assert d["filing_date"] == "2023-09-30"

    def test_filing_with_financials(self):
        filing = Filing(
            company_name="Test Corp",
            ticker="TEST",
            cik="0000000001",
            filing_type="10-K",
            filing_date="2023-12-31",
            accession_number="0001234567-23-000001",
            financials={"revenue": 1000000, "net_income": 200000},
        )
        assert filing.financials["revenue"] == 1000000
        assert filing.financials["net_income"] == 200000


class TestRelationship:
    """Tests for the Relationship model."""

    def test_create_relationship(self):
        rel = Relationship(
            source_id="0000000001",
            source_type="company",
            target_id="0000000002",
            target_type="company",
            relationship_type="subsidiary",
            confidence=0.9,
        )
        assert rel.source_id == "0000000001"
        assert rel.relationship_type == "subsidiary"
        assert rel.confidence == 0.9

    def test_relationship_to_dict(self):
        rel = Relationship(
            source_id="0000000001",
            source_type="company",
            target_id="0000000002",
            target_type="company",
            relationship_type="subsidiary",
            confidence=0.9,
        )
        d = rel.to_dict()
        assert d["source_id"] == "0000000001"
        assert d["confidence"] == 0.9


class TestFinancialRatio:
    """Tests for the FinancialRatio model."""

    def test_financial_ratio_to_dict(self):
        ratio = FinancialRatio(
            name="Debt-to-Equity",
            value=1.5,
            description="Total liabilities / total equity",
            benchmark=1.0,
            trend="up",
        )
        d = ratio.to_dict()
        assert d["name"] == "Debt-to-Equity"
        assert d["value"] == 1.5
        assert d["benchmark"] == 1.0
        assert d["trend"] == "up"


class TestFinancialSummary:
    """Tests for the FinancialSummary model."""

    def test_financial_summary_to_dict(self):
        summary = FinancialSummary(
            company_name="Test Corp",
            ticker="TEST",
            filing_date="2023-12-31",
            total_assets=1000000,
            total_liabilities=500000,
            total_equity=500000,
            warnings=["High debt"],
            insights=["Strong margins"],
        )
        d = summary.to_dict()
        assert d["company_name"] == "Test Corp"
        assert d["total_assets"] == 1000000
        assert d["warnings"] == ["High debt"]
        assert d["insights"] == ["Strong margins"]


class TestRiskFactor:
    """Tests for the RiskFactor model."""

    def test_risk_factor_weighted_score(self):
        factor = RiskFactor(
            name="Financial Risk",
            score=80,
            weight=0.25,
            description="High financial risk",
        )
        assert factor.weighted_score() == 20.0

    def test_risk_factor_to_dict(self):
        factor = RiskFactor(
            name="Litigation Risk",
            score=60,
            weight=0.20,
            description="Moderate litigation risk",
            evidence=["Found 2 lawsuits"],
        )
        d = factor.to_dict()
        assert d["score"] == 60
        assert d["weight"] == 0.20
        assert d["evidence"] == ["Found 2 lawsuits"]


class TestRiskAssessment:
    """Tests for the RiskAssessment model."""

    def test_risk_assessment_to_dict(self):
        assessment = RiskAssessment(
            company_name="Test Corp",
            ticker="TEST",
            cik="0000000001",
            overall_score=75.5,
            risk_level="high",
            trend="deteriorating",
            recommendations=["Review financial health"],
        )
        d = assessment.to_dict()
        assert d["overall_score"] == 75.5
        assert d["risk_level"] == "high"
        assert d["trend"] == "deteriorating"
        assert d["recommendations"] == ["Review financial health"]


class TestNetworkNode:
    """Tests for the NetworkNode model."""

    def test_network_node_to_dict(self):
        node = NetworkNode(
            id="0000000001",
            name="Test Corp",
            node_type="company",
            metadata={"ticker": "TEST"},
        )
        d = node.to_dict()
        assert d["id"] == "0000000001"
        assert d["name"] == "Test Corp"
        assert d["node_type"] == "company"
        assert d["metadata"]["ticker"] == "TEST"


class TestNetworkEdge:
    """Tests for the NetworkEdge model."""

    def test_network_edge_to_dict(self):
        edge = NetworkEdge(
            source="0000000001",
            target="0000000002",
            relationship_type="subsidiary",
            confidence=0.9,
        )
        d = edge.to_dict()
        assert d["source"] == "0000000001"
        assert d["target"] == "0000000002"
        assert d["relationship_type"] == "subsidiary"
        assert d["confidence"] == 0.9


class TestNetworkAnalysis:
    """Tests for the NetworkAnalysis model."""

    def test_network_analysis_to_dict(self):
        analysis = NetworkAnalysis(
            company_name="Test Corp",
            ticker="TEST",
            insights=["Highly connected"],
        )
        d = analysis.to_dict()
        assert d["company_name"] == "Test Corp"
        assert d["insights"] == ["Highly connected"]
