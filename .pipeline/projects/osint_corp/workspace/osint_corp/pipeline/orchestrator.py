"""Pipeline orchestration — coordinates the full OSINT analysis workflow."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from osint_corp.analysis.financial import FinancialAnalyzer, FinancialSummary
from osint_corp.analysis.network import NetworkAnalyzer, NetworkAnalysis
from osint_corp.analysis.risk import RiskAnalyzer, RiskAssessment
from osint_corp.models.entities import Company, Filing
from osint_corp.reports.generator import ReportGenerator

logger = logging.getLogger(__name__)


@dataclass
class PipelineStep:
    """A single step in the pipeline."""
    name: str
    status: str = "pending"  # "pending", "running", "completed", "failed"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    result: Any = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "error": self.error,
        }


@dataclass
class PipelineResult:
    """Complete result of a pipeline execution."""
    company_name: str
    ticker: Optional[str]
    cik: Optional[str]
    financial_summary: Optional[FinancialSummary] = None
    network_analysis: Optional[NetworkAnalysis] = None
    risk_assessment: Optional[RiskAssessment] = None
    html_report: Optional[str] = None
    json_report: Optional[str] = None
    text_report: Optional[str] = None
    steps: list[PipelineStep] = field(default_factory=list)
    total_duration: float = 0.0
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "ticker": self.ticker,
            "cik": self.cik,
            "financial_summary": self.financial_summary.to_dict() if self.financial_summary else None,
            "network_analysis": self.network_analysis.to_dict() if self.network_analysis else None,
            "risk_assessment": self.risk_assessment.to_dict() if self.risk_assessment else None,
            "html_report": self.html_report,
            "json_report": self.json_report,
            "text_report": self.text_report,
            "steps": [s.to_dict() for s in self.steps],
            "total_duration": self.total_duration,
            "completed_at": self.completed_at,
        }


class PipelineOrchestrator:
    """Orchestrates the full OSINT analysis pipeline."""

    def __init__(
        self,
        financial_analyzer: Optional[FinancialAnalyzer] = None,
        network_analyzer: Optional[NetworkAnalyzer] = None,
        risk_analyzer: Optional[RiskAnalyzer] = None,
        report_generator: Optional[ReportGenerator] = None,
    ):
        self.financial_analyzer = financial_analyzer or FinancialAnalyzer()
        self.network_analyzer = network_analyzer or NetworkAnalyzer()
        self.risk_analyzer = risk_analyzer or RiskAnalyzer()
        self.report_generator = report_generator or ReportGenerator()

    def run_pipeline(
        self,
        company: Company,
        filings: Optional[list[Filing]] = None,
        relationships: Optional[list] = None,
        include_financial: bool = True,
        include_network: bool = True,
        include_risk: bool = True,
        generate_reports: bool = True,
    ) -> PipelineResult:
        """Run the full OSINT analysis pipeline.

        Args:
            company: The target Company.
            filings: Optional list of SEC filings.
            relationships: Optional list of relationships.
            include_financial: Whether to run financial analysis.
            include_network: Whether to run network analysis.
            include_risk: Whether to run risk assessment.
            generate_reports: Whether to generate reports.

        Returns:
            PipelineResult with all analysis results.
        """
        start_time = time.time()
        steps: list[PipelineStep] = []
        result = PipelineResult(
            company_name=company.name,
            ticker=company.ticker,
            cik=company.cik,
            steps=steps,
        )

        try:
            # Step 1: Financial Analysis
            if include_financial:
                step = PipelineStep(name="Financial Analysis")
                steps.append(step)
                step.status = "running"
                step.start_time = time.time()

                try:
                    financial_summary = self.financial_analyzer.analyze_company(company, filings)
                    result.financial_summary = financial_summary
                    step.status = "completed"
                    step.result = financial_summary
                    logger.info(f"Financial analysis completed for {company.name}")
                except Exception as e:
                    step.status = "failed"
                    step.error = str(e)
                    logger.error(f"Financial analysis failed for {company.name}: {e}")

                step.end_time = time.time()
                step.duration = step.end_time - step.start_time

            # Step 2: Network Analysis
            if include_network:
                step = PipelineStep(name="Network Analysis")
                steps.append(step)
                step.status = "running"
                step.start_time = time.time()

                try:
                    network_analysis = self.network_analyzer.analyze_network(company, relationships)
                    result.network_analysis = network_analysis
                    step.status = "completed"
                    step.result = network_analysis
                    logger.info(f"Network analysis completed for {company.name}")
                except Exception as e:
                    step.status = "failed"
                    step.error = str(e)
                    logger.error(f"Network analysis failed for {company.name}: {e}")

                step.end_time = time.time()
                step.duration = step.end_time - step.start_time

            # Step 3: Risk Assessment
            if include_risk:
                step = PipelineStep(name="Risk Assessment")
                steps.append(step)
                step.status = "running"
                step.start_time = time.time()

                try:
                    risk_assessment = self.risk_analyzer.assess_risks(
                        company,
                        filings,
                        relationships,
                    )
                    result.risk_assessment = risk_assessment
                    step.status = "completed"
                    step.result = risk_assessment
                    logger.info(f"Risk assessment completed for {company.name}")
                except Exception as e:
                    step.status = "failed"
                    step.error = str(e)
                    logger.error(f"Risk assessment failed for {company.name}: {e}")

                step.end_time = time.time()
                step.duration = step.end_time - step.start_time

            # Step 4: Report Generation
            if generate_reports:
                step = PipelineStep(name="Report Generation")
                steps.append(step)
                step.status = "running"
                step.start_time = time.time()

                try:
                    result.html_report = self.report_generator.generate_report(
                        company,
                        result.financial_summary,
                        result.network_analysis,
                        result.risk_assessment,
                        format="html",
                    )
                    result.json_report = self.report_generator.generate_report(
                        company,
                        result.financial_summary,
                        result.network_analysis,
                        result.risk_assessment,
                        format="json",
                    )
                    result.text_report = self.report_generator.generate_report(
                        company,
                        result.financial_summary,
                        result.network_analysis,
                        result.risk_assessment,
                        format="text",
                    )
                    step.status = "completed"
                    logger.info("Reports generated successfully")
                except Exception as e:
                    step.status = "failed"
                    step.error = str(e)
                    logger.error(f"Report generation failed: {e}")

                step.end_time = time.time()
                step.duration = step.end_time - step.start_time

        except Exception as e:
            logger.error(f"Pipeline failed for {company.name}: {e}")
            result.completed_at = datetime.now().isoformat()
            result.total_duration = time.time() - start_time
            raise

        result.steps = steps
        result.total_duration = time.time() - start_time
        result.completed_at = datetime.now().isoformat()

        logger.info(
            f"Pipeline completed for {company.name} in {result.total_duration:.2f}s"
        )
        return result

    def run_pipeline_async(
        self,
        company: Company,
        filings: Optional[list[Filing]] = None,
        relationships: Optional[list] = None,
        include_financial: bool = True,
        include_network: bool = True,
        include_risk: bool = True,
        generate_reports: bool = True,
    ) -> PipelineResult:
        """Run the pipeline synchronously (placeholder for async future).

        In a production system, this would use asyncio.gather for parallel execution.
        For now, we run sequentially.
        """
        return self.run_pipeline(
            company,
            filings,
            relationships,
            include_financial,
            include_network,
            include_risk,
            generate_reports,
        )

    def get_pipeline_status(self, result: PipelineResult) -> dict:
        """Get the current status of a pipeline execution."""
        completed_steps = sum(1 for s in result.steps if s.status == "completed")
        failed_steps = sum(1 for s in result.steps if s.status == "failed")
        total_steps = len(result.steps)

        return {
            "company": result.company_name,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "pending_steps": total_steps - completed_steps - failed_steps,
            "total_duration": result.total_duration,
            "completed_at": result.completed_at,
            "steps": [s.to_dict() for s in result.steps],
        }
