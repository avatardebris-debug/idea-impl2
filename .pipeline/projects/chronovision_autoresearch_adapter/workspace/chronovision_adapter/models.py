"""Core data models for the Chronovision Autoresearch Adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Paper:
    """Represents a research paper from any source."""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    source: str  # "arxiv", "openreview", "biorxiv", "nasa_ads", "nber"
    published_date: str  # ISO format
    url: str = ""
    categories: List[str] = field(default_factory=list)
    citation_count: int = 0
    keywords: List[str] = field(default_factory=list)
    doi: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Paper:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> Paper:
        return cls.from_dict(json.loads(json_str))


@dataclass
class FundingEvent:
    """Represents a funding/investment event."""
    event_id: str
    company: str
    amount_usd: float
    round_type: str  # "seed", "series_a", "series_b", etc.
    investors: List[str]
    date: str  # ISO format
    sector: str = ""
    source: str = ""  # "crunchbase", "pitchbook", "cb_insights", "yc", "a16z"
    description: str = ""
    valuation_usd: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FundingEvent:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> FundingEvent:
        return cls.from_dict(json.loads(json_str))


@dataclass
class ResearchTrend:
    """Aggregated trend signal combining papers and funding."""
    topic: str
    paper_count: int = 0
    funding_total_usd: float = 0.0
    funding_event_count: int = 0
    momentum_score: float = 0.0  # 0-1 normalized
    top_papers: List[str] = field(default_factory=list)  # paper_ids
    top_investors: List[str] = field(default_factory=list)
    sectors: List[str] = field(default_factory=list)
    first_seen: str = ""
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ResearchTrend:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> ResearchTrend:
        return cls.from_dict(json.loads(json_str))
