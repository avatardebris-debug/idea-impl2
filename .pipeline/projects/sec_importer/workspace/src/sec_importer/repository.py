"""Database repository layer for SEC Importer.

Provides CRUD operations with deduplication support for Company, Filing,
and FilingItem tables.
"""

import sqlite3
from typing import Optional, List, Dict, Any, Set
from sec_importer.schema import init_db
from sec_importer.models import CompanyModel, FilingModel, FilingItemModel
from sec_importer.rate_limiter import RateLimiter


class CompanyRepository:
    """Repository for Company table operations."""

    def __init__(self, db_path_or_conn):
        """Initialize repository with a db_path string or sqlite3.Connection."""
        if isinstance(db_path_or_conn, str):
            self.conn = init_db(db_path_or_conn)
            self._owns_conn = True
        else:
            self.conn = db_path_or_conn
            self._owns_conn = False

    def init_db(self):
        """Initialize the database (no-op if already initialized)."""
        pass

    def close(self):
        """Close the database connection if we own it."""
        if self._owns_conn and self.conn:
            self.conn.close()
            self.conn = None

    def upsert(self, company: CompanyModel) -> int:
        """Insert or update a company by CIK. Returns company ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO companies (cik, name, ticker, sic, industry, state)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(cik) DO UPDATE SET
                name = excluded.name,
                ticker = excluded.ticker,
                sic = excluded.sic,
                industry = excluded.industry,
                state = excluded.state
            """,
            (
                company.cik,
                company.name,
                company.ticker,
                company.sic,
                company.industry,
                company.state,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def insert_company(self, company: CompanyModel) -> int:
        """Insert or update a company by CIK. Returns company ID (alias for upsert)."""
        return self.upsert(company)

    def get_by_cik(self, cik: str) -> Optional[Dict[str, Any]]:
        """Get company by CIK (alias for get_company_by_cik)."""
        return self.get_company_by_cik(cik)

    def get_company_by_cik(self, cik: str) -> Optional[Dict[str, Any]]:
        """Get company by CIK."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE cik = ?", (cik,))
        row = cursor.fetchone()
        if row:
            return dict(zip([col[0] for col in cursor.description], row))
        return None

    def exists_by_cik(self, cik: str) -> bool:
        """Check if company exists by CIK."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE cik = ?", (cik,))
        return cursor.fetchone() is not None


