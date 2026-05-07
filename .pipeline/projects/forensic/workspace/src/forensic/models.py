"""Pydantic models for forensic fraud analysis outputs."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    """Red flag severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskLevel(str, Enum):
    """Composite fraud risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RedFlagEntry(BaseModel):
    """A single fraud red flag finding."""

    flag_name: str = Field(description="Name of the red flag check")
    severity: Severity = Field(description="Severity of the red flag")
    evidence_excerpt: str = Field(description="Relevant excerpt from the filing")
    score_contribution: float = Field(
        ge=0.0, le=100.0, description="Points contributed to the composite score"
    )

    def model_dump(self, **kwargs) -> dict:
        """Serialize to dict, converting enum to string."""
        data = super().model_dump(**kwargs)
        data["severity"] = data["severity"].value
        return data


class FraudScore(BaseModel):
    """Composite fraud score for a filing."""

    fraud_score: int = Field(
        ge=0, le=100, description="Composite fraud score from 0 to 100"
    )
    risk_level: RiskLevel = Field(description="Mapped risk level")
    top_red_flags: List[RedFlagEntry] = Field(
        default_factory=list, description="Top 3 red flags by score"
    )

    @field_validator("risk_level", mode="before")
    @classmethod
    def _map_risk_level(cls, v):
        """Map numeric score to risk level."""
        if isinstance(v, RiskLevel):
            return v
        return None  # will be set by compute_fraud_score

    def model_dump(self, **kwargs) -> dict:
        """Serialize to dict, converting enums to strings."""
        data = super().model_dump(**kwargs)
        data["risk_level"] = data["risk_level"].value
        return data


class AnalysisReport(BaseModel):
    """Full forensic analysis report."""

    ticker: str = Field(description="Company ticker symbol")
    cik: str = Field(description="CIK number")
    filing_date: str = Field(description="Date of the analyzed filing")
    fraud_score: FraudScore = Field(description="Composite fraud score")
    red_flags: List[RedFlagEntry] = Field(
        default_factory=list, description="All detected red flags"
    )
    summary: str = Field(
        default="", description="Human-readable summary of findings"
    )

    def model_dump(self, **kwargs) -> dict:
        """Serialize to dict, converting enums to strings."""
        data = super().model_dump(**kwargs)
        data["fraud_score"] = self.fraud_score.model_dump()
        for flag in data.get("red_flags", []):
            if isinstance(flag, dict) and "severity" in flag:
                flag["severity"] = flag["severity"].value if hasattr(flag["severity"], "value") else flag["severity"]
        return data
