"""SQLite database layer for Forensic Suite."""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional

logger = logging.getLogger("forensic.database")


class ForensicDatabase:
    """SQLite database for storing filings, companies, and analysis results."""

    def __init__(self, db_path: str = "forensic.db"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cik TEXT UNIQUE NOT NULL,
                    ticker TEXT,
                    company_name TEXT,
                    industry TEXT,
                    sic_code TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS filings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cik TEXT NOT NULL,
                    ticker TEXT,
                    accession_no TEXT UNIQUE NOT NULL,
                    filing_type TEXT,
                    filing_date TEXT,
                    period_end_date TEXT,
                    accepted_date TEXT,
                    url TEXT,
                    FOREIGN KEY (cik) REFERENCES companies(cik)
                );

                CREATE TABLE IF NOT EXISTS filing_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filing_id INTEGER,
                    accession_no TEXT,
                    item_number TEXT,
                    item_title TEXT,
                    item_content TEXT,
                    FOREIGN KEY (filing_id) REFERENCES filings(id)
                );

                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT,
                    cik TEXT,
                    accession_no TEXT,
                    fraud_risk_score REAL,
                    red_flags TEXT,
                    advanced_flags TEXT,
                    capital_flows TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        logger.info("Database initialized at %s", self.db_path)

    # ---- Company operations ----

    def upsert_company(self, company_info: Dict) -> None:
        """Insert or update a company record."""
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO companies (cik, ticker, company_name, industry, sic_code)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(cik) DO UPDATE SET
                       ticker=excluded.ticker,
                       company_name=excluded.company_name,
                       industry=excluded.industry,
                       sic_code=excluded.sic_code,
                       last_updated=CURRENT_TIMESTAMP""",
                (
                    company_info.get("cik"),
                    company_info.get("ticker"),
                    company_info.get("company_name"),
                    company_info.get("industry"),
                    company_info.get("sic_code"),
                ),
            )

    # ---- Filing operations ----

    def upsert_filing(self, filing_info: Dict) -> int:
        """Insert or update a filing record. Returns the filing id."""
        with self._connection() as conn:
            cursor = conn.execute(
                """INSERT INTO filings (cik, ticker, accession_no, filing_type,
                   filing_date, period_end_date, accepted_date, url)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(accession_no) DO UPDATE SET
                       filing_type=excluded.filing_type,
                       filing_date=excluded.filing_date,
                       period_end_date=excluded.period_end_date,
                       accepted_date=excluded.accepted_date,
                       url=excluded.url""",
                (
                    filing_info.get("cik"),
                    filing_info.get("ticker"),
                    filing_info.get("accession_no"),
                    filing_info.get("filing_type"),
                    filing_info.get("filing_date"),
                    filing_info.get("period_end_date"),
                    filing_info.get("accepted_date"),
                    filing_info.get("url"),
                ),
            )
            return cursor.lastrowid

    def add_filing_item(self, filing_id: int, item: Dict) -> None:
        """Add an item to a filing."""
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO filing_items (filing_id, accession_no, item_number,
                   item_title, item_content)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    filing_id,
                    item.get("accession_no"),
                    item.get("item_number"),
                    item.get("item_title"),
                    item.get("item_content"),
                ),
            )

    def get_filing_items(self, accession_no: str) -> List[Dict]:
        """Retrieve all items for a filing."""
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT fi.item_number, fi.item_title, fi.item_content
                   FROM filing_items fi
                   JOIN filings f ON fi.filing_id = f.id
                   WHERE f.accession_no = ?""",
                (accession_no,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # ---- Analysis operations ----

    def save_analysis(self, result: Dict) -> None:
        """Save an analysis result."""
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO analysis_results
                   (ticker, cik, accession_no, fraud_risk_score,
                    red_flags, advanced_flags, capital_flows)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    result.get("ticker"),
                    result.get("cik"),
                    result.get("accession_no"),
                    result.get("fraud_risk_score"),
                    json.dumps(result.get("red_flags", [])),
                    json.dumps(result.get("advanced_flags")),
                    json.dumps(result.get("capital_flows")),
                ),
            )

    def get_analysis_by_ticker(self, ticker: str) -> List[Dict]:
        """Retrieve all analysis results for a ticker."""
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM analysis_results WHERE ticker = ? ORDER BY created_at DESC""",
                (ticker,),
            )
            rows = cursor.fetchall()
            return [
                {
                    **dict(row),
                    "red_flags": json.loads(row["red_flags"]) if row["red_flags"] else [],
                    "advanced_flags": json.loads(row["advanced_flags"]) if row["advanced_flags"] else None,
                    "capital_flows": json.loads(row["capital_flows"]) if row["capital_flows"] else None,
                }
                for row in rows
            ]

    def get_latest_analysis(self, ticker: str) -> Optional[Dict]:
        """Retrieve the latest analysis result for a ticker."""
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM analysis_results WHERE ticker = ? ORDER BY created_at DESC LIMIT 1""",
                (ticker,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return {
                **dict(row),
                "red_flags": json.loads(row["red_flags"]) if row["red_flags"] else [],
                "advanced_flags": json.loads(row["advanced_flags"]) if row["advanced_flags"] else None,
                "capital_flows": json.loads(row["capital_flows"]) if row["capital_flows"] else None,
            }

    def get_company(self, cik: str) -> Optional[Dict]:
        """Retrieve company info by CIK."""
        with self._connection() as conn:
            cursor = conn.execute("SELECT * FROM companies WHERE cik = ?", (cik,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_company_by_ticker(self, ticker: str) -> Optional[Dict]:
        """Retrieve company info by ticker."""
        with self._connection() as conn:
            cursor = conn.execute("SELECT * FROM companies WHERE ticker = ?", (ticker,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_filings_by_cik(self, cik: str) -> List[Dict]:
        """Retrieve all filings for a CIK."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM filings WHERE cik = ? ORDER BY filing_date DESC",
                (cik,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_filings_by_ticker(self, ticker: str) -> List[Dict]:
        """Retrieve all filings for a ticker."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM filings WHERE ticker = ? ORDER BY filing_date DESC",
                (ticker,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_tickers(self) -> List[str]:
        """Retrieve all unique tickers."""
        with self._connection() as conn:
            cursor = conn.execute("SELECT DISTINCT ticker FROM filings WHERE ticker IS NOT NULL")
            return [row["ticker"] for row in cursor.fetchall()]

    def get_all_ciks(self) -> List[str]:
        """Retrieve all unique CIKs."""
        with self._connection() as conn:
            cursor = conn.execute("SELECT DISTINCT cik FROM filings")
            return [row["cik"] for row in cursor.fetchall()]

    def get_filings_count(self) -> int:
        """Get total number of filings."""
        with self._connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM filings")
            return cursor.fetchone()[0]

    def get_companies_count(self) -> int:
        """Get total number of companies."""
        with self._connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM companies")
            return cursor.fetchone()[0]

    def get_analysis_count(self) -> int:
        """Get total number of analysis results."""
        with self._connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM analysis_results")
            return cursor.fetchone()[0]

    def get_stats(self) -> Dict:
        """Get database statistics."""
        with self._connection() as conn:
            filings = conn.execute("SELECT COUNT(*) FROM filings").fetchone()[0]
            companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
            analyses = conn.execute("SELECT COUNT(*) FROM analysis_results").fetchone()[0]
            return {
                "filings": filings,
                "companies": companies,
                "analyses": analyses,
            }

    def get_high_risk_filings(self, threshold: float = 70) -> List[Dict]:
        """Retrieve filings with fraud risk scores above threshold."""
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT ar.*, f.filing_date, f.filing_type
                   FROM analysis_results ar
                   JOIN filings f ON ar.accession_no = f.accession_no
                   WHERE ar.fraud_risk_score >= ?
                   ORDER BY ar.fraud_risk_score DESC""",
                (threshold,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_risk_distribution(self) -> Dict:
        """Get distribution of risk scores."""
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT
                   COUNT(*) as total,
                   SUM(CASE WHEN fraud_risk_score < 30 THEN 1 ELSE 0 END) as low,
                   SUM(CASE WHEN fraud_risk_score >= 30 AND fraud_risk_score < 60 THEN 1 ELSE 0 END) as medium,
                   SUM(CASE WHEN fraud_risk_score >= 60 AND fraud_risk_score < 85 THEN 1 ELSE 0 END) as high,
                   SUM(CASE WHEN fraud_risk_score >= 85 THEN 1 ELSE 0 END) as critical
                   FROM analysis_results"""
            )
            row = cursor.fetchone()
            return {
                "total": row["total"],
                "low": row["low"],
                "medium": row["medium"],
                "high": row["high"],
                "critical": row["critical"],
            }
