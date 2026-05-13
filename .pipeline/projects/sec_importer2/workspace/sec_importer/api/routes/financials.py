"""Financial data endpoints: GET /financials/{ticker}/{period}."""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schemas import FinancialData
from .base import _get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/financials", tags=["financials"])


@router.get("/{ticker}/{period}", response_model=FinancialData)
def get_financials(ticker: str, period: str):
    """Return structured financial data for a ticker and period.

    Args:
        ticker: Company ticker symbol.
        period: Period identifier (e.g. '2024-12-31', '2024-Q4', '2024').
    """
    ticker_upper = ticker.upper()
    session: Session = next(_get_session())

    # Check company exists
    from ..models import Company, Filing, FilingContent
    company = session.execute(
        select(Company).where(Company.ticker == ticker_upper)
    ).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")

    # Find the most recent filing matching the period
    query = select(Filing).where(Filing.ticker == ticker_upper)
    if period:
        # Try matching filing_date or period in content
        query = query.where(Filing.filing_date == period)
    query = query.order_by(Filing.filing_date.desc()).limit(1)

    filing = session.execute(query).scalar_one_or_none()
    if not filing:
        # Try without period filter — return most recent
        filing = session.execute(
            select(Filing).where(Filing.ticker == ticker_upper)
            .order_by(Filing.filing_date.desc())
            .limit(1)
        ).scalar_one_or_none()

    if not filing:
        raise HTTPException(status_code=404, detail=f"No filings found for {ticker}")

    # Get XBRL content
    xbrl_data = session.execute(
        select(FilingContent).where(
            FilingContent.filing_id == filing.id,
            FilingContent.content_type == "xbrl"
        )
    ).scalar_one_or_none()

    income_statement = None
    balance_sheet = None
    cash_flow = None

    if xbrl_data and xbrl_data.content_data:
        try:
            data = json.loads(xbrl_data.content_data)
            income_statement = data.get("income_statement")
            balance_sheet = data.get("balance_sheet")
            cash_flow = data.get("cash_flow")
        except (json.JSONDecodeError, TypeError):
            pass

    return FinancialData(
        ticker=ticker_upper,
        period=period or filing.filing_date,
        filing_date=filing.filing_date,
        income_statement=income_statement,
        balance_sheet=balance_sheet,
        cash_flow=cash_flow,
    )
