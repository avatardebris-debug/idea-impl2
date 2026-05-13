"""Tests for SEC Importer 2 API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sec_importer.api.main import create_app
from sec_importer.api.config import APIConfig


@pytest.fixture
def app(db_path):
    """Create test app with in-memory database."""
    config = APIConfig(
        app_name="Test App",
        app_version="0.1.0",
        db_path=db_path,
        debug=True,
        log_level="DEBUG",
        rate_limit_per_ip=100,
        rate_limit_per_minute=100,
        cors_origins=["*"],
    )
    return create_app(config)


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        assert "database" in data


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root(self, client):
        """Test root returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


class TestCompaniesEndpoint:
    """Tests for the companies endpoint."""

    def test_get_company_not_found(self, client):
        """Test getting non-existent company returns 404."""
        response = client.get("/companies/NONEXISTENT")
        assert response.status_code == 404


class TestFilingsEndpoint:
    """Tests for the filings endpoint."""

    def test_get_filings_empty(self, client):
        """Test getting filings returns empty list."""
        response = client.get("/filings?ticker=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestSearchEndpoint:
    """Tests for the search endpoint."""

    def test_search_empty(self, client):
        """Test search returns empty results."""
        response = client.get("/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
