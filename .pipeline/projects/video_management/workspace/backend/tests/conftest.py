"""Pytest configuration and fixtures for video management backend tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import TableMetadata, TableField, FieldTypeId

# ── Test database setup ──────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_video_management.db"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override the database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_client():
    """Return the test client."""
    with TestClient(app) as tc:
        yield tc


@pytest.fixture(autouse=True)
def setup_and_teardown(test_client):
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def sample_table(test_client):
    """Create a default table via the API and return its table_id."""
    response = test_client.post(
        "/api/tables",
        json={
            "name": "Test Table",
            "description": "A test table for integration tests",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def db_session():
    """Provide a database session for tests that need direct DB access."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_table(db_session):
    """Create a test table in the database."""
    table = TableMetadata(
        name="Test Table",
        description="A test table for integration tests",
    )
    db_session.add(table)
    db_session.commit()
    db_session.refresh(table)
    return table
