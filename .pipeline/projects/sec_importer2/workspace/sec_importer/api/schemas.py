"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Response Schemas ──────────────────────────────────────────────


class CompanyResponse(BaseModel):
    """Company summary."""

    ticker: str = Field(..., description="Ticker symbol", examples=["AAPL"])
    name: str = Field(..., description="Company name", examples=["Apple Inc."])
    cik: str = Field(..., description="CIK number", examples=["0000320193"])
    filing_count: int = Field(0, description="Total filings on file")


class CompanyDetailResponse(BaseModel):
    """Company details with recent filings."""

    ticker: str
    name: str
    cik: str
    filing_count: int
    recent_filings: list["FilingResponse"] = Field(
        default_factory=list, description="Recent filings"
    )


class FilingResponse(BaseModel):
    """Filing metadata."""

    accession_number: str = Field(..., description="SEC accession number", examples=["0000320193-24-000006"])
    ticker: str
    filing_type: str = Field(..., description="Form type (10-K, 10-Q, etc.)", examples=["10-K"])
    filing_date: str = Field(..., description="Filing date (YYYY-MM-DD)")
    form_description: Optional[str] = Field(None, description="Form description")
    document_url: Optional[str] = Field(None, description="URL to the filing document")
    fill_url: Optional[str] = Field(None, description="URL to the filing index")
    accepted_date: Optional[str] = Field(None, description="Accepted date (YYYY-MM-DD)")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: list[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")
    has_more: bool = Field(..., description="Whether more pages exist")


class SearchResponse(BaseModel):
    """Search result."""

    accession_number: str
    ticker: str
    filing_type: str
    filing_date: str
    form_description: Optional[str]
    score: float = Field(0.0, description="Relevance score")
    snippet: Optional[str] = Field(None, description="Relevant text snippet")


class FinancialMetric(BaseModel):
    """A single financial metric."""

    label: str = Field(..., description="Metric label", examples=["Revenue"])
    value: Optional[float] = Field(None, description="Metric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    period: Optional[str] = Field(None, description="Reporting period")


class FinancialResponse(BaseModel):
    """Financial data for a specific period."""

    ticker: str
    period: str = Field(..., description="Period identifier", examples=["2024-Q4"])
    filing_date: Optional[str] = Field(None, description="Filing date")
    metrics: list[FinancialMetric] = Field(default_factory=list, description="Financial metrics")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Overall status", examples=["ok"])
    database: str = Field(..., description="Database status", examples=["connected"])
    version: str = Field(..., description="API version", examples=["0.1.0"])
    uptime_seconds: float = Field(0.0, description="Uptime in seconds")
    tickers_count: int = Field(0, description="Number of tickers")
    filings_count: int = Field(0, description="Number of filings")


# ── Request Schemas ──────────────────────────────────────────────


class FilingFilter(BaseModel):
    """Query parameters for filing filtering."""

    filing_type: Optional[str] = Field(None, description="Filter by form type (e.g., 10-K)")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    limit: int = Field(50, ge=1, le=500, description="Page size")
    offset: int = Field(0, ge=0, description="Page offset")


class SearchFilter(BaseModel):
    """Query parameters for search."""

    q: Optional[str] = Field(None, description="Search keyword")
    filing_type: Optional[str] = Field(None, description="Filter by form type")
    ticker: Optional[str] = Field(None, description="Filter by ticker")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    limit: int = Field(50, ge=1, le=500, description="Page size")


# ── Error Schemas ──────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str = Field(..., description="Error description", examples=["Company not found"])
    status_code: int = Field(..., description="HTTP status code", examples=[404])


# ── Scheduler Schemas ──────────────────────────────────────────────


class SchedulerConfigResponse(BaseModel):
    """Scheduler configuration."""

    mode: str
    sync_hour: int
    sync_minute: int
    timezone: str
    cron_expression: str
    run_once: bool
    tickers_file: str
    limit_per_ticker: int
    db_path: str


class SchedulerRunResponse(BaseModel):
    """Scheduler run result."""

    success: bool
    summary: dict = Field(default_factory=dict)
    error: Optional[str] = None
