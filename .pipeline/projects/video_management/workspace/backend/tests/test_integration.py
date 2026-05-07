"""Integration tests for the video management platform."""

from app.models import VideoStatus


class TestIntegration:
    """Integration tests covering multiple endpoints."""

    def test_create_video(self, test_client, sample_table):
        """Test creating a video and verifying it appears in the list."""
        # Create a video
        response = test_client.post(
            "/api/videos",
            json={
                "title": "Integration Test Video",
                "description": "This is an integration test",
                "status": VideoStatus.DRAFT,
                "tags": ["integration", "test"],
                "thumbnail_url": "https://example.com/integration-thumb.jpg",
            },
        )
        assert response.status_code == 201
        video_id = response.json()["id"]

        # Verify it appears in the list
        list_response = test_client.get("/api/videos")
        list_data = list_response.json()
        assert list_data["total"] >= 1
        video_titles = [v["title"] for v in list_data["items"]]
        assert "Integration Test Video" in video_titles

        # Verify we can get it individually
        get_response = test_client.get(f"/api/videos/{video_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Integration Test Video"

    def test_update_video(self, test_client, sample_table):
        """Test updating a video and verifying the changes."""
        # Create a video
        create_response = test_client.post(
            "/api/videos",
            json={
                "title": "Original Title",
                "description": "Original description",
                "status": VideoStatus.DRAFT,
            },
        )
        video_id = create_response.json()["id"]

        # Update the video
        update_response = test_client.put(
            f"/api/videos/{video_id}",
            json={
                "title": "Updated Title",
                "status": VideoStatus.PUBLISHED,
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Title"
        assert update_response.json()["status"] == VideoStatus.PUBLISHED

        # Verify the update persisted
        get_response = test_client.get(f"/api/videos/{video_id}")
        assert get_response.json()["title"] == "Updated Title"
        assert get_response.json()["status"] == VideoStatus.PUBLISHED

    def test_create_field_and_video(self, test_client, sample_table):
        """Test creating a custom field and using it in a video."""
        # Add a custom field
        field_response = test_client.post(
            f"/api/tables/{sample_table}/fields",
            json={
                "name": "Custom Field",
                "field_type": "text",
                "is_required": False,
            },
        )
        assert field_response.status_code == 201

        # Create a video with the custom field
        video_response = test_client.post(
            "/api/videos",
            json={
                "title": "Video with Custom Field",
                "custom_fields": {"Custom Field": "Custom Value"},
            },
        )
        assert video_response.status_code == 201
        assert video_response.json()["custom_fields"]["Custom Field"] == "Custom Value"

    def test_delete_video(self, test_client, sample_table):
        """Test deleting a video and verifying it's gone."""
        # Create a video
        create_response = test_client.post(
            "/api/videos",
            json={"title": "Delete Me Video"},
        )
        video_id = create_response.json()["id"]

        # Delete the video
        delete_response = test_client.delete(f"/api/videos/{video_id}")
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = test_client.get(f"/api/videos/{video_id}")
        assert get_response.status_code == 404

        # Verify it's not in the list
        list_response = test_client.get("/api/videos")
        list_data = list_response.json()
        video_titles = [v["title"] for v in list_data["items"]]
        assert "Delete Me Video" not in video_titles

    def test_create_table_and_fields(self, test_client):
        """Test creating a table and its fields."""
        # Create a table
        table_response = test_client.post(
            "/api/tables",
            json={"name": "Integration Table", "description": "For integration tests"},
        )
        assert table_response.status_code == 201
        table_id = table_response.json()["id"]

        # Verify the table exists
        get_response = test_client.get(f"/api/tables/{table_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Integration Table"

        # Verify fields exist
        fields_response = test_client.get(f"/api/tables/{table_id}/fields")
        assert fields_response.status_code == 200
        assert fields_response.json()["total"] >= 11  # Built-in fields

        # Add a custom field
        custom_field_response = test_client.post(
            f"/api/tables/{table_id}/fields",
            json={
                "name": "Custom Integration Field",
                "field_type": "text",
            },
        )
        assert custom_field_response.status_code == 201

        # Verify the custom field appears in the list
        fields_response = test_client.get(f"/api/tables/{table_id}/fields")
        field_names = [f["name"] for f in fields_response.json()["items"]]
        assert "Custom Integration Field" in field_names
