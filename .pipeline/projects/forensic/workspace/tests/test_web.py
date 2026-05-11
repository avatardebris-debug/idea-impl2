"""Tests for Forensic Suite web module."""

import sys
import os
import pytest
import tempfile

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from forensic.database import ForensicDatabase
from forensic.web import create_app


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
    app = create_app(db=db)
    app.config["TESTING"] = True
    return app


class TestWeb:
    def test_index(self, app):
        """Test the index endpoint."""
        with app.test_client() as client:
            response = client.get("/")
            assert response.status_code == 200

    def test_companies(self, app):
        """Test the companies endpoint."""
        with app.test_client() as client:
            response = client.get("/companies")
            assert response.status_code == 200

    def test_fraud_scores(self, app):
        """Test the fraud_scores endpoint."""
        with app.test_client() as client:
            response = client.get("/fraud-scores")
            assert response.status_code == 200

    def test_red_flags(self, app):
        """Test the red_flags endpoint."""
        with app.test_client() as client:
            response = client.get("/red-flags")
            assert response.status_code == 200

    def test_capital_flows(self, app):
        """Test the capital_flows endpoint."""
        with app.test_client() as client:
            response = client.get("/capital-flows")
            assert response.status_code == 200

    def test_ticker_detail(self, app):
        """Test the ticker_detail endpoint."""
        with app.test_client() as client:
            response = client.get("/ticker/AAPL")
            assert response.status_code == 200

    def test_api_companies(self, app):
        """Test the API companies endpoint."""
        with app.test_client() as client:
            response = client.get("/api/companies")
            assert response.status_code == 200

    def test_api_fraud_scores(self, app):
        """Test the API fraud_scores endpoint."""
        with app.test_client() as client:
            response = client.get("/api/fraud-scores")
            assert response.status_code == 200

    def test_api_red_flags(self, app):
        """Test the API red_flags endpoint."""
        with app.test_client() as client:
            response = client.get("/api/red-flags")
            assert response.status_code == 200

    def test_api_capital_flows(self, app):
        """Test the API capital_flows endpoint."""
        with app.test_client() as client:
            response = client.get("/api/capital-flows")
            assert response.status_code == 200
