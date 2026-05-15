"""sec_importer database stub for the forensic suite.

Provides a minimal SECDatabase class so that the forensic project can
import without requiring the full sec_importer project to be installed.
The forensic suite uses its own ForensicDatabase for all real persistence;
this stub only satisfies the import chain.
"""

from __future__ import annotations

from typing import Any, Optional


class SECDatabase:
    """Stub SEC database for import compatibility."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path

    def __enter__(self) -> "SECDatabase":
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    @property
    def companies(self) -> "_CompaniesStub":
        return _CompaniesStub()

    @property
    def filings(self) -> "_FilingsStub":
        return _FilingsStub()

    @property
    def items(self) -> "_ItemsStub":
        return _ItemsStub()


class _CompaniesStub:
    def resolve_ticker(self, ticker: str) -> Optional[str]:
        return None

    def get_or_fetch_company(self, cik: str) -> Optional[dict]:
        return None

    def upsert_company(self, company_info: dict) -> None:
        pass


class _FilingsStub:
    def get_filings_by_cik(self, cik: str) -> list:
        return []

    def fetch_latest_10k(self, cik: str) -> None:
        return None

    def upsert_filing(self, filing: Any) -> None:
        pass

    def download_filing(self, filing: Any) -> Optional[str]:
        return None


class _ItemsStub:
    def upsert_items(self, filing_id: int, accession_no: str, items: list) -> None:
        pass
