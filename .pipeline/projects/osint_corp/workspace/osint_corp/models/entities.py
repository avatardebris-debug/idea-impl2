"""Core data models for OSINT Corp — corporate entities and related objects."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Optional


def _dataclass_to_dict(obj: Any) -> dict:
    """Convert a dataclass instance to a dict, handling nested dataclasses."""
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for fname in obj.__dataclass_fields__:
            val = getattr(obj, fname)
            result[fname] = _dataclass_to_dict(val)
        return result
    elif isinstance(obj, list):
        return [_dataclass_to_dict(i) for i in obj]
    elif isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def _dataclass_from_dict(cls: type, data: dict) -> Any:
    """Create a dataclass instance from a dict, handling nested dataclasses."""
    if hasattr(cls, "__dataclass_fields__"):
        kwargs = {}
        for fname in cls.__dataclass_fields__:
            val = data.get(fname)
            if val is None:
                kwargs[fname] = None
            elif hasattr(cls.__dataclass_fields__[fname].type, "__dataclass_fields__"):
                nested_cls = cls.__dataclass_fields__[fname].type
                kwargs[fname] = _dataclass_from_dict(nested_cls, val)
            elif isinstance(val, list) and len(val) > 0:
                # Try to detect list of dataclasses
                item_type = cls.__dataclass_fields__[fname].type.__args__[0] if hasattr(cls.__dataclass_fields__[fname].type, "__args__") else None
                if item_type and hasattr(item_type, "__dataclass_fields__"):
                    kwargs[fname] = [_dataclass_from_dict(item_type, i) for i in val]
                else:
                    kwargs[fname] = val
            else:
                kwargs[fname] = val
        return cls(**kwargs)
    return data


@dataclass
class Company:
    """Represents a corporate entity from registry or filing data."""
    name: str
    ticker: Optional[str] = None
    cik: Optional[str] = None
    jurisdiction: Optional[str] = None
    state_of_incorporation: Optional[str] = None
    registration_number: Optional[str] = None
    incorporation_date: Optional[str] = None
    industry: Optional[str] = None
    sic_code: Optional[str] = None
    naics_code: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None  # active, inactive, dissolved, etc.
    source: Optional[str] = None  # e.g., "sec", "opencorporates", "sos"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> Company:
        return _dataclass_from_dict(cls, data)

    @classmethod
    def from_json(cls, json_str: str) -> Company:
        return cls.from_dict(json.loads(json_str))


@dataclass
class Filing:
    """Represents an SEC filing (10-K, 10-Q, 8-K, etc.)."""
    company_name: str
    filing_type: str  # 10-K, 10-Q, 8-K, etc.
    accession_number: Optional[str] = None
    filing_date: Optional[str] = None
    ticker: Optional[str] = None
    cik: Optional[str] = None
    document_url: Optional[str] = None
    url: Optional[str] = None  # Alias for document_url for compatibility
    accepted_date: Optional[str] = None
    form_description: Optional[str] = None
    financials: dict = field(default_factory=dict)  # extracted financial data
    material_events: list = field(default_factory=list)  # for 8-K items
    primary_document: Optional[str] = None
    source: Optional[str] = "sec_edgar"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> Filing:
        return _dataclass_from_dict(cls, data)

    @classmethod
    def from_json(cls, json_str: str) -> Filing:
        return cls.from_dict(json.loads(json_str))


@dataclass
class Relationship:
    """Represents a link between two entities."""
    source_type: str  # "Company", "Filing", etc.
    source_id: str  # identifier of the source entity
    target_type: str
    target_id: str  # identifier of the target entity
    relationship_type: str  # "subsidiary_of", "officer_of", "same_address", etc.
    confidence: float = 0.0  # 0.0 to 1.0
    evidence: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> Relationship:
        return _dataclass_from_dict(cls, data)

    @classmethod
    def from_json(cls, json_str: str) -> Relationship:
        return cls.from_dict(json.loads(json_str))


@dataclass
class Location:
    """Represents a physical or mailing address."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_type: Optional[str] = None  # "headquarters", "registered_agent", "mailing"
    source: Optional[str] = None

    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> Location:
        return _dataclass_from_dict(cls, data)

    @classmethod
    def from_json(cls, json_str: str) -> Location:
        return cls.from_dict(json.loads(json_str))


