"""Core data models for the forensic accounting suite.

Defines Pydantic models for the key entities used in cross-correlation
and anomaly detection: Company, CorporateRegistryEntry, ShippingManifest,
ProcurementRecord, GovernmentContract, and SEC_Filing.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------

class Company(BaseModel):
    """Represents a company entity with identifying fields."""

    name: str = Field(description="Legal or trading name of the company")
    registration_number: Optional[str] = Field(default=None, description="Company registration number")
    tax_id: Optional[str] = Field(default=None, description="Tax identification number")
    addresses: list[str] = Field(default_factory=list, description="List of known addresses")
    directors: list[str] = Field(default_factory=list, description="List of director names")
    officers: list[str] = Field(default_factory=list, description="List of officer names")
    country: Optional[str] = Field(default=None, description="Country of incorporation")
    industry: Optional[str] = Field(default=None, description="Industry / sector")
    status: Optional[str] = Field(default=None, description="Active / inactive / dissolved")
    aliases: list[str] = Field(default_factory=list, description="Known aliases / trade names")
    linked_entities: list[str] = Field(default_factory=list, description="Links to other entity IDs")

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> Company:
        return cls(**data)


# ---------------------------------------------------------------------------
# CorporateRegistryEntry
# ---------------------------------------------------------------------------

class CorporateRegistryEntry(BaseModel):
    """A single entry from a corporate registry."""

    company_name: str = Field(description="Registered company name")
    registration_number: str = Field(description="Unique registration number")
    incorporation_date: Optional[date] = Field(default=None)
    registered_address: Optional[str] = Field(default=None)
    directors: list[str] = Field(default_factory=list)
    officers: list[str] = Field(default_factory=list)
    company_type: Optional[str] = Field(default=None)
    status: str = Field(default="active")
    jurisdiction: Optional[str] = Field(default=None)
    share_capital: Optional[float] = Field(default=None)
    naics_code: Optional[str] = Field(default=None)
    source_db: Optional[str] = Field(default=None, description="Registry database name")

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> CorporateRegistryEntry:
        return cls(**data)


# ---------------------------------------------------------------------------
# ShippingManifest
# ---------------------------------------------------------------------------

class ShippingManifest(BaseModel):
    """A shipping manifest record."""

    manifest_id: str = Field(description="Unique manifest identifier")
    vessel_name: Optional[str] = Field(default=None)
    vessel_imo: Optional[str] = Field(default=None)
    shipper: Optional[str] = Field(default=None)
    consignee: Optional[str] = Field(default=None)
    origin_port: Optional[str] = Field(default=None)
    destination_port: Optional[str] = Field(default=None)
    departure_date: Optional[date] = Field(default=None)
    arrival_date: Optional[date] = Field(default=None)
    cargo_description: Optional[str] = Field(default=None)
    weight_kg: Optional[float] = Field(default=None)
    hs_code: Optional[str] = Field(default=None)
    declared_value: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default=None)
    sender_address: Optional[str] = Field(default=None)
    receiver_address: Optional[str] = Field(default=None)
    sender_company: Optional[str] = Field(default=None)
    receiver_company: Optional[str] = Field(default=None)
    source_db: Optional[str] = Field(default=None)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> ShippingManifest:
        return cls(**data)


# ---------------------------------------------------------------------------
# ProcurementRecord
# ---------------------------------------------------------------------------

class ProcurementRecord(BaseModel):
    """A government or corporate procurement / purchase record."""

    procurement_id: str = Field(description="Unique procurement identifier")
    contract_number: Optional[str] = Field(default=None)
    vendor_name: str = Field(description="Name of the vendor / contractor")
    vendor_registration_number: Optional[str] = Field(default=None)
    vendor_address: Optional[str] = Field(default=None)
    vendor_directors: list[str] = Field(default_factory=list)
    item_description: Optional[str] = Field(default=None)
    quantity: Optional[int] = Field(default=None)
    unit_price: Optional[float] = Field(default=None)
    total_value: float = Field(description="Total procurement value")
    currency: Optional[str] = Field(default=None)
    award_date: Optional[date] = Field(default=None)
    delivery_date: Optional[date] = Field(default=None)
    procuring_entity: Optional[str] = Field(default=None)
    procuring_entity_address: Optional[str] = Field(default=None)
    source_db: Optional[str] = Field(default=None)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> ProcurementRecord:
        return cls(**data)


# ---------------------------------------------------------------------------
# GovernmentContract
# ---------------------------------------------------------------------------

class GovernmentContract(BaseModel):
    """A government contract record."""

    contract_id: str = Field(description="Unique contract identifier")
    contract_number: Optional[str] = Field(default=None)
    agency: str = Field(description="Government agency")
    agency_address: Optional[str] = Field(default=None)
    contractor_name: str = Field(description="Contractor company name")
    contractor_registration_number: Optional[str] = Field(default=None)
    contractor_address: Optional[str] = Field(default=None)
    contractor_directors: list[str] = Field(default_factory=list)
    contract_value: float = Field(description="Total contract value")
    currency: Optional[str] = Field(default=None)
    award_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    description: Optional[str] = Field(default=None)
    contract_type: Optional[str] = Field(default=None)
    source_db: Optional[str] = Field(default=None)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> GovernmentContract:
        return cls(**data)


# ---------------------------------------------------------------------------
# SEC_Filing
# ---------------------------------------------------------------------------

class SEC_Filing(BaseModel):
    """An SEC filing record."""

    filing_id: str = Field(description="Unique SEC filing identifier")
    accession_number: Optional[str] = Field(default=None)
    company_name: str = Field(description="Filing company name")
    company_cik: Optional[str] = Field(default=None)
    filing_type: str = Field(description="SEC form type (10-K, 10-Q, 8-K, etc.)")
    filing_date: Optional[date] = Field(default=None)
    period_end_date: Optional[date] = Field(default=None)
    document_url: Optional[str] = Field(default=None)
    sic_code: Optional[str] = Field(default=None)
    industry: Optional[str] = Field(default=None)
    revenue: Optional[float] = Field(default=None)
    net_income: Optional[float] = Field(default=None)
    total_assets: Optional[float] = Field(default=None)
    total_liabilities: Optional[float] = Field(default=None)
    shareholders_equity: Optional[float] = Field(default=None)
    filing_text_summary: Optional[str] = Field(default=None)
    source_db: Optional[str] = Field(default=None)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> SEC_Filing:
        return cls(**data)
