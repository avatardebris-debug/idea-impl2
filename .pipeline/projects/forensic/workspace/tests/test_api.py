"""Tests for Forensic Suite API module."""

import sys
import os
import pytest
import tempfile

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from forensic.database import ForensicDatabase
from forensic.api import create_api


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    db = ForensicDatabase(db_path)
    yield db
    db.close()
    os.unlink(db_path)


@pytest.fixture
def app(db):
    """Create a Flask app for testing."""
    from forensic.web import create_app
    app = create_app(db=db)
    app.config["TESTING"] = True
    return app


class TestAPI:
    def test_get_companies(self, app, db):
        """Test the get_companies endpoint."""
        company = {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "cik": "0000320193",
            "sic": "3571",
            "industry": "Computer Manufacturing",
            "state": "CA",
        }
        db.insert_company(company)

        with app.test_client() as client:
            response = client.get("/api/companies")
            assert response.status_code == 200
            data = response.get_json()
            assert "companies" in data
            assert len(data["companies"]) == 1
            assert data["companies"][0]["ticker"] == "AAPL"

    def test_get_companies_by_ticker(self, app, db):
        """Test the get_companies endpoint with ticker filter."""
        company = {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "cik": "0000320193",
            "sic": "3571",
            "industry": "Computer Manufacturing",
            "state": "CA",
        }
        db.insert_company(company)

        with app.test_client() as client:
            response = client.get("/api/companies?ticker=AAPL")
            assert response.status_code == 200
            data = response.get_json()
            assert "companies" in data
            assert len(data["companies"]) == 1
            assert data["companies"][0]["ticker"] == "AAPL"

    def test_get_fraud_scores(self, app, db):
        """Test the get_fraud_scores endpoint."""
        score = {
            "ticker": "AAPL",
            "fraud_score": 75.5,
            "risk_level": "high",
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_fraud_score(score)

        with app.test_client() as client:
            response = client.get("/api/fraud-scores")
            assert response.status_code == 200
            data = response.get_json()
            assert "scores" in data
            assert len(data["scores"]) == 1
            assert data["scores"][0]["ticker"] == "AAPL"

    def test_get_fraud_scores_by_ticker(self, app, db):
        """Test the get_fraud_scores endpoint with ticker filter."""
        score = {
            "ticker": "AAPL",
            "fraud_score": 75.5,
            "risk_level": "high",
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_fraud_score(score)

        with app.test_client() as client:
            response = client.get("/api/fraud-scores?ticker=AAPL")
            assert response.status_code == 200
            data = response.get_json()
            assert "scores" in data
            assert len(data["scores"]) == 1
            assert data["scores"][0]["ticker"] == "AAPL"

    def test_get_red_flags(self, app, db):
        """Test the get_red_flags endpoint."""
        flag = {
            "ticker": "AAPL",
            "category": "accounting",
            "severity": "high",
            "description": "Revenue recognition issues",
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_red_flag(flag)

        with app.test_client() as client:
            response = client.get("/api/red-flags")
            assert response.status_code == 200
            data = response.get_json()
            assert "flags" in data
            assert len(data["flags"]) == 1
            assert data["flags"][0]["ticker"] == "AAPL"

    def test_get_red_flags_by_ticker(self, app, db):
        """Test the get_red_flags endpoint with ticker filter."""
        flag = {
            "ticker": "AAPL",
            "category": "accounting",
            "severity": "high",
            "description": "Revenue recognition issues",
            "filing_date": "2023-01-01",
            "accession_no": "0000320193-23-000001",
        }
        db.insert_red_flag(flag)

        with app.test_client() as client:
            response = client.get("/api/red-flags?ticker=AAPL")
            assert response.status_code == 200
            data = response.get_json()
            assert "flags" in data
            assert len(data["flags"]) == 1
            assert data["flags"][0]["ticker"] == "AAPL"

    def test_get_capital_flows(self, app, db):
        """Test the get_capital_flows endpoint."""
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

        with app.test_client() as client:
            response = client.get("/api/capital-flows")
            assert response.status_code == 200
            data = response.get_json()
            assert "flows" in data
            assert len(data["flows"]) == 1
            assert data["flows"][0]["ticker"] == "AAPL"

    def test_get_capital_flows_by_ticker(self, app, db):
        """Test the get_capital_flows endpoint with ticker filter."""
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

        with app.test_client() as client:
            response = client.get("/api/capital-flows?ticker=AAPL")
            assert response.status_code == 200
            data = response.get_json()
            assert "flows" in data
            assert len(data["flows"]) == 1
            assert data["flows"][0]["ticker"] == "AAPL"
