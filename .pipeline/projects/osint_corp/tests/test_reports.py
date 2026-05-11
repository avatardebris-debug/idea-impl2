"""Tests for reports/generator module."""

import pytest
import json
from osint_corp.reports.generator import ReportGenerator
from osint_corp.models.entities import Company


class TestReportGenerator:
    """Tests for ReportGenerator."""

    def test_generate_html_report(self):
        """Test HTML report generation."""
        generator = ReportGenerator()
        company = Company(name="Test Corp", ticker="TEST")
        html = generator.generate_report(company, None, None, None, format="html")
        assert html is not None
        assert "<html" in html.lower()
        assert "Test Corp" in html
        assert "TEST" in html

    def test_generate_json_report(self):
        """Test JSON report generation."""
        generator = ReportGenerator()
        company = Company(name="Test Corp", ticker="TEST")
        json_str = generator.generate_report(company, None, None, None, format="json")
        data = json.loads(json_str)
        assert data["company_name"] == "Test Corp"
        assert data["ticker"] == "TEST"

    def test_generate_text_report(self):
        """Test text report generation."""
        generator = ReportGenerator()
        company = Company(name="Test Corp", ticker="TEST")
        text = generator.generate_report(company, None, None, None, format="text")
        assert text is not None
        assert "Test Corp" in text
        assert "TEST" in text

    def test_generate_report_invalid_format(self):
        """Test invalid format raises error."""
        generator = ReportGenerator()
        company = Company(name="Test Corp", ticker="TEST")
        with pytest.raises(ValueError, match="Invalid format"):
            generator.generate_report(company, None, None, None, format="invalid")

    def test_generate_report_with_financial_data(self):
        """Test report with financial data."""
        generator = ReportGenerator()
        company = Company(name="Test Corp", ticker="TEST")

        from osint_corp.analysis.financial import FinancialSummary
        financial_summary = FinancialSummary(
            revenue_ttm=1000000,
            net_income_ttm=100000,
            total_assets=5000000,
            total_equity=2000000,
            pe_ratio=20.0,
            roe=0.05,
        )

        html = generator.generate_report(
            company, financial_summary, None, None, format="html"
        )
        assert "1,000,000" in html or "1000000" in html
        assert "100,000" in html or "100000" in html

    def test_generate_report_with_network_data(self):
        """Test report with network data."""
        generator = ReportGenerator()
        company = Company(name="Test Corp", ticker="TEST")

        from osint_corp.analysis.network import NetworkAnalysis
        network_analysis = NetworkAnalysis(
            nodes=[{"id": "A", "type": "company"}],
            edges=[{"source": "A", "target": "B"}],
            key_officers=[{"name": "John", "role": "CEO"}],
        )

        html = generator.generate_report(
            company, None, network_analysis, None, format="html"
        )
        assert "John" in html
        assert "CEO" in html

    def test_generate_report_with_risk_data(self):
        """Test report with risk data."""
        generator = ReportGenerator()
        company = Company(name="Test Corp", ticker="TEST")

        from osint_corp.analysis.risk import RiskAssessment, RiskFactor
        risk_assessment = RiskAssessment(
            overall_risk_score=65,
            risk_level="Medium",
            risk_factors=[RiskFactor(name="Financial Risk", score=75)],
            mitigations=["Monitor debt"],
        )

        html = generator.generate_report(
            company, None, None, risk_assessment, format="html"
        )
        assert "Medium" in html
        assert "Financial Risk" in html

    def test_generate_report_all_data(self):
        """Test report with all data types."""
        generator = ReportGenerator()
        company = Company(name="Test Corp", ticker="TEST")

        from osint_corp.analysis.financial import FinancialSummary
        from osint_corp.analysis.network import NetworkAnalysis
        from osint_corp.analysis.risk import RiskAssessment, RiskFactor

        financial_summary = FinancialSummary(
            revenue_ttm=1000000,
            net_income_ttm=100000,
            total_assets=5000000,
            total_equity=2000000,
        )
        network_analysis = NetworkAnalysis(
            nodes=[{"id": "A", "type": "company"}],
            edges=[],
        )
        risk_assessment = RiskAssessment(
            overall_risk_score=50,
            risk_level="Medium",
            risk_factors=[],
            mitigations=[],
        )

        html = generator.generate_report(
            company, financial_summary, network_analysis, risk_assessment, format="html"
        )
        assert "Test Corp" in html
        assert "1,000,000" in html or "1000000" in html
        assert "Medium" in html

    def test_generate_report_json_all_data(self):
        """Test JSON report with all data types."""
        generator = ReportGenerator()
        company = Company(name="Test Corp", ticker="TEST")

        from osint_corp.analysis.financial import FinancialSummary
        from osint_corp.analysis.network import NetworkAnalysis
        from osint_corp.analysis.risk import RiskAssessment, RiskFactor

        financial_summary = FinancialSummary(
            revenue_ttm=1000000,
            net_income_ttm=100000,
            total_assets=5000000,
            total_equity=2000000,
        )
        network_analysis = NetworkAnalysis(
            nodes=[{"id": "A", "type": "company"}],
            edges=[],
        )
        risk_assessment = RiskAssessment(
            overall_risk_score=50,
            risk_level="Medium",
            risk_factors=[],
            mitigations=[],
        )

        json_str = generator.generate_report(
            company, financial_summary, network_analysis, risk_assessment, format="json"
        )
        data = json.loads(json_str)
        assert data["company_name"] == "Test Corp"
        assert data["financial_summary"]["revenue_ttm"] == 1000000
        assert data["risk_assessment"]["overall_risk_score"] == 50
