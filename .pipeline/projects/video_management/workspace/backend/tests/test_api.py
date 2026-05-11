"""Tests for the Video Management Platform API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import YouTubeChannel

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    """Create a test client."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def test_get_health_success(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_create_table_success(client):
    """Test creating a table."""
    response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_table"
    assert data["description"] == "Test table"
    assert "id" in data


def test_list_tables_success(client):
    """Test listing tables."""
    # Create a table first
    client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    response = client.get("/api/v1/tables")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_table_success(client):
    """Test getting a table."""
    # Create a table first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    response = client.get(f"/api/v1/tables/{table_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_table"


def test_update_table_success(client):
    """Test updating a table."""
    # Create a table first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    response = client.put(f"/api/v1/tables/{table_id}", json={"name": "updated_table"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated_table"


def test_delete_table_success(client):
    """Test deleting a table."""
    # Create a table first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    response = client.delete(f"/api/v1/tables/{table_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Table deleted successfully."


def test_create_field_success(client):
    """Test creating a field."""
    # Create a table first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    response = client.post(f"/api/v1/tables/{table_id}/fields", json={"name": "test_field", "type": "text"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_field"
    assert data["type"] == "text"
    assert "id" in data


def test_list_fields_success(client):
    """Test listing fields."""
    # Create a table and field first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    client.post(f"/api/v1/tables/{table_id}/fields", json={"name": "test_field", "type": "text"})
    response = client.get(f"/api/v1/tables/{table_id}/fields")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_field_success(client):
    """Test getting a field."""
    # Create a table and field first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    field_response = client.post(f"/api/v1/tables/{table_id}/fields", json={"name": "test_field", "type": "text"})
    field_id = field_response.json()["id"]
    response = client.get(f"/api/v1/tables/{table_id}/fields/{field_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_field"


def test_update_field_success(client):
    """Test updating a field."""
    # Create a table and field first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    field_response = client.post(f"/api/v1/tables/{table_id}/fields", json={"name": "test_field", "type": "text"})
    field_id = field_response.json()["id"]
    response = client.put(f"/api/v1/tables/{table_id}/fields/{field_id}", json={"name": "updated_field"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated_field"


def test_delete_field_success(client):
    """Test deleting a field."""
    # Create a table and field first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    field_response = client.post(f"/api/v1/tables/{table_id}/fields", json={"name": "test_field", "type": "text"})
    field_id = field_response.json()["id"]
    response = client.delete(f"/api/v1/tables/{table_id}/fields/{field_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Field deleted successfully."


def test_create_video_success(client):
    """Test creating a video."""
    # Create a table first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    response = client.post("/api/v1/videos", json={"title": "Test Video", "description": "Test Description", "table_id": table_id})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Video"
    assert data["description"] == "Test Description"
    assert "id" in data


def test_list_videos_success(client):
    """Test listing videos."""
    # Create a table and video first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    client.post("/api/v1/videos", json={"title": "Test Video", "description": "Test Description", "table_id": table_id})
    response = client.get("/api/v1/videos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_video_success(client):
    """Test getting a video."""
    # Create a table and video first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    video_response = client.post("/api/v1/videos", json={"title": "Test Video", "description": "Test Description", "table_id": table_id})
    video_id = video_response.json()["id"]
    response = client.get(f"/api/v1/videos/{video_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Video"


def test_update_video_success(client):
    """Test updating a video."""
    # Create a table and video first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    video_response = client.post("/api/v1/videos", json={"title": "Test Video", "description": "Test Description", "table_id": table_id})
    video_id = video_response.json()["id"]
    response = client.put(f"/api/v1/videos/{video_id}", json={"title": "Updated Video"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Video"


def test_delete_video_success(client):
    """Test deleting a video."""
    # Create a table and video first
    create_response = client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})
    table_id = create_response.json()["id"]
    video_response = client.post("/api/v1/videos", json={"title": "Test Video", "description": "Test Description", "table_id": table_id})
    video_id = video_response.json()["id"]
    response = client.delete(f"/api/v1/videos/{video_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Video deleted successfully."


def test_get_stats_success(client):
    """Test getting channel stats."""
    # Create a YouTube channel first
    db = TestingSessionLocal()
    channel = YouTubeChannel(
        channel_id="test_channel_id",
        channel_name="Test Channel",
        is_connected=True,
        access_token="test_token",
        refresh_token="test_refresh_token",
        token_expiry=None,
    )
    db.add(channel)
    db.commit()
    db.close()

    response = client.get("/api/v1/youtube/stats")
    assert response.status_code == 200
    data = response.json()
    assert "subscriber_count" in data


def test_disconnect_success(client):
    """Test disconnecting YouTube channel."""
    # Create a YouTube channel first
    db = TestingSessionLocal()
    channel = YouTubeChannel(
        channel_id="test_channel_id",
        channel_name="Test Channel",
        is_connected=True,
        access_token="test_token",
        refresh_token="test_refresh_token",
        token_expiry=None,
    )
    db.add(channel)
    db.commit()
    db.close()

    response = client.delete("/api/v1/youtube/disconnect")
    assert response.status_code == 200
    assert response.json()["message"] == "Disconnected from YouTube."


def test_sync_success(client):
    """Test syncing YouTube videos."""
    # Create a YouTube channel first
    db = TestingSessionLocal()
    channel = YouTubeChannel(
        channel_id="test_channel_id",
        channel_name="Test Channel",
        is_connected=True,
        access_token="test_token",
        refresh_token="test_refresh_token",
        token_expiry=None,
    )
    db.add(channel)
    db.commit()
    db.close()

    # Create a table first
    client.post("/api/v1/tables", json={"name": "test_table", "description": "Test table"})

    response = client.post("/api/v1/youtube/sync")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "synced" in data


def test_get_sync_status_success(client):
    """Test getting sync status."""
    # Create a YouTube channel first
    db = TestingSessionLocal()
    channel = YouTubeChannel(
        channel_id="test_channel_id",
        channel_name="Test Channel",
        is_connected=True,
        access_token="test_token",
        refresh_token="test_refresh_token",
        token_expiry=None,
    )
    db.add(channel)
    db.commit()
    db.close()

    response = client.get("/api/v1/youtube/sync-status")
    assert response.status_code == 200
    data = response.json()
    assert "is_connected" in data
    assert "last_sync_at" in data


def test_get_auth_url_success(client):
    """Test getting OAuth auth URL."""
    response = client.get("/api/v1/youtube/auth")
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert "state" in data


def test_get_channel_status_success(client):
    """Test getting channel status."""
    # Create a YouTube channel first
    db = TestingSessionLocal()
    channel = YouTubeChannel(
        channel_id="test_channel_id",
        channel_name="Test Channel",
        is_connected=True,
        access_token="test_token",
        refresh_token="test_refresh_token",
        token_expiry=None,
    )
    db.add(channel)
    db.commit()
    db.close()

    response = client.get("/api/v1/youtube/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_connected" in data
    assert "channel_name" in data


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/api/v1/tables")
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
