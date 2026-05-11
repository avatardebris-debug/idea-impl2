"""Tests for analysis/financial module."""

import pytest
from osint_corp.analysis.financial import (
    FinancialAnalyzer,
    FinancialSummary,
    FinancialRatio,
)
from osint_corp.models.entities import Company, Filing


class TestFinancialRatio:
    """Tests for FinancialRatio."""

    def test_financial_ratio_creation(self):
        """Test creating a FinancialRatio."""
        ratio = FinancialRatio(name="ROE", value=0.15, industry_avg=0.12)
        assert ratio.name == "ROE"
        assert ratio.value == 0.15
        assert ratio.industry_avg == 0.12
        assert ratio.is_positive is True

    def test_financial_ratio_negative(self):
        """Test negative ratio."""
        ratio = FinancialRatio(name="Net Margin", value=-0.05)
        assert ratio.is_positive is False

    def test_financial_ratio_comparison(self):
        """Test ratio comparison."""
        ratio = FinancialRatio(name="ROE", value=0.15, industry_avg=0.12)
        assert ratio.is_better_than_industry is True

        ratio2 = FinancialRatio(name="ROE", value=0.10, industry_avg=0.12)
        assert ratio2.is_better_than_industry is False


class TestFinancialSummary:
    """Tests for FinancialSummary."""

    def test_financial_summary_creation(self):
        """Test creating a FinancialSummary."""
        summary = FinancialSummary(
            revenue_ttm=1000000,
            net_income_ttm=100000,
            total_assets=5000000,
            total_equity=2000000,
            total_debt=1000000,
            current_assets=500000,
            current_liabilities=250000,
            inventory=100000,
            operating_income=200000,
            ebitda=300000,
            free_cash_flow=150000,
            eps=5.0,
            pe_ratio=20.0,
            pb_ratio=3.0,
            roe=0.05,
            roa=0.02,
            debt_to_equity=0.5,
            current_ratio=2.0,
            quick_ratio=1.6,
            operating_margin=0.2,
            net_margin=0.1,
            ratios=[],
        )
        assert summary.revenue_ttm == 1000000
        assert summary.roe == 0.05
        assert summary.debt_to_equity == 0.5

    def test_financial_summary_to_dict(self):
        """Test FinancialSummary serialization."""
        summary = FinancialSummary(
            revenue_ttm=1000000,
            net_income_ttm=100000,
            total_assets=5000000,
            total_equity=2000000,
            ratios=[FinancialRatio(name="ROE", value=0.15)],
        )
        d = summary.to_dict()
        assert d["revenue_ttm"] == 1000000
        assert d["ratios"][0]["name"] == "ROE"

    def test_financial_summary_from_dict(self):
        """Test FinancialSummary deserialization."""
        d = {
            "revenue_ttm": 1000000,
            "net_income_ttm": 100000,
            "total_assets": 5000000,
            "total_equity": 2000000,
            "ratios": [{"name": "ROE", "value": 0.15}],
        }
        summary = FinancialSummary.from_dict(d)
        assert summary.revenue_ttm == 1000000
        assert len(summary.ratios) == 1
        assert summary.ratios[0].name == "ROE"


class TestFinancialAnalyzer:
    """Tests for FinancialAnalyzer."""

    def test_analyze_company_no_filings(self):
        """Test analysis with no filings returns empty summary."""
        analyzer = FinancialAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")
        summary = analyzer.analyze_company(company, [])
        assert summary is not None
        assert summary.revenue_ttm is None

    def test_analyze_company_with_filing(self):
        """Test analysis with a filing containing financial data."""
        analyzer = FinancialAnalyzer()
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

        summary = analyzer.analyze_company(company, [filing])
        assert summary is not None
        assert summary.revenue_ttm == 1000000
        assert summary.net_income_ttm == 100000
        assert summary.roe == pytest.approx(0.05)
        assert summary.debt_to_equity == pytest.approx(0.5)
        assert summary.current_ratio == pytest.approx(2.0)

    def test_analyze_company_multiple_filings(self):
        """Test analysis with multiple filings uses the latest."""
        analyzer = FinancialAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")

        filing1 = Filing(
            company_cik="0000000001",
            filing_type="10-K",
            filing_date="2023-01-15",
            content={"revenue": 800000, "net_income": 80000},
        )
        filing2 = Filing(
            company_cik="0000000001",
            filing_type="10-K",
            filing_date="2024-01-15",
            content={"revenue": 1000000, "net_income": 100000},
        )

        summary = analyzer.analyze_company(company, [filing1, filing2])
        assert summary.revenue_ttm == 1000000

    def test_calculate_ratios(self):
        """Test ratio calculation."""
        analyzer = FinancialAnalyzer()
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

        summary = analyzer.analyze_company(company, [filing])

        # Check calculated ratios
        assert summary.roe == pytest.approx(0.05)  # 100k / 2M
        assert summary.roa == pytest.approx(0.02)  # 100k / 5M
        assert summary.debt_to_equity == pytest.approx(0.5)  # 1M / 2M
        assert summary.current_ratio == pytest.approx(2.0)  # 500k / 250k
        assert summary.quick_ratio == pytest.approx(1.6)  # (500k - 100k) / 250k
        assert summary.operating_margin == pytest.approx(0.2)  # 200k / 1M
        assert summary.net_margin == pytest.approx(0.1)  # 100k / 1M

    def test_calculate_ratios_zero_division(self):
        """Test that zero division is handled."""
        analyzer = FinancialAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")

        filing = Filing(
            company_cik="0000000001",
            filing_type="10-K",
            filing_date="2024-01-15",
            content={
                "revenue": 1000000,
                "net_income": 100000,
                "total_assets": 0,  # Zero assets
                "total_equity": 0,  # Zero equity
                "total_debt": 0,
                "current_assets": 0,
                "current_liabilities": 0,
                "inventory": 0,
                "operating_income": 0,
                "ebitda": 0,
                "free_cash_flow": 0,
                "eps": 0,
                "pe_ratio": 0,
                "pb_ratio": 0,
            },
        )

        summary = analyzer.analyze_company(company, [filing])
        # Should not raise, ratios should be None
        assert summary.roe is None
        assert summary.roa is None
        assert summary.debt_to_equity is None
        assert summary.current_ratio is None
