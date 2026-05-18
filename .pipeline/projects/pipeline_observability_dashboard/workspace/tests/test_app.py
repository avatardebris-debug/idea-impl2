"""Tests for FastAPI endpoints."""
from fastapi.testclient import TestClient
from dashboard.app import app

client = TestClient(app)

def test_read_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Pipeline Observability Dashboard" in response.text

def test_api_metrics():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "global" in data
    assert "projects" in data
    assert "total_projects" in data["global"]
