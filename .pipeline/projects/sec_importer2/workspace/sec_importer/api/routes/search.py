"""Search endpoint — full-text search across filings."""

from __future__ import annotations

import re
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sec_importer.models import Filing
from .config import APIConfig
from .dependencies import get_db
from .schemas import PaginatedResponse, SearchResponse

router = APIRouter()


def _compute_relevance(query: str, text: str) -> float:
    """Compute a simple relevance score for a query against text."""
    if not text:
        return 0.0

    query_lower = query.lower()
    text_lower = text.lower()

    score = 0.0

    # Exact phrase match gets highest score
    if query_lower in text_lower:
        score += 10.0

    # Word matches
    words = re.findall(r'\w+', query_lower)
    for word in words:
        if word in text_lower:
            score += 1.0

    return score


def _extract_snippet(text: str, query: str, max_length: int = 100) -> str:
    """Extract a relevant snippet from text around the query."""
    if not text or not query:
        return ""

    query_lower = query.lower()
    text_lower = text_lower

    idx = text_lower.find(query_lower)
    if idx == -1:
        # Fallback: just return first chunk
        return text[:max_length] + "..." if len(text) > max_length else text

    start = max(0, idx - 30)
    end = min(len(text), idx + len(query) + 30)
    snippet = text[start:end]

    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet


@router.get("/search", response_model=PaginatedResponse, tags=["Search"])
async def search_filings(
    db: Session = Depends(get_db),
    config: APIConfig = Depends(),
    q: str | None = Query(None, description="Search keyword"),
    filing_type: str | None = Query(None, description="Filter by form type"),
    ticker: str | None = Query(None, description="Filter by ticker"),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
):
    """Search filings by keyword.

    Searches across accession numbers, form descriptions, and other text fields.
    Results are ranked by relevance score.
    """
    if not q:
        return PaginatedResponse(items=[], total=0, limit=limit, offset=offset, has_more=False)

    # Build base query
    stmt = select(Filing).order_by(Filing.filing_date.desc())

    if filing_type:
        stmt = stmt.where(Filing.filing_type == filing_type.upper())
    if ticker:
        stmt = stmt.where(Filing.ticker == ticker.upper())
    if date_from:
        stmt = stmt.where(Filing.filing_date >= date_from)
    if date_to:
        stmt = stmt.where(Filing.filing_date <= date_to)

    # Get total count
    count_stmt = select(func.count(Filing.id))
    if filing_type:
        count_stmt = count_stmt.where(Filing.filing_type == filing_type.upper())
    if ticker:
        count_stmt = count_stmt.where(Filing.ticker == ticker.upper())
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

    # Compute relevance scores
    items = []
    for f in filings:
        # Combine searchable fields
        searchable = f"{f.accession_number or ''} {f.form_description or ''} {f.ticker}"
        score = _compute_relevance(q, searchable)

        snippet = _extract_snippet(searchable, q)

        items.append(SearchResponse(
            accession_number=f.accession_number or "",
            ticker=f.ticker,
            filing_type=f.filing_type,
            filing_date=f.filing_date or "",
            form_description=f.form_description,
            score=score,
            snippet=snippet,
        ))

    # Sort by relevance score descending
    items.sort(key=lambda x: x.score, reverse=True)

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )
