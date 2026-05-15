"""Tests for video CRUD API endpoints."""

from app.models import VideoStatus


class TestVideoEndpoints:
    """Tests for video CRUD endpoints."""

    def test_create_video(self, sample_table, test_client):
        """Test creating a video record."""
        response = test_client.post(
            "/api/videos",
            json={
                "title": "Test Video",
                "description": "A test video",
                "status": VideoStatus.DRAFT,
                "tags": ["test", "demo"],
                "thumbnail_url": "https://example.com/thumb.jpg",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Video"
        assert data["status"] == VideoStatus.DRAFT
        assert "id" in data
        assert "created_at" in data

    def test_get_video(self, sample_table, test_client):
        """Test getting a specific video."""
        # Create a video first
        create_response = test_client.post(
            "/api/videos",
            json={
                "title": "Get Test Video",
                "description": "For get test",
                "status": VideoStatus.PUBLISHED,
            },
        )
        video_id = create_response.json()["id"]

        # Get the video
        response = test_client.get(f"/api/videos/{video_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Get Test Video"
        assert data["status"] == VideoStatus.PUBLISHED

    def test_get_nonexistent_video(self, test_client):
        """Test getting a video that doesn't exist."""
        response = test_client.get("/api/videos/nonexistent-id")
        assert response.status_code == 404

    def test_update_video(self, sample_table, test_client):
        """Test updating a video."""
        # Create a video first
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
        response = test_client.put(
            f"/api/videos/{video_id}",
            json={
                "title": "Updated Title",
                "status": VideoStatus.PUBLISHED,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == VideoStatus.PUBLISHED

    def test_update_partial_video(self, sample_table, test_client):
        """Test updating only some fields of a video."""
        # Create a video first
        create_response = test_client.post(
            "/api/videos",
            json={
                "title": "Original Title",
                "description": "Original description",
                "status": VideoStatus.DRAFT,
            },
        )
        video_id = create_response.json()["id"]

        # Update only the title
        response = test_client.put(
            f"/api/videos/{video_id}",
            json={"title": "Only Title Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Only Title Updated"
        assert data["description"] == "Original description"
        assert data["status"] == VideoStatus.DRAFT

    def test_delete_video(self, sample_table, test_client):
        """Test deleting a video."""
        # Create a video first
        create_response = test_client.post(
            "/api/videos",
            json={
                "title": "Delete Me Video",
                "description": "This video will be deleted",
            },
        )
        video_id = create_response.json()["id"]

        # Delete the video
        response = test_client.delete(f"/api/videos/{video_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = test_client.get(f"/api/videos/{video_id}")
        assert get_response.status_code == 404

    def test_list_videos(self, sample_table, test_client):
        """Test listing videos with pagination."""
        # Create several videos
        for i in range(5):
            test_client.post(
                "/api/videos",
                json={
                    "title": f"Video {i}",
                    "description": f"Description {i}",
                    "status": VideoStatus.DRAFT,
                },
            )

        # List videos
        response = test_client.get("/api/videos?page=1&page_size=3")
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert data["total"] >= 5

    def test_list_videos_with_search(self, sample_table, test_client):
        """Test listing videos with search."""
        test_client.post(
            "/api/videos",
            json={
                "title": "Search Test Video",
                "description": "For search test",
                "status": "published",
            },
        )

        # Search by title
        response = test_client.get("/api/videos?search=Search")
        data = response.json()
        assert data["total"] >= 1
        assert any("Search Test Video" in v["title"] for v in data["items"])

        # Search by description
        response = test_client.get("/api/videos?search=test")
        data = response.json()
        assert data["total"] >= 1

    def test_list_videos_with_status_filter(self, sample_table, test_client):
        """Test listing videos with status filter."""
        test_client.post(
            "/api/videos",
            json={
                "title": "Draft Video",
                "status": "draft",
            },
        )
        test_client.post(
            "/api/videos",
            json={
                "title": "Published Video",
                "status": "published",
            },
        )

        # Filter by DRAFT
        response = test_client.get("/api/videos?status=draft")
        data = response.json()
        assert all(v["status"] == "draft" for v in data["items"])

        # Filter by PUBLISHED
        response = test_client.get("/api/videos?status=published")
        data = response.json()
        assert all(v["status"] == "published" for v in data["items"])

    def test_list_videos_with_tags_filter(self, sample_table, test_client):
        """Test listing videos with tags filter."""
        test_client.post(
            "/api/videos",
            json={
                "title": "Python Video",
                "tags": ["python", "tutorial"],
                "status": VideoStatus.PUBLISHED,
            },
        )

        # Filter by tag
        response = test_client.get("/api/videos?tags=python")
        data = response.json()
        assert data["total"] >= 1
        assert any("python" in v.get("tags", []) for v in data["items"])

    def test_update_thumbnail_url_to_none(self, sample_table, test_client):
        """Test updating thumbnail_url to None."""
        # Create a video with thumbnail
        create_response = test_client.post(
            "/api/videos",
            json={
                "title": "Thumbnail Test Video",
                "thumbnail_url": "https://example.com/thumb.jpg",
            },
        )
        video_id = create_response.json()["id"]

        # Update thumbnail_url to None
        response = test_client.put(
            f"/api/videos/{video_id}",
            json={"thumbnail_url": None},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["thumbnail_url"] is None

    def test_create_video_with_custom_fields(self, sample_table, test_client):
        """Test creating a video with custom fields."""
        response = test_client.post(
            "/api/videos",
            json={
                "title": "Custom Fields Video",
                "custom_fields": {
                    "episode_number": 1,
                    "duration": "10:30",
                    "guest": "John Doe",
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["custom_fields"]["episode_number"] == 1
        assert data["custom_fields"]["duration"] == "10:30"
        assert data["custom_fields"]["guest"] == "John Doe"

    def test_create_video_with_all_builtin_fields(self, sample_table, test_client):
        """Test creating a video with all built-in fields."""
        response = test_client.post(
            "/api/videos",
            json={
                "title": "All Fields Video",
                "description": "Testing all fields",
                "status": VideoStatus.PUBLISHED,
                "tags": ["test", "all", "fields"],
                "thumbnail_url": "https://example.com/all.jpg",
                "youtube_video_id": "dQw4w9WgXcQ",
                "custom_fields": {"custom": "value"},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "All Fields Video"
        assert data["description"] == "Testing all fields"
        assert data["status"] == VideoStatus.PUBLISHED
        assert "test" in data["tags"]
        assert data["thumbnail_url"] == "https://example.com/all.jpg"
        assert data["youtube_video_id"] == "dQw4w9WgXcQ"
        assert data["custom_fields"]["custom"] == "value"
