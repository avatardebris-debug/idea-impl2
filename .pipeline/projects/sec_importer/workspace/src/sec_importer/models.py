"""Pydantic models for SEC Importer data validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CompanyModel(BaseModel):
    """Model representing a company filing record."""

    cik: str = Field(..., min_length=1, description="CIK number")
    name: Optional[str] = Field(None, description="Company name")
    ticker: Optional[str] = Field(None, description="Stock ticker symbol")
    sic: Optional[str] = Field(None, description="SIC code")
    industry: Optional[str] = Field(None, description="Industry classification")
    state: Optional[str] = Field(None, description="State of incorporation")

    @field_validator("cik")
    @classmethod
    def validate_cik(cls, v: str) -> str:
        """Validate CIK is numeric and zero-padded to 10 digits."""
        v = v.strip()
        if not v:
            raise ValueError("CIK cannot be empty")
        if not v.isdigit():
            raise ValueError("Invalid CIK")
        return v.zfill(10)


class FilingModel(BaseModel):
    """Model representing a SEC filing record."""

    accession_no: str = Field(..., min_length=1, description="Accession number")
    cik: str = Field(..., min_length=1, description="CIK number")
    filing_type: str = Field(..., min_length=1, description="Filing type (e.g. 10-K)")
    filing_date: Optional[str] = Field(None, description="Filing date (YYYY-MM-DD)")
    accepted_date: Optional[str] = Field(None, description="Accepted date/time")
    file_url: Optional[str] = Field(None, description="URL to the filing document")
    is_xbrl: bool = Field(False, description="Whether the filing is in XBRL format")

    @field_validator("accession_no")
    @classmethod
    def validate_accession_no(cls, v: str) -> str:
        """Validate accession number format and strip dashes."""
        v = v.strip()
        if not v:
            raise ValueError("Accession number cannot be empty")
        # Validate it's numeric (allowing dashes)
        check = v.replace("-", "")
        if not check.isdigit():
            raise ValueError("Invalid accession number")
        # Strip dashes for normalized storage
        return check

    @field_validator("cik")
    @classmethod
    def validate_cik(cls, v: str) -> str:
        """Validate CIK is numeric and zero-padded to 10 digits."""
        v = v.strip()
        if not v.isdigit():
            raise ValueError("CIK must be numeric")
        return v


class FilingItemModel(BaseModel):
    """Model representing a filing item (e.g. Item 1, Item 7)."""

    filing_id: Optional[int] = Field(None, description="Foreign key to filings table")
    accession_no: str = Field(..., min_length=1, description="Accession number")
    item_label: Optional[str] = Field(None, description="Item label (e.g. 'Item 1')")
    item_content: Optional[str] = Field(None, description="Item content text")
    item_type: str = Field("text", description="Item type/category")

    @field_validator("filing_id")
    @classmethod
    def validate_filing_id(cls, v: Optional[int]) -> Optional[int]:
        """Validate filing_id is greater than 0 if provided."""
        if v is not None and v <= 0:
            raise ValueError("filing_id must be greater than 0")
        return v

    @field_validator("accession_no")
    @classmethod
    def validate_accession_no(cls, v: str) -> str:
        """Validate accession number format and strip dashes."""
        v = v.strip()
        # Validate it's numeric (allowing dashes)
        check = v.replace("-", "")
        if not check.isdigit():
            raise ValueError("Accession number must be numeric")
        # Strip dashes for normalized storage
        return check


class XBRLFactModel(BaseModel):
    """Model representing an XBRL fact."""

    filing_id: int = Field(..., description="Foreign key to filings table")
    tag: str = Field(..., description="XBRL tag (e.g. 'us-gaap:Assets')")
    value: str = Field(..., description="Fact value as string")
    unit: Optional[str] = Field(None, description="Unit of measurement")

    @field_validator("value", mode="before")
    @classmethod
    def validate_value(cls, v) -> str:
        """Ensure value is stored as string."""
        return str(v)


class FilingSchemaConfig(BaseModel):
    """Configuration for XBRL schema parsing."""

    namespace: str = Field(..., description="XML namespace URI")
    prefix: str = Field(..., description="XML namespace prefix")

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        """Validate namespace is not empty."""
        if not v:
            raise ValueError("Namespace cannot be empty")
        return v
