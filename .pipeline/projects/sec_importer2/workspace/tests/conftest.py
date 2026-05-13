"""Test configuration and fixtures for SEC Importer 2."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Add workspace to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sec_importer.models import Base
from sec_importer.storage import init_db
from sec_importer.api.config import APIConfig as Settings


# ── Fixtures ───────────────────────────────────────────────────

@pytest.fixture
def db_path():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def session(db_path):
    """Create a test database session."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    sess = SessionLocal()
    yield sess
    sess.close()


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings()


@pytest.fixture
def sample_company():
    """Sample company data."""
    return {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "cik": "0000320193",
    }


@pytest.fixture
def sample_filing():
    """Sample filing data."""
    return {
        "ticker": "AAPL",
        "filing_type": "10-K",
        "filing_date": "2024-10-31",
        "accession_number": "0000320193-24-000123",
        "form_description": "Annual report [Section 13 and 15(d), not Shell Companies]",
        "document_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-10k.htm",
        "accepted_date": "2024-11-01T16:30:00",
        "fill_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/",
    }


@pytest.fixture
def sample_xbrl_data():
    """Sample XBRL data."""
    return {
        "income_statement": {
            "revenue": 383285000000,
            "gross_profit": 169148000000,
            "operating_income": 114301000000,
            "net_income": 93736000000,
        },
        "balance_sheet": {
            "total_assets": 352583000000,
            "total_liabilities": 290437000000,
            "total_equity": 62146000000,
        },
        "cash_flow": {
            "operating_cash_flow": 110543000000,
            "investing_cash_flow": -8891000000,
            "financing_cash_flow": -108488000000,
        },
    }


@pytest.fixture
def sample_html_sections():
    """Sample HTML sections."""
    return [
        {
            "section": "business",
            "title": "Part I — Business",
            "content": "<html><body>Apple designs...</body></html>",
        },
        {
            "section": "risk_factors",
            "title": "Risk Factors",
            "content": "<html><body>Risks include...</body></html>",
        },
    ]