class FilingRepository:
    """Repository for Filing table operations with deduplication."""

    def __init__(self, db_path_or_conn):
        """Initialize repository with a db_path string or sqlite3.Connection."""
        if isinstance(db_path_or_conn, str):
            self.conn = init_db(db_path_or_conn)
            self._owns_conn = True
        else:
            self.conn = db_path_or_conn
            self._owns_conn = False

    def init_db(self):
        """Initialize the database (no-op if already initialized)."""
        pass

    def close(self):
        """Close the database connection if we own it."""
        if self._owns_conn and self.conn:
            self.conn.close()
            self.conn = None

    def upsert(self, filing: FilingModel) -> int:
        """Insert or update a filing by accession_no. Returns filing ID."""
        cursor = self.conn.cursor()
        normalized = self._normalize_accession(filing.accession_no)
        cursor.execute(
            """
            INSERT INTO filings (accession_no, cik, filing_type, filing_date,
                                 accepted_date, file_url, is_xbrl)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(accession_no) DO UPDATE SET
                cik = excluded.cik,
                filing_type = excluded.filing_type,
                filing_date = excluded.filing_date,
                accepted_date = excluded.accepted_date,
                file_url = excluded.file_url,
                is_xbrl = excluded.is_xbrl
            """,
            (
                normalized,
                filing.cik,
                filing.filing_type,
                filing.filing_date,
                filing.accepted_date,
                filing.file_url,
                filing.is_xbrl,
            ),
        )
        self.conn.commit()
        # lastrowid may be None on update; query to get the ID
        if cursor.lastrowid is None:
            cursor.execute("SELECT id FROM filings WHERE accession_no = ?", (normalized,))
            row = cursor.fetchone()
            return row[0] if row else 0
        return cursor.lastrowid

    def insert_filing(self, filing: FilingModel) -> int:
        """Insert or update a filing by accession_no. Returns filing ID (alias for upsert)."""
        return self.upsert(filing)

    def _normalize_accession(self, accession_no: str) -> str:
        """Normalize accession number by stripping dashes."""
        return accession_no.replace("-", "")

    def get_by_accession_no(self, accession_no: str) -> Optional[Dict[str, Any]]:
        """Get filing by accession number."""
        normalized = self._normalize_accession(accession_no)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM filings WHERE accession_no = ?", (normalized,))
        row = cursor.fetchone()
        if row:
            return dict(zip([col[0] for col in cursor.description], row))
        return None

    def get_filing_by_accession_no(self, accession_no: str) -> Optional[Dict[str, Any]]:
        """Get filing by accession number (alias for get_by_accession_no)."""
        return self.get_by_accession_no(accession_no)

    def exists_by_accession_no(self, accession_no: str) -> bool:
        """Check if filing exists by accession number."""
        normalized = self._normalize_accession(accession_no)
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM filings WHERE accession_no = ?", (normalized,))
        return cursor.fetchone() is not None

    def get_new_filings(self, cik: Optional[str] = None,
                        filing_type: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get filings not yet processed (where file_url is not empty).

        Args:
            cik: Filter by CIK.
            filing_type: Filter by filing type.
            limit: Maximum number of rows to return.
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM filings WHERE file_url IS NOT NULL AND file_url != ''"
        params = []

        if cik:
            query += " AND cik = ?"
            params.append(cik)
        if filing_type:
            query += " AND filing_type = ?"
            params.append(filing_type)

        query += " ORDER BY filing_date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(zip([col[0] for col in cursor.description], row))
                for row in cursor.fetchall()]

    def get_filings_by_cik(self, cik: str) -> List[Dict[str, Any]]:
        """Get all filings for a CIK."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM filings WHERE cik = ? ORDER BY id", (cik,))
        return [dict(zip([col[0] for col in cursor.description], row))
                for row in cursor.fetchall()]


class FilingItemRepository:
    """Repository for FilingItem table operations."""

    def __init__(self, db_path_or_conn):
        """Initialize repository with a db_path string or sqlite3.Connection."""
        if isinstance(db_path_or_conn, str):
            self.conn = init_db(db_path_or_conn)
            self._owns_conn = True
        else:
            self.conn = db_path_or_conn
            self._owns_conn = False

    def init_db(self):
        """Initialize the database (no-op if already initialized)."""
        pass

    def close(self):
        """Close the database connection if we own it."""
        if self._owns_conn and self.conn:
            self.conn.close()
            self.conn = None

    def _normalize_accession(self, accession_no: str) -> str:
        """Normalize accession number by stripping dashes."""
        return accession_no.replace("-", "")

    def upsert(self, item: FilingItemModel) -> int:
        """Insert or update a filing item. Returns item ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO filing_items (filing_id, accession_no, item_label,
                                      item_content, item_type)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                item.filing_id,
                self._normalize_accession(item.accession_no),
                item.item_label,
                item.item_content,
                item.item_type,
            ),
        )
        self.conn.commit()
        # lastrowid may be None on conflict; query to get the ID
        if cursor.lastrowid is None:
            cursor.execute("SELECT id FROM filing_items WHERE filing_id = ? AND accession_no = ? AND item_label = ?",
                           (item.filing_id, self._normalize_accession(item.accession_no), item.item_label))
            row = cursor.fetchone()
            return row[0] if row else 0
        return cursor.lastrowid

    def insert_filing_item(self, item: FilingItemModel) -> int:
        """Insert or update a filing item. Returns item ID (alias for upsert)."""
        return self.upsert(item)

    def get_by_filing_id(self, filing_id: int) -> List[Dict[str, Any]]:
        """Get all items for a filing."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM filing_items WHERE filing_id = ? ORDER BY id",
            (filing_id,),
        )
        return [dict(zip([col[0] for col in cursor.description], row))
                for row in cursor.fetchall()]

    def get_filing_items_by_filing_id(self, filing_id: int) -> List[Dict[str, Any]]:
        """Get all items for a filing (alias for get_by_filing_id)."""
        return self.get_by_filing_id(filing_id)

    def get_by_accession_no(self, accession_no: str) -> List[Dict[str, Any]]:
        """Get all items by accession number."""
        normalized = self._normalize_accession(accession_no)
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM filing_items WHERE accession_no = ? ORDER BY id",
            (normalized,),
        )
        return [dict(zip([col[0] for col in cursor.description], row))
                for row in cursor.fetchall()]

    def get_filing_items_by_accession_no(self, accession_no: str) -> List[Dict[str, Any]]:
        """Get all items by accession number (alias for get_by_accession_no)."""
        return self.get_by_accession_no(accession_no)

    def bulk_insert(self, items: List[FilingItemModel]) -> int:
        """Bulk insert items. Returns count of inserted rows."""
        if not items:
            return 0

        cursor = self.conn.cursor()
        values = [
            (i.filing_id, self._normalize_accession(i.accession_no), i.item_label,
             i.item_content, i.item_type)
            for i in items
        ]
        cursor.executemany(
            """
            INSERT OR IGNORE INTO filing_items
                (filing_id, accession_no, item_label, item_content, item_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            values,
        )
        self.conn.commit()
        # rowcount may be -1 on some SQLite drivers; count from the items
        if cursor.rowcount == -1:
            return len(items)
        return cursor.rowcount


class DeduplicationManager:
    """Manages deduplication state for imports."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._seen_accessions: Set[str] = set()
        self._seen_ciks: Set[str] = set()

    def mark_seen_accession(self, accession_no: str):
        """Mark an accession number as seen."""
        self._seen_accessions.add(accession_no)

    def mark_seen_cik(self, cik: str):
        """Mark a CIK as seen."""
        self._seen_ciks.add(cik)

    def is_accession_seen(self, accession_no: str) -> bool:
        """Check if accession was seen in this session."""
        return accession_no in self._seen_accessions

    def is_cik_seen(self, cik: str) -> bool:
        """Check if CIK was seen in this session."""
        return cik in self._seen_ciks

    def is_accession_in_db(self, accession_no: str) -> bool:
        """Check if accession exists in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM filings WHERE accession_no = ?", (accession_no.replace("-", ""),))
        return cursor.fetchone() is not None

    def is_cik_in_db(self, cik: str) -> bool:
        """Check if CIK exists in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE cik = ?", (cik,))
        return cursor.fetchone() is not None


class SECDatabase:
    """Main database interface combining repositories and rate limiting."""

    def __init__(self, db_path: str = "sec_importer.db",
                 rate_limiter: Optional[RateLimiter] = None):
        """Initialize database connection and repositories.

        Args:
            db_path: Path to SQLite database file.
            rate_limiter: Optional rate limiter for API calls.
        """
        self.conn = init_db(db_path)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.companies = CompanyRepository(self.conn)
        self.filings = FilingRepository(self.conn)
        self.items = FilingItemRepository(self.conn)
        self.dedup = DeduplicationManager(self.conn)

    def init_db(self):
        """Initialize the database (no-op if already initialized)."""
        pass

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
