"""Company endpoints — lookup and list SEC companies."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sec_importer.models import Filing, Company
from ..config import APIConfig
from ..dependencies import get_db, get_config
from ..schemas import CompanyDetailResponse, CompanyResponse, FilingResponse, PaginatedResponse

router = APIRouter()


@router.get("/{ticker}", response_model=CompanyDetailResponse, tags=["Companies"])
async def get_company(
    ticker: str,
    db: Session = Depends(get_db),
    config: APIConfig = Depends(get_config),
):
    """Get company info by ticker symbol.

    Returns company details plus the 5 most recent filings.
    """
    ticker_upper = ticker.upper()

    # Get company info
    company = db.execute(
        select(Company).where(Company.ticker == ticker_upper)
    ).scalar_one_or_none()

    # Query filings for this ticker
    filings_query = (
        select(Filing)
        .where(Filing.ticker == ticker_upper)
        .order_by(Filing.filing_date.desc())
        .limit(5)
    )
    filings = db.execute(filings_query).scalars().all()

    # Get total count
    count_query = select(func.count(Filing.id)).where(Filing.ticker == ticker_upper)
    total = db.execute(count_query).scalar() or 0

    if not filings and not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ticker '{ticker_upper}' not found",
        )

    return CompanyDetailResponse(
        ticker=ticker_upper,
        name=company.name if company else f"Company {ticker_upper}",
        cik=company.cik if company else "",
        filing_count=total,
        recent_filings=[
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
        ],
    )


@router.get("", response_model=PaginatedResponse, tags=["Companies"])
async def list_companies(
    db: Session = Depends(get_db),
    config: APIConfig = Depends(get_config),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List all companies in the database.

    Returns a paginated list of unique tickers with their filing counts.
    """
    # Get unique tickers with filing counts
    subquery = (
        select(Filing.ticker, func.count(Filing.id).label("filing_count"))
        .group_by(Filing.ticker)
        .order_by(func.count(Filing.id).desc())
        .offset(offset)
        .limit(limit)
        .subquery()
    )

    rows = db.execute(select(subquery)).all()

    if not rows:
        return PaginatedResponse(items=[], total=0, limit=limit, offset=offset, has_more=False)

    # Get company names/ciks for the tickers
    tickers = [row[0] for row in rows]
    companies = db.execute(
        select(Company).where(Company.ticker.in_(tickers))
    ).scalars().all()
    company_map = {c.ticker: c for c in companies}

    items = [
        CompanyResponse(
            ticker=row[0],
            name=company_map.get(row[0]).name if row[0] in company_map else f"Company {row[0]}",
            cik=company_map.get(row[0]).cik if row[0] in company_map else "",
            filing_count=row[1],
        )
        for row in rows
    ]

    # Get total count
    total_query = select(func.count(func.distinct(Filing.ticker)))
    total = db.execute(total_query).scalar() or 0

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )
