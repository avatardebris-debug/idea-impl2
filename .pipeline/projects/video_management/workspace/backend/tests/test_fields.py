"""Tests for custom field management API."""

import pytest
from app.models import FieldTypeId


class TestFieldEndpoints:
    """Tests for field CRUD endpoints."""

    def test_list_fields(self, sample_table, test_client):
        """Test listing fields for a table."""
        response = test_client.get(f"/api/tables/{sample_table}/fields")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 11  # Built-in fields
        field_names = [f["name"] for f in data["items"]]
        assert "title" in field_names
        assert "description" in field_names

    def test_create_field(self, sample_table, test_client):
        """Test creating a custom field."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Custom Field",
                "field_type": "text",
                "is_required": False,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Custom Field"
        assert data["field_type"] == "text"
        assert data["is_required"] is False
        assert "id" in data

    def test_create_field_duplicate_name(self, sample_table, test_client):
        """Test that duplicate field names are rejected."""
        # Create first field
        test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"name": "Duplicate Field", "field_type": "text"},
        )
        # Try to create another with same name
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"name": "Duplicate Field", "field_type": "text"},
        )
        assert response.status_code == 409

    def test_delete_field(self, sample_table, test_client):
        """Test deleting a field."""
        # Create a field first
        create_response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"name": "Delete Me Field", "field_type": "text"},
        )
        field_id = create_response.json()["id"]

        # Delete the field
        response = test_client.delete(f"/api/tables/{sample_table}/fields/{field_id}")
        assert response.status_code == 204

    def test_create_field_invalid_type(self, sample_table, test_client):
        """Test that invalid field types are rejected."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"name": "Invalid Field", "field_type": "invalid_type"},
        )
        assert response.status_code == 422

    def test_create_field_missing_name(self, sample_table, test_client):
        """Test that missing field name is rejected."""
        response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={"field_type": "text"},
        )
        assert response.status_code == 422