@dataclass
class Manifest:
    """A manifest of discovered entities and their relationships."""
    entities: list = field(default_factory=list)  # list of Company dicts
    filings: list = field(default_factory=list)  # list of Filing dicts
    relationships: list = field(default_factory=list)  # list of Relationship dicts
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    query_params: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> Manifest:
        return _dataclass_from_dict(cls, data)

    @classmethod
    def from_json(cls, json_str: str) -> Manifest:
        return cls.from_dict(json.loads(json_str))


@dataclass
class Contract:
    """Represents a material contract from a filing."""
    contract_type: str  # "employment", "lease", "loan", "partnership", etc.
    counterparty: str
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    value: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    filing_accession: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> Contract:
        return _dataclass_from_dict(cls, data)

    @classmethod
    def from_json(cls, json_str: str) -> Contract:
        return cls.from_dict(json.loads(json_str))


@dataclass
class JobPosting:
    """Represents a job posting extracted from a filing or website."""
    title: str
    company_name: str
    location: Optional[str] = None
    job_type: Optional[str] = None  # "full-time", "contract", etc.
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    posted_date: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> JobPosting:
        return _dataclass_from_dict(cls, data)

    @classmethod
    def from_json(cls, json_str: str) -> JobPosting:
        return cls.from_dict(json.loads(json_str))


@dataclass
class FinancialRatio:
    name: str
    value: float
    description: Optional[str] = None
    benchmark: Optional[float] = None
    trend: Optional[str] = None
    
    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)
        
    @classmethod
    def from_dict(cls, data: dict) -> FinancialRatio:
        return _dataclass_from_dict(cls, data)


@dataclass
class FinancialSummary:
    company_name: str
    ticker: Optional[str] = None
    filing_date: Optional[str] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    warnings: list = field(default_factory=list)
    insights: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)
        
    @classmethod
    def from_dict(cls, data: dict) -> FinancialSummary:
        return _dataclass_from_dict(cls, data)


@dataclass
class RiskFactor:
    name: str
    score: float
    weight: float
    description: Optional[str] = None
    evidence: list = field(default_factory=list)
    
    def weighted_score(self) -> float:
        return self.score * self.weight
        
    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)
        
    @classmethod
    def from_dict(cls, data: dict) -> RiskFactor:
        return _dataclass_from_dict(cls, data)


@dataclass
class RiskAssessment:
    company_name: str
    ticker: Optional[str] = None
    cik: Optional[str] = None
    overall_score: Optional[float] = None
    risk_level: Optional[str] = None
    trend: Optional[str] = None
    recommendations: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)
        
    @classmethod
    def from_dict(cls, data: dict) -> RiskAssessment:
        return _dataclass_from_dict(cls, data)


@dataclass
class NetworkNode:
    id: str
    name: str
    node_type: str
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)
        
    @classmethod
    def from_dict(cls, data: dict) -> NetworkNode:
        return _dataclass_from_dict(cls, data)


@dataclass
class NetworkEdge:
    source: str
    target: str
    relationship_type: str
    confidence: Optional[float] = None
    
    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)
        
    @classmethod
    def from_dict(cls, data: dict) -> NetworkEdge:
        return _dataclass_from_dict(cls, data)


@dataclass
class NetworkAnalysis:
    company_name: str
    ticker: Optional[str] = None
    insights: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)
        
    @classmethod
    def from_dict(cls, data: dict) -> NetworkAnalysis:
        return _dataclass_from_dict(cls, data)

