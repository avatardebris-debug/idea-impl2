"""Tests for pipeline/orchestrator module."""

import pytest
from osint_corp.pipeline.orchestrator import (
    PipelineOrchestrator,
    PipelineResult,
    PipelineStep,
)
from osint_corp.models.entities import Company, Filing


class TestPipelineStep:
    """Tests for PipelineStep."""

    def test_pipeline_step_creation(self):
        """Test creating a PipelineStep."""
        step = PipelineStep(name="Test Step")
        assert step.name == "Test Step"
        assert step.status == "pending"
        assert step.start_time is None
        assert step.duration is None

    def test_pipeline_step_to_dict(self):
        """Test PipelineStep serialization."""
        step = PipelineStep(
            name="Test Step",
            status="completed",
            start_time=1000.0,
            end_time=1005.0,
            duration=5.0,
        )
        d = step.to_dict()
        assert d["name"] == "Test Step"
        assert d["status"] == "completed"
        assert d["duration"] == 5.0


class TestPipelineResult:
    """Tests for PipelineResult."""

    def test_pipeline_result_creation(self):
        """Test creating a PipelineResult."""
        result = PipelineResult(
            company_name="Test Corp",
            ticker="TEST",
            cik="0000000001",
        )
        assert result.company_name == "Test Corp"
        assert result.ticker == "TEST"
        assert result.steps == []
        assert result.total_duration == 0.0

    def test_pipeline_result_to_dict(self):
        """Test PipelineResult serialization."""
        from osint_corp.analysis.financial import FinancialSummary

        result = PipelineResult(
            company_name="Test Corp",
            ticker="TEST",
            financial_summary=FinancialSummary(
                revenue_ttm=1000000,
                net_income_ttm=100000,
                total_assets=5000000,
                total_equity=2000000,
            ),
        )
        d = result.to_dict()
        assert d["company_name"] == "Test Corp"
        assert d["financial_summary"]["revenue_ttm"] == 1000000


class TestPipelineOrchestrator:
    """Tests for PipelineOrchestrator."""

    def test_orchestrator_creation(self):
        """Test creating a PipelineOrchestrator."""
        orchestrator = PipelineOrchestrator()
        assert orchestrator is not None

    def test_run_pipeline_basic(self):
        """Test running the pipeline with basic data."""
        orchestrator = PipelineOrchestrator()
        company = Company(name="Test Corp", ticker="TEST")

        result = orchestrator.run_pipeline(
            company,
            include_financial=True,
            include_network=False,
            include_risk=False,
            generate_reports=False,
        )
        assert result.company_name == "Test Corp"
        assert result.ticker == "TEST"
        assert len(result.steps) > 0
        assert result.total_duration >= 0

    def test_run_pipeline_with_financial_data(self):
        """Test pipeline with financial data."""
        orchestrator = PipelineOrchestrator()
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

        result = orchestrator.run_pipeline(
            company,
            filings=[filing],
            include_financial=True,
            include_network=False,
            include_risk=False,
            generate_reports=False,
        )
        assert result.financial_summary is not None
        assert result.financial_summary.revenue_ttm == 1000000

    def test_run_pipeline_with_reports(self):
        """Test pipeline with report generation."""
        orchestrator = PipelineOrchestrator()
        company = Company(name="Test Corp", ticker="TEST")

        result = orchestrator.run_pipeline(
            company,
            include_financial=False,
            include_network=False,
            include_risk=False,
            generate_reports=True,
        )
        assert result.html_report is not None
        assert result.json_report is not None
        assert result.text_report is not None
        assert "Test Corp" in result.html_report
        assert "Test Corp" in result.json_report
        assert "Test Corp" in result.text_report

    def test_run_pipeline_all_components(self):
        """Test pipeline with all components."""
        orchestrator = PipelineOrchestrator()
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

        relationships = [
            {
                "source_name": "Test Corp",
                "target_name": "Subsidiary Inc",
                "relationship_type": "subsidiary",
                "strength": 0.8,
            },
        ]

        result = orchestrator.run_pipeline(
            company,
            filings=[filing],
            relationships=relationships,
            include_financial=True,
            include_network=True,
            include_risk=True,
            generate_reports=True,
        )
        assert result.financial_summary is not None
        assert result.network_analysis is not None
        assert result.risk_assessment is not None
        assert result.html_report is not None
        assert result.json_report is not None
        assert result.text_report is not None

    def test_run_pipeline_invalid_company(self):
        """Test pipeline with invalid company."""
        orchestrator = PipelineOrchestrator()
        with pytest.raises(ValueError, match="Company name and ticker are required"):
            orchestrator.run_pipeline(
                Company(name="", ticker=""),
                include_financial=False,
                include_network=False,
                include_risk=False,
                generate_reports=False,
            )

    def test_run_pipeline_deterministic(self):
        """Test that pipeline results are deterministic."""
        orchestrator = PipelineOrchestrator()
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

        result1 = orchestrator.run_pipeline(
            company,
            filings=[filing],
            include_financial=True,
            include_network=False,
            include_risk=False,
            generate_reports=False,
        )
        result2 = orchestrator.run_pipeline(
            company,
            filings=[filing],
            include_financial=True,
            include_network=False,
            include_risk=False,
            generate_reports=False,
        )

        assert result1.financial_summary.revenue_ttm == result2.financial_summary.revenue_ttm
        assert result1.financial_summary.roe == result2.financial_summary.roe
