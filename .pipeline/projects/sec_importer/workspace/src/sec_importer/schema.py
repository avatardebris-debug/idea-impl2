"""SQLite schema definitions and database initialization for SEC Importer."""

import sqlite3
import os

# SQL DDL statements
CREATE_COMPANIES_TABLE = """
CREATE TABLE IF NOT EXISTS companies (
    cik TEXT PRIMARY KEY,
    name TEXT,
    ticker TEXT,
    sic TEXT,
    industry TEXT,
    state TEXT
);
"""

CREATE_FILINGS_TABLE = """
CREATE TABLE IF NOT EXISTS filings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    accession_no TEXT UNIQUE NOT NULL,
    cik TEXT NOT NULL,
    filing_type TEXT NOT NULL,
    filing_date TEXT,
    accepted_date TEXT,
    file_url TEXT,
    is_xbrl INTEGER DEFAULT 0,
    FOREIGN KEY (cik) REFERENCES companies(cik)
);
"""

CREATE_FILING_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS filing_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id INTEGER NOT NULL,
    accession_no TEXT NOT NULL,
    item_label TEXT,
    item_content TEXT,
    item_type TEXT,
    FOREIGN KEY (filing_id) REFERENCES filings(id)
);
"""

CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_filings_cik ON filings(cik);
CREATE INDEX IF NOT EXISTS idx_filings_type ON filings(filing_type);
CREATE INDEX IF NOT EXISTS idx_filings_date ON filings(filing_date);
CREATE INDEX IF NOT EXISTS idx_filings_accession ON filings(accession_no);
CREATE INDEX IF NOT EXISTS idx_filing_items_filing ON filing_items(filing_id);
CREATE INDEX IF NOT EXISTS idx_filing_items_accession ON filing_items(accession_no);
"""


def init_db(db_path: str = "sec_importer.db") -> sqlite3.Connection:
    """Initialize the SQLite database, creating all tables and indexes.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A connected sqlite3.Connection object.
    """
    # Ensure parent directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF;")

    cursor = conn.cursor()
    cursor.executescript(CREATE_COMPANIES_TABLE)
    cursor.executescript(CREATE_FILINGS_TABLE)
    cursor.executescript(CREATE_FILING_ITEMS_TABLE)
    cursor.executescript(CREATE_INDEXES)

    conn.commit()
    return conn
