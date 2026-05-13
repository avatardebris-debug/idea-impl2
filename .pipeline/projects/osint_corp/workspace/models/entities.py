"""Entity models for OSINT Corp."""

from __future__ import annotations

import json
from typing import Any, Optional


class Company:
    """Represents a company entity."""

    def __init__(
        self,
        name: str,
        ticker: Optional[str] = None,
        cik: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        industry: Optional[str] = None,
        registration_number: Optional[str] = None,
        incorporation_date: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.name = name
        self.ticker = ticker
        self.cik = cik
        self.jurisdiction = jurisdiction
        self.industry = industry
        self.registration_number = registration_number
        self.incorporation_date = incorporation_date
        self.status = status
        self.source = source
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ticker": self.ticker,
            "cik": self.cik,
            "jurisdiction": self.jurisdiction,
            "industry": self.industry,
            "registration_number": self.registration_number,
            "incorporation_date": self.incorporation_date,
            "status": self.status,
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Company":
        return cls(**{k: v for k, v in data.items() if k != "metadata"}, metadata=data.get("metadata", {}))

    def __repr__(self) -> str:
        return f"Company(name={self.name!r}, ticker={self.ticker!r}, cik={self.cik!r})"


class Filing:
    """Represents an SEC filing."""

    def __init__(
        self,
        company_name: str,
        ticker: Optional[str] = None,
        cik: Optional[str] = None,
        filing_type: str = "",
        filing_date: Optional[str] = None,
        accession_number: Optional[str] = None,
        url: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.company_name = company_name
        self.ticker = ticker
        self.cik = cik
        self.filing_type = filing_type
        self.filing_date = filing_date
        self.accession_number = accession_number
        self.url = url
        self.source = source
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "ticker": self.ticker,
            "cik": self.cik,
            "filing_type": self.filing_type,
            "filing_date": self.filing_date,
            "accession_number": self.accession_number,
            "url": self.url,
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Filing":
        return cls(**{k: v for k, v in data.items() if k != "metadata"}, metadata=data.get("metadata", {}))

    def __repr__(self) -> str:
        return f"Filing(company_name={self.company_name!r}, filing_type={self.filing_type!r}, accession={self.accession_number!r})"


class Manifest:
    """Serialized manifest of entities, filings, and relationships."""

    def __init__(
        self,
        entities: list[Company] | None = None,
        filings: list[Filing] | None = None,
        relationships: list[dict[str, Any]] | None = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.entities = entities or []
        self.filings = filings or []
        self.relationships = relationships or []
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "filings": [f.to_dict() for f in self.filings],
            "relationships": self.relationships,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Manifest":
        entities = [Company.from_dict(e) for e in data.get("entities", [])]
        filings = [Filing.from_dict(f) for f in data.get("filings", [])]
        relationships = data.get("relationships", [])
        metadata = data.get("metadata", {})
        return cls(entities=entities, filings=filings, relationships=relationships, metadata=metadata)

    @classmethod
    def from_json(cls, json_str: str) -> "Manifest":
        return cls.from_dict(json.loads(json_str))

    def __repr__(self) -> str:
        return f"Manifest(entities={len(self.entities)}, filings={len(self.filings)}, relationships={len(self.relationships)})"
