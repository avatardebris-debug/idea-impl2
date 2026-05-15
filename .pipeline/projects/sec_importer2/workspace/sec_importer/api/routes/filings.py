"""Filing endpoints — list and retrieve individual filings."""

from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sec_importer.models import Filing, FilingContent
from ..config import APIConfig
from ..dependencies import get_db, get_config
from ..schemas import FilingFilter, FilingResponse, PaginatedResponse, FinancialResponse, FinancialMetric

router = APIRouter()


@router.get("", response_model=PaginatedResponse, tags=["Filings"])
async def list_filings(
    db: Session = Depends(get_db),
    config: APIConfig = Depends(get_config),
    ticker: str | None = Query(None, description="Filter by ticker"),
    filing_type: str | None = Query(None, description="Filter by form type (e.g., 10-K)"),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
):
    """List filings with optional filters.

    Supports filtering by ticker, form type, and date range.
    """
    stmt = select(Filing).order_by(Filing.filing_date.desc())

    if ticker:
        stmt = stmt.where(Filing.ticker == ticker.upper())
    if filing_type:
        stmt = stmt.where(Filing.filing_type == filing_type.upper())
    if date_from:
        stmt = stmt.where(Filing.filing_date >= date_from)
    if date_to:
        stmt = stmt.where(Filing.filing_date <= date_to)

    # Get total count
    count_stmt = select(func.count(Filing.id))
    if ticker:
        count_stmt = count_stmt.where(Filing.ticker == ticker.upper())
    if filing_type:
        count_stmt = count_stmt.where(Filing.filing_type == filing_type.upper())
    if date_from:
        count_stmt = count_stmt.where(Filing.filing_date >= date_from)
    if date_to:
        count_stmt = count_stmt.where(Filing.filing_date <= date_to)

    total = db.execute(count_stmt).scalar() or 0

    # Apply pagination
    stmt = stmt.offset(offset).limit(limit)
    filings = db.execute(stmt).scalars().all()

    if not filings:
        return PaginatedResponse(items=[], total=0, limit=limit, offset=offset, has_more=False)

    items = [
        FilingResponse(
            accession_number=f.accession_number or "",
            ticker=f.ticker,
            filing_type=f.filing_type,
            filing_date=f.filing_date or "",
            form_description=f.form_description,
            document_url=f.document_url,
            fill_url=f.fill_url,
            accepted_date=f.accepted_date,
        )
        for f in filings
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.get("/{accession}", response_model=FilingResponse, tags=["Filings"])
async def get_filing(
    accession: str,
    db: Session = Depends(get_db),
):
    """Get a specific filing by accession number."""
    filing = db.execute(
        select(Filing).where(Filing.accession_number == accession)
    ).scalar_one_or_none()

    if not filing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filing with accession number '{accession}' not found",
        )

    return FilingResponse(
        accession_number=filing.accession_number or "",
        ticker=filing.ticker,
        filing_type=filing.filing_type,
        filing_date=filing.filing_date or "",
        form_description=filing.form_description,
        document_url=filing.document_url,
        fill_url=filing.fill_url,
        accepted_date=filing.accepted_date,
    )


@router.get("/{accession_number}/financials", response_model=FinancialResponse, tags=["Financials"])
async def get_filing_financials(
    accession_number: str,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500, description="Max financial items"),
):
    """Get financial data (XBRL) for a specific filing."""
    filing = db.execute(
        select(Filing).where(Filing.accession_number == accession_number)
    ).scalar_one_or_none()

    if not filing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filing not found: {accession_number}",
        )

    # Try to get parsed XBRL content from FilingContent
    content = db.execute(
        select(FilingContent)
        .where(FilingContent.filing_id == filing.id)
        .where(FilingContent.content_type == "xbrl")
    ).scalar_one_or_none()

    metrics = []
    if content and content.content_data:
        try:
            content_data = json.loads(content.content_data)
            if isinstance(content_data, dict):
                for key, value in content_data.items():
                    if isinstance(value, dict):
                        metrics.append(FinancialMetric(
                            label=key,
                            value=value.get("value"),
                            unit=value.get("unit"),
                            period=value.get("period"),
                        ))
                    elif isinstance(value, (int, float)):
                        metrics.append(FinancialMetric(
                            label=key,
                            value=float(value),
                        ))
        except (json.JSONDecodeError, TypeError):
            pass

    return FinancialResponse(
        ticker=filing.ticker,
        period=filing.filing_date or "",
        filing_date=filing.filing_date,
        metrics=metrics,
    )
