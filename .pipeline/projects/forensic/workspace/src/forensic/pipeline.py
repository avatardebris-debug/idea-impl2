"""Forensic pipeline - Orchestrates ingestion and analysis."""

import logging
import re
from typing import Optional, Dict, List

from forensic.models import IngestResult, AnalysisResult, RedFlag, FraudReport, RiskLevel
from forensic.database import ForensicDatabase
from forensic.scoring import compute_fraud_score, get_risk_level, generate_report as scoring_report
from forensic.red_flags import run_all_checks
from forensic.config import get_config

logger = logging.getLogger("forensic.pipeline")


class ForensicPipeline:
    """Main pipeline for forensic analysis."""

    def __init__(self, db_path: Optional[str] = None):
        config = get_config()
        self.db = ForensicDatabase(db_path or config.db_path)
        from forensic.analyzer import FraudAnalyzer
        self.analyzer = FraudAnalyzer()

    def ingest_filing(self, ticker: str, filing_type: str = "10-K") -> IngestResult:
        """Ingest a filing for a given ticker."""
        try:
            from sec_importer.fetcher import (
                get_cik_from_ticker,
                get_latest_filing,
                download_filing_text,
                get_company_info,
            )
            from sec_importer.models import FilingItemModel
            from sec_importer.parser import FilingParser
        except ImportError as e:
            raise ImportError(f"Failed to import sec_importer modules: {e}") from e

        # Resolve ticker to CIK
        cik = get_cik_from_ticker(ticker)
        if not cik:
            raise ValueError(f"Could not resolve ticker {ticker} to CIK")

        # Get company info
        company_info = get_company_info(cik)
        if company_info:
            self.db.upsert_company(company_info)

        # Get latest filing
        latest_filing = get_latest_filing(cik, filing_type)
        if not latest_filing:
            raise ValueError(f"No {filing_type} filing found for CIK {cik}")

        # Store filing
        self.db.upsert_filing(latest_filing)

        # Download and parse filing
        filing_text = download_filing_text(latest_filing["accession_no"], cik)
        if not filing_text:
            raise ValueError(f"Could not download filing {latest_filing['accession_no']}")

        parser = FilingParser()
        items = parser.parse(filing_text, filing_type)

        # Store items in database
        filing_record = self.db.get_latest_filing(ticker)
        if filing_record:
            self.db.upsert_items(filing_record["id"], latest_filing["accession_no"], items)

        logger.info(
            "Ingested %d items for %s (CIK=%s, %s, %s)",
            len(items),
            ticker,
            cik,
            latest_filing["filing_type"],
            latest_filing["filing_date"],
        )

        return IngestResult(
            ticker=ticker,
            cik=cik,
            accession_no=latest_filing["accession_no"],
            filing_date=latest_filing["filing_date"] or "",
            filing_type=latest_filing["filing_type"],
            item_count=len(items),
        )

    def analyze_filing(self, ticker: str) -> AnalysisResult:
        """Analyze a filing for fraud indicators."""
        # Get filing data from database
        filing_data = self.db.get_latest_filing(ticker)
        if not filing_data:
            raise ValueError(f"No filing found for ticker {ticker}")

        # Get items
        items = self.db.get_filing_items(filing_data["accession_no"])

        # Extract text from items for the FraudAnalyzer
        text_parts = [item.get("item_content", "") for item in items if item.get("item_content")]
        full_text = "\n".join(text_parts)

        # Extract financial and cash flow data for the FraudAnalyzer
        financial_data = self._extract_financial_data(items)
        cash_flow_data = self._extract_cash_flow_data(items)

        # Use the FraudAnalyzer for comprehensive analysis
        fraud_score, red_flags = self.analyzer.analyze(
            text=full_text,
            financial_data=financial_data,
            cash_flow_data=cash_flow_data,
            disclosure_text=full_text,
        )

        return AnalysisResult(
            ticker=ticker,
            cik=filing_data["cik"],
            accession_no=filing_data["accession_no"],
            fraud_risk_score=fraud_score,
            red_flags=red_flags,
        )

    def generate_report(self, ticker: str) -> FraudReport:
        """Generate a fraud risk report."""
        analysis = self.analyze_filing(ticker)

        # Determine overall risk level using scoring module
        overall_risk = get_risk_level(analysis.fraud_risk_score)

        # Generate recommendations using scoring module
        report_data = scoring_report(
            ticker=ticker,
            cik=analysis.cik,
            accession_no=analysis.accession_no,
            flags=analysis.red_flags,
        )

        return FraudReport(
            ticker=ticker,
            cik=analysis.cik,
            risk_score=analysis.fraud_risk_score,
            overall_risk=overall_risk,
            red_flags=analysis.red_flags,
            recommendations=report_data["recommendations"],
        )

    def _extract_financial_data(self, items: List[Dict]) -> Dict[str, float]:
        """Extract financial data from filing items."""
        financial_data = {}
        revenue_pattern = re.compile(r'revenue\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)', re.IGNORECASE)
        expense_pattern = re.compile(r'expenses\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)', re.IGNORECASE)
        
        for item in items:
            content = item.get("item_content", "")
            if "revenue" in content.lower():
                revenue_match = revenue_pattern.search(content)
                if revenue_match:
                    financial_data["revenue"] = float(revenue_match.group(1).replace(",", ""))
            if "expenses" in content.lower():
                expense_match = expense_pattern.search(content)
                if expense_match:
                    financial_data["expenses"] = float(expense_match.group(1).replace(",", ""))
        return financial_data

    def _extract_cash_flow_data(self, items: List[Dict]) -> Dict[str, float]:
        """Extract cash flow data from filing items."""
        cash_flow_data = {}
        net_income_pattern = re.compile(r'net income\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)', re.IGNORECASE)
        operating_cf_pattern = re.compile(r'operating cash flow\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)', re.IGNORECASE)
        
        for item in items:
            content = item.get("item_content", "")
            if "cash flow" in content.lower():
                net_income_match = net_income_pattern.search(content)
                if net_income_match:
                    cash_flow_data["net_income"] = float(net_income_match.group(1).replace(",", ""))
                operating_cf_match = operating_cf_pattern.search(content)
                if operating_cf_match:
                    cash_flow_data["operating_cash_flow"] = float(operating_cf_match.group(1).replace(",", ""))
        return cash_flow_data

    def _generate_recommendations(self, red_flags: List[RedFlag]) -> List[str]:
        """Generate recommendations based on red flags."""
        recommendations = []

        categories = set(flag.category for flag in red_flags)

        if "text_pattern" in categories:
            recommendations.append("Review all mentions of fraud, restatements, and litigation in detail")
            recommendations.append("Verify the context of suspicious language with management")

        if "financial_ratio" in categories:
            recommendations.append("Conduct detailed analysis of financial ratios over multiple periods")
            recommendations.append("Compare ratios to industry peers")

        if "cash_flow" in categories:
            recommendations.append("Analyze cash flow statement in detail")
            recommendations.append("Verify operating cash flow quality")

        if "disclosure" in categories:
            recommendations.append("Review disclosure completeness and quality")
            recommendations.append("Compare disclosures to industry standards")

        if not recommendations:
            recommendations.append("No specific recommendations at this time")

        return recommendations
