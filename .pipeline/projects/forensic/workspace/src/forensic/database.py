"""Forensic database - SQLite repository for forensic data."""

import sqlite3
from typing import List, Optional, Dict, Any
from forensic.config import get_config
from sec_importer.models import FilingItemModel


class ForensicDatabase:
    """SQLite database for forensic analysis data."""

    def __init__(self, db_path: Optional[str] = None):
        config = get_config()
        self.db_path = db_path or config.db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> "ForensicDatabase":
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        # Initialize schema on the existing connection
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS companies (
                cik TEXT PRIMARY KEY,
                name TEXT,
                ticker TEXT,
                sic TEXT,
                industry TEXT,
                state TEXT
            );
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
            CREATE TABLE IF NOT EXISTS filing_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filing_id INTEGER NOT NULL,
                accession_no TEXT NOT NULL,
                item_label TEXT,
                item_content TEXT,
                item_type TEXT DEFAULT 'text',
                FOREIGN KEY (filing_id) REFERENCES filings(id)
            );
            CREATE TABLE IF NOT EXISTS fraud_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                cik TEXT,
                filing_date TEXT NOT NULL,
                accession_no TEXT NOT NULL,
                fraud_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                FOREIGN KEY (cik) REFERENCES companies(cik)
            );
            CREATE TABLE IF NOT EXISTS red_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                cik TEXT,
                filing_date TEXT NOT NULL,
                accession_no TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                evidence TEXT,
                FOREIGN KEY (cik) REFERENCES companies(cik)
            );
            CREATE TABLE IF NOT EXISTS capital_flows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                cik TEXT,
                filing_date TEXT NOT NULL,
                accession_no TEXT NOT NULL,
                period_label TEXT NOT NULL,
                operating_cash_flow REAL,
                investing_cash_flow REAL,
                financing_cash_flow REAL,
                net_change_in_cash REAL,
                capital_expenditures REAL,
                free_cash_flow REAL,
                FOREIGN KEY (cik) REFERENCES companies(cik)
            );
            CREATE INDEX IF NOT EXISTS idx_filings_cik ON filings(cik);
            CREATE INDEX IF NOT EXISTS idx_filings_type ON filings(filing_type);
            CREATE INDEX IF NOT EXISTS idx_filings_date ON filings(filing_date);
            CREATE INDEX IF NOT EXISTS idx_filings_accession ON filings(accession_no);
            CREATE INDEX IF NOT EXISTS idx_fraud_scores_ticker ON fraud_scores(ticker);
            CREATE INDEX IF NOT EXISTS idx_fraud_scores_date ON fraud_scores(filing_date);
            CREATE INDEX IF NOT EXISTS idx_red_flags_ticker ON red_flags(ticker);
            CREATE INDEX IF NOT EXISTS idx_red_flags_severity ON red_flags(severity);
            CREATE INDEX IF NOT EXISTS idx_capital_flows_ticker ON capital_flows(ticker);
            CREATE INDEX IF NOT EXISTS idx_capital_flows_date ON capital_flows(filing_date);
            -- Monitoring results table
            CREATE TABLE IF NOT EXISTS monitoring_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                filing_date TEXT NOT NULL,
                score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                checked_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );
            CREATE INDEX IF NOT EXISTS idx_monitoring_results_ticker ON monitoring_results(ticker);
            CREATE INDEX IF NOT EXISTS idx_monitoring_results_checked_at ON monitoring_results(checked_at);
            -- Alerts table
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                flags TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );
            CREATE INDEX IF NOT EXISTS idx_alerts_ticker ON alerts(ticker);
            CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
            """
        )
        return self

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if not self.conn:
            self.connect()
        return self.conn

    def upsert_company(self, company_info: Dict[str, str]) -> None:
        """Insert or update company data."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO companies (cik, name, ticker, sic, industry, state)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                company_info.get("cik", ""),
                company_info.get("name", ""),
                company_info.get("ticker", ""),
                company_info.get("sic", ""),
                company_info.get("industry", ""),
                company_info.get("state", ""),
            ),
        )
        conn.commit()

    def insert_company(self, company_info: Dict[str, str]) -> None:
        """Insert a single company record."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO companies (cik, name, ticker, sic, industry, state)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                company_info.get("cik", ""),
                company_info.get("name", ""),
                company_info.get("ticker", ""),
                company_info.get("sic", ""),
                company_info.get("industry", ""),
                company_info.get("state", ""),
            ),
        )
        conn.commit()

    def upsert_filing(self, filing_data: Dict[str, str]) -> None:
        """Insert or update filing data."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO filings (accession_no, cik, filing_type, filing_date, accepted_date, file_url, is_xbrl)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                filing_data.get("accession_no", ""),
                filing_data.get("cik", ""),
                filing_data.get("filing_type", ""),
                filing_data.get("filing_date", ""),
                filing_data.get("accepted_date", ""),
                filing_data.get("file_url", ""),
                0,
            ),
        )
        conn.commit()

    def upsert_items(self, filing_id: int, accession_no: str, items: List[FilingItemModel]) -> None:
        """Insert or update filing items."""
        conn = self._get_conn()
        cursor = conn.cursor()
        for item in items:
            cursor.execute(
                """INSERT OR REPLACE INTO filing_items (filing_id, accession_no, item_label, item_content, item_type)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    filing_id,
                    accession_no,
                    item.item_label,
                    item.item_content,
                    item.item_type,
                ),
            )
        conn.commit()

    def get_latest_filing(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get the latest filing for a ticker."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT f.*, c.ticker
               FROM filings f
               JOIN companies c ON f.cik = c.cik
               WHERE c.ticker = ?
               ORDER BY f.filing_date DESC
               LIMIT 1""",
            (ticker,),
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_filing_items(self, accession_no: str) -> List[Dict[str, Any]]:
        """Get all items for a filing."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM filing_items WHERE accession_no = ?",
            (accession_no,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_company_by_cik(self, cik: str) -> Optional[Dict[str, Any]]:
        """Get company by CIK."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE cik = ?", (cik,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    # ---- Fraud scores ----

    def upsert_fraud_score(self, data: Dict[str, Any]) -> None:
        """Insert or update a fraud score record."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO fraud_scores (ticker, cik, filing_date, accession_no, fraud_score, risk_level)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                data.get("ticker", ""),
                data.get("cik") or None,
                data.get("filing_date", ""),
                data.get("accession_no", ""),
                data.get("fraud_score", 0),
                data.get("risk_level", "low"),
            ),
        )
        conn.commit()

    def insert_fraud_score(self, data: Dict[str, Any]) -> None:
        """Insert a single fraud score record."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO fraud_scores (ticker, cik, filing_date, accession_no, fraud_score, risk_level)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                data.get("ticker", ""),
                data.get("cik") or None,
                data.get("filing_date", ""),
                data.get("accession_no", ""),
                data.get("fraud_score", 0),
                data.get("risk_level", "low"),
            ),
        )
        conn.commit()

    def get_fraud_scores(
        self,
        ticker: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get fraud scores with optional filters."""
        conn = self._get_conn()
        query = "SELECT * FROM fraud_scores WHERE 1=1"
        params: list = []
        if ticker:
            query += " AND ticker = ?"
            params.append(ticker)
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)
        query += " ORDER BY filing_date DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    # ---- Red flags ----

    def upsert_red_flags(self, flags: List[Dict[str, Any]]) -> None:
        """Insert red flags."""
        conn = self._get_conn()
        for flag in flags:
            conn.execute(
                """INSERT INTO red_flags (ticker, cik, filing_date, accession_no, category, description, severity, evidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    flag.get("ticker", ""),
                    flag.get("cik") or None,
                    flag.get("filing_date", ""),
                    flag.get("accession_no", ""),
                    flag.get("category", ""),
                    flag.get("description", ""),
                    flag.get("severity", ""),
                    flag.get("evidence"),
                ),
            )
        conn.commit()

    def insert_red_flag(self, flag: Dict[str, Any]) -> None:
        """Insert a single red flag record."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO red_flags (ticker, cik, filing_date, accession_no, category, description, severity, evidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                flag.get("ticker", ""),
                flag.get("cik") or None,
                flag.get("filing_date", ""),
                flag.get("accession_no", ""),
                flag.get("category", ""),
                flag.get("description", ""),
                flag.get("severity", ""),
                flag.get("evidence"),
            ),
        )
        conn.commit()

    def get_red_flags(
        self,
        ticker: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Get red flags with optional filters."""
        conn = self._get_conn()
        query = "SELECT * FROM red_flags WHERE 1=1"
        params: list = []
        if ticker:
            query += " AND ticker = ?"
            params.append(ticker)
        if category:
            query += " AND category = ?"
            params.append(category)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        query += " ORDER BY filing_date DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    # ---- Capital flows ----

    def upsert_capital_flows(self, flows: List[Dict[str, Any]]) -> None:
        """Insert capital flow records."""
        conn = self._get_conn()
        for flow in flows:
            conn.execute(
                """INSERT INTO capital_flows (ticker, cik, filing_date, accession_no, period_label,
                   operating_cash_flow, investing_cash_flow, financing_cash_flow,
                   net_change_in_cash, capital_expenditures, free_cash_flow)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    flow.get("ticker", ""),
                    flow.get("cik") or None,
                    flow.get("filing_date", ""),
                    flow.get("accession_no", ""),
                    flow.get("period_label", ""),
                    flow.get("operating_cash_flow"),
                    flow.get("investing_cash_flow"),
                    flow.get("financing_cash_flow"),
                    flow.get("net_change_in_cash"),
                    flow.get("capital_expenditures"),
                    flow.get("free_cash_flow"),
                ),
            )
        conn.commit()

    def insert_capital_flow(self, flow: Dict[str, Any]) -> None:
        """Insert a single capital flow record."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO capital_flows (ticker, cik, filing_date, accession_no, period_label,
               operating_cash_flow, investing_cash_flow, financing_cash_flow,
               net_change_in_cash, capital_expenditures, free_cash_flow)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                flow.get("ticker", ""),
                flow.get("cik") or None,
                flow.get("filing_date", ""),
                flow.get("accession_no", ""),
                flow.get("period_label", ""),
                flow.get("operating_cash_flow"),
                flow.get("investing_cash_flow"),
                flow.get("financing_cash_flow"),
                flow.get("net_change_in_cash"),
                flow.get("capital_expenditures"),
                flow.get("free_cash_flow"),
            ),
        )
        conn.commit()

    def get_capital_flows(
        self,
        ticker: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get capital flow records."""
        conn = self._get_conn()
        query = "SELECT * FROM capital_flows WHERE 1=1"
        params: list = []
        if ticker:
            query += " AND ticker = ?"
            params.append(ticker)
        query += " ORDER BY filing_date DESC, period_label ASC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    # ---- Dashboard summary ----

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the dashboard."""
        conn = self._get_conn()
        total_filings = conn.execute("SELECT COUNT(*) FROM filings").fetchone()[0]
        total_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        total_fraud_scores = conn.execute("SELECT COUNT(*) FROM fraud_scores").fetchone()[0]
        total_red_flags = conn.execute("SELECT COUNT(*) FROM red_flags").fetchone()[0]
        total_capital_flows = conn.execute("SELECT COUNT(*) FROM capital_flows").fetchone()[0]

        # Risk level distribution
        risk_dist = conn.execute(
            "SELECT risk_level, COUNT(*) as cnt FROM fraud_scores GROUP BY risk_level"
        ).fetchall()
        risk_distribution = {r["risk_level"]: r["cnt"] for r in risk_dist}

        # Category distribution
        cat_dist = conn.execute(
            "SELECT category, COUNT(*) as cnt FROM red_flags GROUP BY category"
        ).fetchall()
        category_distribution = {r["category"]: r["cnt"] for r in cat_dist}

        # Recent fraud scores (last 30 days)
        recent_scores = conn.execute(
            "SELECT ticker, fraud_score, risk_level, filing_date FROM fraud_scores "
            "WHERE filing_date >= date('now', '-30 days') ORDER BY filing_date DESC LIMIT 20"
        ).fetchall()

        # Top red flag categories
        top_flags = conn.execute(
            "SELECT category, severity, COUNT(*) as cnt FROM red_flags GROUP BY category, severity "
            "ORDER BY cnt DESC LIMIT 10"
        ).fetchall()

        # Capital flow trends (latest per ticker)
        capital_flow_trends = conn.execute(
            """SELECT cf.ticker, cf.period_label, cf.operating_cash_flow, cf.investing_cash_flow,
                      cf.financing_cash_flow, cf.free_cash_flow
               FROM capital_flows cf
               INNER JOIN (
                   SELECT ticker, MAX(filing_date) as max_date
                   FROM capital_flows
                   GROUP BY ticker
               ) latest ON cf.ticker = latest.ticker AND cf.filing_date = latest.max_date
               ORDER BY cf.ticker
               LIMIT 20"""
        ).fetchall()
        capital_flow_trends = [dict(r) for r in capital_flow_trends]

        return {
            "total_filings": total_filings,
            "total_companies": total_companies,
            "total_fraud_scores": total_fraud_scores,
            "total_red_flags": total_red_flags,
            "total_capital_flows": total_capital_flows,
            "risk_distribution": risk_distribution,
            "category_distribution": category_distribution,
            "recent_scores": [dict(r) for r in recent_scores],
            "top_flags": [dict(r) for r in top_flags],
            "capital_flow_trends": capital_flow_trends,
        }

    # ---- Monitoring results ----

    def get_last_monitoring_time(self, ticker: str) -> Optional[str]:
        """Get the last monitoring check time for a ticker."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT checked_at FROM monitoring_results WHERE ticker = ? ORDER BY checked_at DESC LIMIT 1",
            (ticker,),
        ).fetchone()
        return row[0] if row else None

    def record_monitoring_result(
        self, ticker: str, filing_date: str, score: float, risk_level: str
    ) -> None:
        """Record a monitoring check result."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO monitoring_results (ticker, filing_date, score, risk_level, checked_at)
               VALUES (?, ?, ?, ?, datetime('now'))""",
            (ticker, filing_date, score, risk_level),
        )
        conn.commit()

    def get_recent_alerts(self, ticker: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent alerts for a ticker within the last N hours."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM alerts WHERE ticker = ? AND created_at >= datetime('now', ?) ORDER BY created_at DESC",
            (ticker, f"-{hours} hours"),
        ).fetchall()
        return [dict(r) for r in rows]

    def insert_alert(
        self, ticker: str, score: float, risk_level: str, flags: List[str]
    ) -> None:
        """Insert an alert record."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO alerts (ticker, score, risk_level, flags, created_at)
               VALUES (?, ?, ?, ?, datetime('now'))""",
            (ticker, score, risk_level, ",".join(flags)),
        )
        conn.commit()
