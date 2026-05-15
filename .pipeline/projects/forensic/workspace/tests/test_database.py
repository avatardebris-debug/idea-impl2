"""Tests for Forensic Suite database module."""

import sys
import os
import pytest
import tempfile
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from forensic.database import ForensicDatabase


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    db = ForensicDatabase(db_path)
    yield db
    db.close()
    os.unlink(db_path)


class TestDatabase:
    def test_init_creates_tables(self, db):
        """Test that initialization creates the required tables."""
        # Check if tables exist
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = [t[0] for t in tables]
        assert "companies" in table_names
        assert "fraud_scores" in table_names
        assert "red_flags" in table_names
        assert "capital_flows" in table_names

    def test_insert_company(self, db):
        """Test inserting a company."""
        company = {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "cik": "0000320193",
            "sic": "3571",
            "industry": "Computer Manufacturing",
            "state": "CA",
        }
        db.insert_company(company)

        result = db.execute("SELECT * FROM companies WHERE ticker = ?", ("AAPL",)).fetchone()
        assert result is not None
        assert result[1] == "Apple Inc."
        assert result[2] == "AAPL"

    def test_insert_fraud_score(self, db):
        """Test inserting a fraud score."""
        score = {
            "ticker": "AAPL",
            "fraud_score": 75.5,
            "risk_level": "high",
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_fraud_score(score)

        result = db.execute("SELECT * FROM fraud_scores WHERE ticker = ?", ("AAPL",)).fetchone()
        assert result is not None
        assert result[1] == "AAPL"
        assert result[5] == 75.5

    def test_insert_red_flag(self, db):
        """Test inserting a red flag."""
        flag = {
            "ticker": "AAPL",
            "category": "accounting",
            "severity": "high",
            "description": "Revenue recognition issues",
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_red_flag(flag)

        result = db.execute("SELECT * FROM red_flags WHERE ticker = ?", ("AAPL",)).fetchone()
        assert result is not None
        assert result[1] == "AAPL"
        assert result[5] == "accounting"

    def test_insert_capital_flow(self, db):
        """Test inserting a capital flow."""
        flow = {
            "ticker": "AAPL",
            "period_label": "2023-Q1",
            "operating_cash_flow": 100.0,
            "investing_cash_flow": -50.0,
            "financing_cash_flow": -30.0,
            "net_change_in_cash": 20.0,
            "capital_expenditures": 40.0,
            "free_cash_flow": 60.0,
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_capital_flow(flow)

        result = db.execute("SELECT * FROM capital_flows WHERE ticker = ?", ("AAPL",)).fetchone()
        assert result is not None
        assert result[1] == "AAPL"
        assert result[5] == "2023-Q1"

    def test_get_companies(self, db):
        """Test getting all companies."""
        company1 = {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "cik": "0000320193",
            "sic": "3571",
            "industry": "Computer Manufacturing",
            "state": "CA",
        }
        company2 = {
            "ticker": "GOOGL",
            "name": "Alphabet Inc.",
            "cik": "0001652044",
            "sic": "7370",
            "industry": "Services-Computer Programming",
            "state": "CA",
        }
        db.insert_company(company1)
        db.insert_company(company2)

        companies = db.get_companies()
        assert len(companies) == 2

    def test_get_companies_by_ticker(self, db):
        """Test getting companies by ticker."""
        company = {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "cik": "0000320193",
            "sic": "3571",
            "industry": "Computer Manufacturing",
            "state": "CA",
        }
        db.insert_company(company)

        companies = db.get_companies(ticker="AAPL")
        assert len(companies) == 1
        assert companies[0]["ticker"] == "AAPL"

    def test_get_fraud_scores(self, db):
        """Test getting fraud scores."""
        score = {
            "ticker": "AAPL",
            "fraud_score": 75.5,
            "risk_level": "high",
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_fraud_score(score)

        scores = db.get_fraud_scores()
        assert len(scores) == 1
        assert scores[0]["ticker"] == "AAPL"

    def test_get_fraud_scores_by_ticker(self, db):
        """Test getting fraud scores by ticker."""
        score = {
            "ticker": "AAPL",
            "fraud_score": 75.5,
            "risk_level": "high",
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_fraud_score(score)

        scores = db.get_fraud_scores(ticker="AAPL")
        assert len(scores) == 1
        assert scores[0]["ticker"] == "AAPL"

    def test_get_red_flags(self, db):
        """Test getting red flags."""
        flag = {
            "ticker": "AAPL",
            "category": "accounting",
            "severity": "high",
            "description": "Revenue recognition issues",
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_red_flag(flag)

        flags = db.get_red_flags()
        assert len(flags) == 1
        assert flags[0]["ticker"] == "AAPL"

    def test_get_red_flags_by_ticker(self, db):
        """Test getting red flags by ticker."""
        flag = {
            "ticker": "AAPL",
            "category": "accounting",
            "severity": "high",
            "description": "Revenue recognition issues",
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_red_flag(flag)

        flags = db.get_red_flags(ticker="AAPL")
        assert len(flags) == 1
        assert flags[0]["ticker"] == "AAPL"

    def test_get_capital_flows(self, db):
        """Test getting capital flows."""
        flow = {
            "ticker": "AAPL",
            "period_label": "2023-Q1",
            "operating_cash_flow": 100.0,
            "investing_cash_flow": -50.0,
            "financing_cash_flow": -30.0,
            "net_change_in_cash": 20.0,
            "capital_expenditures": 40.0,
            "free_cash_flow": 60.0,
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_capital_flow(flow)

        flows = db.get_capital_flows()
        assert len(flows) == 1
        assert flows[0]["ticker"] == "AAPL"

    def test_get_capital_flows_by_ticker(self, db):
        """Test getting capital flows by ticker."""
        flow = {
            "ticker": "AAPL",
            "period_label": "2023-Q1",
            "operating_cash_flow": 100.0,
            "investing_cash_flow": -50.0,
            "financing_cash_flow": -30.0,
            "net_change_in_cash": 20.0,
            "capital_expenditures": 40.0,
            "free_cash_flow": 60.0,
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_capital_flow(flow)

        flows = db.get_capital_flows(ticker="AAPL")
        assert len(flows) == 1
        assert flows[0]["ticker"] == "AAPL"
