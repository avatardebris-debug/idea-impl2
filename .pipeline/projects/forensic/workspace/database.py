"""Forensic database module using SQLite."""

import sqlite3
import os
from typing import Optional


class ForensicDatabase:
    """SQLite database for forensic filing data."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Connect to the database and create tables if needed."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        """Create the required tables."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                cik TEXT PRIMARY KEY,
                name TEXT,
                ticker TEXT,
                sic TEXT,
                industry TEXT,
                state TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS filings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accession_no TEXT UNIQUE,
                cik TEXT,
                filing_type TEXT,
                filing_date TEXT,
                accepted_date TEXT,
                file_url TEXT,
                FOREIGN KEY (cik) REFERENCES companies(cik)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS filing_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filing_id INTEGER,
                accession_no TEXT,
                item_label TEXT,
                item_content TEXT,
                item_type TEXT,
                FOREIGN KEY (filing_id) REFERENCES filings(id)
            )
        """)
        self.conn.commit()

    def _get_conn(self):
        """Get connection, auto-connecting if needed."""
        if self.conn is None:
            self.connect()
        return self.conn

    def upsert_company(self, company_info: dict):
        """Insert or update a company record."""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO companies (cik, name, ticker, sic, industry, state)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(cik) DO UPDATE SET
                name=excluded.name,
                ticker=excluded.ticker,
                sic=excluded.sic,
                industry=excluded.industry,
                state=excluded.state
        """, (
            company_info["cik"],
            company_info.get("name"),
            company_info.get("ticker"),
            company_info.get("sic"),
            company_info.get("industry"),
            company_info.get("state"),
        ))
        conn.commit()

    def upsert_filing(self, filing_data: dict):
        """Insert or update a filing record."""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO filings (accession_no, cik, filing_type, filing_date, accepted_date, file_url)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(accession_no) DO UPDATE SET
                cik=excluded.cik,
                filing_type=excluded.filing_type,
                filing_date=excluded.filing_date,
                accepted_date=excluded.accepted_date,
                file_url=excluded.file_url
        """, (
            filing_data["accession_no"],
            filing_data["cik"],
            filing_data.get("filing_type"),
            filing_data.get("filing_date"),
            filing_data.get("accepted_date"),
            filing_data.get("file_url"),
        ))
        conn.commit()

    def upsert_items(self, filing_id: int, accession_no: str, items):
        """Insert or update filing items."""
        conn = self._get_conn()
        for item in items:
            conn.execute("""
                INSERT INTO filing_items (filing_id, accession_no, item_label, item_content, item_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                filing_id,
                accession_no,
                item.item_label,
                item.item_content,
                item.item_type,
            ))
        conn.commit()

    def get_company_by_cik(self, cik: str) -> Optional[dict]:
        """Get a company by CIK."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM companies WHERE cik = ?", (cik,))
        row = cursor.fetchone()
        if row:
            return dict(zip(["cik", "name", "ticker", "sic", "industry", "state"], row))
        return None

    def get_latest_filing(self, ticker: str) -> Optional[dict]:
        """Get the latest filing for a ticker."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT f.accession_no, f.cik, f.filing_type, f.filing_date, f.accepted_date, f.file_url
            FROM filings f
            JOIN companies c ON f.cik = c.cik
            WHERE c.ticker = ?
            ORDER BY f.filing_date DESC
            LIMIT 1
        """, (ticker,))
        row = cursor.fetchone()
        if row:
            return dict(zip(["accession_no", "cik", "filing_type", "filing_date", "accepted_date", "file_url"], row))
        return None

    def get_filing_items(self, accession_no: str) -> list:
        """Get all items for a filing."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT item_label, item_content, item_type
            FROM filing_items
            WHERE accession_no = ?
        """, (accession_no,))
        return [dict(zip(["item_label", "item_content", "item_type"], row)) for row in cursor.fetchall()]

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
