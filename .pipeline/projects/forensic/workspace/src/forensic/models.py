"""Pydantic models for forensic fraud analysis outputs."""

from __future__ import annotations

import json
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RedFlagSeverity(str, Enum):
    """Severity levels for red flags."""

    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def _missing_(cls, value):
        """Handle unknown values gracefully."""
        return None


class RiskLevel(str, Enum):
    """Composite fraud risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Red flag / recommendation
# ---------------------------------------------------------------------------

class RedFlag(BaseModel):
    """A single fraud red flag finding."""

    category: str = Field(description="Category of the red flag")
    description: str = Field(default="", description="Human-readable description")
    severity: RedFlagSeverity = Field(description="Severity of the red flag")
    evidence: Optional[str] = Field(default=None, description="Supporting evidence excerpt")

    def model_dump(self, **kwargs) -> dict:
        """Serialize to dict, converting enum to string."""
        data = super().model_dump(**kwargs)
        data["severity"] = data["severity"].value
        return data

    def to_dict(self, **kwargs) -> dict:
        """Serialize to dict."""
        return self.model_dump(**kwargs)

    @classmethod
    def from_dict(cls, data: dict) -> "RedFlag":
        """Deserialize from dict."""
        severity = data.get("severity", "info")
        if isinstance(severity, str):
            severity = RedFlagSeverity(severity)
        return cls(
            category=data.get("category", ""),
            description=data.get("description", ""),
            severity=severity,
            evidence=data.get("evidence"),
        )


class Recommendation(BaseModel):
    """An actionable recommendation."""

    category: str = Field(description="Category of the recommendation")
    description: str = Field(description="Human-readable recommendation text")
    priority: str = Field(description="Priority level (low / medium / high / critical)")

    def model_dump(self, **kwargs) -> dict:
        """Serialize to dict."""
        return super().model_dump(**kwargs)

    def to_dict(self, **kwargs) -> dict:
        """Serialize to dict."""
        return self.model_dump(**kwargs)


# ---------------------------------------------------------------------------
# Fraud score / report
# ---------------------------------------------------------------------------

class FraudScore(BaseModel):
    """Composite fraud score for a filing."""

    score: float = Field(ge=0.0, le=100.0, description="Composite fraud score from 0 to 100")
    risk_level: RiskLevel = Field(description="Mapped risk level")
    top_red_flags: List[RedFlag] = Field(default_factory=list, description="Top red flags by score")

    def model_dump(self, **kwargs) -> dict:
        """Serialize to dict."""
        data = super().model_dump(**kwargs)
        data["risk_level"] = data["risk_level"].value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "FraudScore":
        """Deserialize from dict."""
        red_flags = [RedFlag(**flag) for flag in data.get("top_red_flags", [])]
        return cls(
            score=data.get("score", 0.0),
            risk_level=RiskLevel(data.get("risk_level", "low")),
            top_red_flags=red_flags,
        )


class Report(BaseModel):
    """Complete fraud risk report for a filing."""

    ticker: str = Field(description="Company ticker symbol")
    cik: str = Field(description="Company CIK")
    filing_date: str = Field(description="Filing date")
    risk_score: float = Field(ge=0.0, le=100.0, description="Composite fraud score")
    overall_risk: str = Field(description="Overall risk level string")
    red_flags: List[RedFlag] = Field(default_factory=list, description="All detected red flags")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Actionable recommendations")

    def model_dump(self, **kwargs) -> dict:
        """Serialize to dict."""
        data = super().model_dump(**kwargs)
        data["red_flags"] = [flag.model_dump() for flag in self.red_flags]
        data["recommendations"] = [r.model_dump() for r in self.recommendations]
        return data

    def to_dict(self, **kwargs) -> dict:
        """Serialize to dict."""
        return self.model_dump(**kwargs)

    def to_json(self, path: Optional[str] = None, **kwargs) -> Optional[str]:
        """Serialize to JSON string or write to file."""
        data = self.to_dict()
        if path:
            with open(path, "w") as f:
                json.dump(data, f, **kwargs)
            return None
        return json.dumps(data, **kwargs)

    @classmethod
    def from_dict(cls, data: dict) -> "Report":
        """Deserialize from dict."""
        red_flags = [RedFlag(**flag) for flag in data.get("red_flags", [])]
        recommendations = [Recommendation(**rec) for rec in data.get("recommendations", [])]
        return cls(
            ticker=data.get("ticker", ""),
            cik=data.get("cik", ""),
            filing_date=data.get("filing_date", ""),
            risk_score=data.get("risk_score", 0.0),
            overall_risk=data.get("overall_risk", "low"),
            red_flags=red_flags,
            recommendations=recommendations,
        )


# Alias for backward compatibility and explicit usage
FraudReport = Report


# ---------------------------------------------------------------------------
# Pipeline ingest / analysis results
# ---------------------------------------------------------------------------

class IngestResult(BaseModel):
    """Result of the ingestion pipeline."""

    ticker: str
    cik: str
    accession_no: str
    filing_type: str
    filing_date: str
    item_count: int = 0
    success: bool = True
    error: Optional[str] = None

    def model_dump(self, **kwargs) -> dict:
        """Serialize to dict."""
        return super().model_dump(**kwargs)

    def to_dict(self, **kwargs) -> dict:
        """Serialize to dict."""
        return self.model_dump(**kwargs)

    def to_json(self, path: Optional[str] = None, **kwargs) -> Optional[str]:
        """Serialize to JSON string or write to file."""
        data = self.to_dict()
        if path:
            with open(path, "w") as f:
                json.dump(data, f, **kwargs)
            return None
        return json.dumps(data, **kwargs)


class AnalysisResult(BaseModel):
    """Result of the analysis pipeline."""

    ticker: str
    cik: str
    accession_no: str
    filing_date: str = ""
    fraud_risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    red_flags: List[RedFlag] = Field(default_factory=list)
    capital_flows: Optional[dict] = None
    advanced_flags: Optional[dict] = None
    report: Optional[Report] = None

    def model_dump(self, **kwargs) -> dict:
        """Serialize to dict."""
        data = super().model_dump(**kwargs)
        data["risk_level"] = data["risk_level"].value
        data["red_flags"] = [flag.model_dump() for flag in self.red_flags]
        if self.report:
            data["report"] = self.report.model_dump()
        return data

    def to_dict(self, **kwargs) -> dict:
        """Serialize to dict."""
        return self.model_dump(**kwargs)

    def to_json(self, path: Optional[str] = None, **kwargs) -> Optional[str]:
        """Serialize to JSON string or write to file."""
        data = self.to_dict()
        if path:
            with open(path, "w") as f:
                json.dump(data, f, **kwargs)
            return None
        return json.dumps(data, **kwargs)
