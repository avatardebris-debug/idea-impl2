"""Tests for SEC Importer 2 API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sec_importer.api.main import app
from sec_importer.api.config import APIConfig


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
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
        response = client.get("/api/v1/companies/NONEXISTENT")
        assert response.status_code == 404


class TestFilingsEndpoint:
    """Tests for the filings endpoint."""

    def test_get_filings_empty(self, client):
        """Test getting filings returns empty list."""
        response = client.get("/api/v1/filings?ticker=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)


class TestSearchEndpoint:
    """Tests for the search endpoint."""

    def test_search_empty(self, client):
        """Test search returns empty results."""
        response = client.get("/api/v1/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
