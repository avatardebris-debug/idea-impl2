"""Data models for Forensic Suite."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class RedFlagSeverity(str, Enum):
    """Severity levels for red flags."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Overall risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RedFlag:
    """A single fraud red flag."""
    category: str
    description: str
    severity: RedFlagSeverity
    details: Optional[str] = None


@dataclass
class IngestResult:
    """Result of ingesting a filing."""
    ticker: str
    cik: str
    accession_no: str
    filing_date: str
    filing_type: str
    item_count: int

    def to_json(self, path: Optional[str] = None) -> str:
        """Serialize to JSON."""
        data = {
            "ticker": self.ticker,
            "cik": self.cik,
            "accession_no": self.accession_no,
            "filing_date": self.filing_date,
            "filing_type": self.filing_type,
            "item_count": self.item_count,
        }
        text = json.dumps(data, indent=2)
        if path:
            with open(path, "w") as f:
                f.write(text)
        return text


@dataclass
class AnalysisResult:
    """Result of analyzing a filing."""
    ticker: str
    cik: str
    accession_no: str
    fraud_risk_score: float
    red_flags: List[RedFlag]
    advanced_flags: Optional[Dict] = None
    capital_flows: Optional[Dict] = None

    def to_json(self, path: Optional[str] = None) -> str:
        """Serialize to JSON."""
        data = {
            "ticker": self.ticker,
            "cik": self.cik,
            "accession_no": self.accession_no,
            "fraud_risk_score": self.fraud_risk_score,
            "red_flags": [
                {
                    "category": flag.category,
                    "description": flag.description,
                    "severity": flag.severity.value if isinstance(flag.severity, RedFlagSeverity) else flag.severity,
                    "details": flag.details,
                }
                for flag in self.red_flags
            ],
            "advanced_flags": self.advanced_flags,
            "capital_flows": self.capital_flows,
        }
        text = json.dumps(data, indent=2)
        if path:
            with open(path, "w") as f:
                f.write(text)
        return text


@dataclass
class FraudReport:
    """A complete fraud risk report."""
    ticker: str
    cik: str
    filing_date: str
    risk_score: float
    overall_risk: str
    red_flags: List[RedFlag]
    recommendations: List[str]

    def to_json(self, path: Optional[str] = None) -> str:
        """Serialize to JSON."""
        data = {
            "ticker": self.ticker,
            "cik": self.cik,
            "filing_date": self.filing_date,
            "risk_score": self.risk_score,
            "overall_risk": self.overall_risk,
            "red_flags": [
                {
                    "category": flag.category,
                    "description": flag.description,
                    "severity": flag.severity.value if isinstance(flag.severity, RedFlagSeverity) else flag.severity,
                    "details": flag.details,
                }
                for flag in self.red_flags
            ],
            "recommendations": self.recommendations,
        }
        text = json.dumps(data, indent=2)
        if path:
            with open(path, "w") as f:
                f.write(text)
        return text
