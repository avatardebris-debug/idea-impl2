"""Base router with shared query helpers."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from sec_importer.storage import init_db, get_filing_content_data
from sec_importer.models import Company, Filing, FilingContent

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_session():
    """Yield a database session."""
    from ..storage import get_session
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def _paginate(items: list, offset: int, limit: int):
    """Slice items for pagination."""
    total = len(items)
    sliced = items[offset: offset + limit]
    return sliced, total
