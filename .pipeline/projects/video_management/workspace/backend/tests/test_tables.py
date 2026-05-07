"""Tests for table management API endpoints."""

from app.models import FieldTypeId


class TestTableEndpoints:
    """Tests for table CRUD endpoints."""

    def test_create_table(self, test_client):
        """Test creating a new table."""
        response = test_client.post(
            "/api/tables",
            json={
                "name": "Test Table",
                "description": "A test table",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Table"
        assert data["description"] == "A test table"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_table_duplicate_name(self, test_client):
        """Test that duplicate table names are rejected."""
        # Create first table
        test_client.post(
            "/api/tables",
            json={"name": "Duplicate Table", "description": "First"},
        )
        # Try to create another with same name
        response = test_client.post(
            "/api/tables",
            json={"name": "Duplicate Table", "description": "Second"},
        )
        assert response.status_code == 409

    def test_get_table(self, test_client, sample_table):
        """Test getting a specific table."""
        response = test_client.get(f"/api/tables/{sample_table}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Table"

    def test_get_nonexistent_table(self, test_client):
        """Test getting a table that doesn't exist."""
        response = test_client.get("/api/tables/nonexistent-id")
        assert response.status_code == 404

    def test_update_table(self, test_client, sample_table):
        """Test updating a table."""
        response = test_client.put(
            f"/api/tables/{sample_table}",
            json={
                "name": "Updated Table Name",
                "description": "Updated description",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Table Name"
        assert data["description"] == "Updated description"

    def test_delete_table(self, test_client, sample_table):
        """Test deleting a table."""
        response = test_client.delete(f"/api/tables/{sample_table}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = test_client.get(f"/api/tables/{sample_table}")
        assert get_response.status_code == 404

    def test_list_tables(self, test_client):
        """Test listing tables with pagination."""
        # Create several tables
        for i in range(5):
            test_client.post(
                "/api/tables",
                json={"name": f"Table {i}", "description": f"Description {i}"},
            )

        # List tables
        response = test_client.get("/api/tables?page=1&page_size=3")
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 3

    def test_list_tables_with_search(self, test_client):
        """Test listing tables with search."""
        test_client.post(
            "/api/tables",
            json={"name": "Search Table", "description": "For search test"},
        )

        # Search by name
        response = test_client.get("/api/tables?search=Search")
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Search Table"

        # Search by description
        response = test_client.get("/api/tables?search=description")
        data = response.json()
        assert data["total"] == 1

    def test_create_table_with_builtin_fields(self, test_client, sample_table):
        """Test that built-in fields are created with the table."""
        response = test_client.get(f"/api/tables/{sample_table}/fields")
        data = response.json()
        field_names = [f["name"] for f in data["items"]]
        assert "id" in field_names
        assert "title" in field_names
        assert "description" in field_names
        assert "status" in field_names
        assert "tags" in field_names
        assert "publish_date" in field_names
        assert "thumbnail_url" in field_names
        assert "youtube_video_id" in field_names
        assert "custom_fields" in field_names
        assert "created_at" in field_names
        assert "updated_at" in field_names
