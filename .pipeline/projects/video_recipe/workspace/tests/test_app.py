"""Tests for the Video Recipe Browser application."""

import pytest
from fastapi.testclient import TestClient
from video_recipe.app import app, store
from video_recipe.models import Video, Recipe, RecipeStep
from pathlib import Path
import tempfile
import os


@pytest.fixture(autouse=True)
def clean_store():
    """Clean the store before each test."""
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def sample_video():
    """Create a sample video file for testing."""
    video_dir = Path(__file__).parent / "test_videos"
    video_dir.mkdir(exist_ok=True)
    video_path = video_dir / "test_cooking.mp4"
    # Create a dummy video file
    with open(video_path, "wb") as f:
        f.write(b"dummy video content")
    return video_path


class TestUpload:
    """Test video upload functionality."""

    def test_upload_video(self, client, sample_video):
        """Test uploading a video file."""
        with open(sample_video, "rb") as f:
            response = client.post(
                "/upload",
                files={"file": ("test_cooking.mp4", f, "video/mp4")},
                data={"task_type": "cooking"},
            )

        assert response.status_code == 200
        assert "recipe" in response.json()
        assert response.json()["recipe"]["task_type"] == "cooking"

    def test_upload_video_without_task_type(self, client, sample_video):
        """Test uploading a video without specifying task type."""
        with open(sample_video, "rb") as f:
            response = client.post(
                "/upload",
                files={"file": ("test_cooking.mp4", f, "video/mp4")},
            )

        assert response.status_code == 200
        assert "recipe" in response.json()

    def test_upload_invalid_file(self, client):
        """Test uploading an invalid file."""
        response = client.post(
            "/upload",
            files={"file": ("test.txt", b"not a video", "text/plain")},
        )
        assert response.status_code == 400


class TestRecipeView:
    """Test recipe viewing functionality."""

    def test_view_recipe(self, client, sample_video):
        """Test viewing a recipe."""
        # First upload a video
        with open(sample_video, "rb") as f:
            upload_response = client.post(
                "/upload",
                files={"file": ("test_cooking.mp4", f, "video/mp4")},
                data={"task_type": "cooking"},
            )
        recipe_id = upload_response.json()["recipe"]["recipe_id"]

        # Then view the recipe
        response = client.get(f"/recipe/{recipe_id}")
        assert response.status_code == 200
        assert "recipe" in response.json()
        assert response.json()["recipe"]["recipe_id"] == recipe_id

    def test_view_nonexistent_recipe(self, client):
        """Test viewing a recipe that doesn't exist."""
        response = client.get("/recipe/nonexistent")
        assert response.status_code == 404


class TestCompare:
    """Test recipe comparison functionality."""

    def test_compare_page(self, client):
        """Test the compare page loads."""
        response = client.get("/compare")
        assert response.status_code == 200

    def test_compare_recipes(self, client, sample_video):
        """Test comparing two recipes."""
        # Upload two videos
        with open(sample_video, "rb") as f:
            response1 = client.post(
                "/upload",
                files={"file": ("test1.mp4", f, "video/mp4")},
                data={"task_type": "cooking"},
            )
        with open(sample_video, "rb") as f:
            response2 = client.post(
                "/upload",
                files={"file": ("test2.mp4", f, "video/mp4")},
                data={"task_type": "repair"},
            )

        recipe_id_1 = response1.json()["recipe"]["recipe_id"]
        recipe_id_2 = response2.json()["recipe"]["recipe_id"]

        # Compare them
        response = client.post(
            "/compare",
            data={"recipe_id_1": recipe_id_1, "recipe_id_2": recipe_id_2},
        )
        assert response.status_code == 200
        assert "recipe_1" in response.json()
        assert "recipe_2" in response.json()


class TestExport:
    """Test recipe export functionality."""

    def test_export_pdf(self, client, sample_video):
        """Test exporting a recipe as PDF (markdown)."""
        # Upload a video
        with open(sample_video, "rb") as f:
            upload_response = client.post(
                "/upload",
                files={"file": ("test_cooking.mp4", f, "video/mp4")},
                data={"task_type": "cooking"},
            )
        recipe_id = upload_response.json()["recipe"]["recipe_id"]

        # Export as PDF
        response = client.get(f"/export/{recipe_id}/pdf")
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]

    def test_export_text(self, client, sample_video):
        """Test exporting a recipe as text."""
        # Upload a video
        with open(sample_video, "rb") as f:
            upload_response = client.post(
                "/upload",
                files={"file": ("test_cooking.mp4", f, "video/mp4")},
                data={"task_type": "cooking"},
            )
        recipe_id = upload_response.json()["recipe"]["recipe_id"]

        # Export as text
        response = client.get(f"/export/{recipe_id}/text")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestSearch:
    """Test recipe search functionality."""

    def test_search_all(self, client, sample_video):
        """Test searching all recipes."""
        # Upload a video
        with open(sample_video, "rb") as f:
            client.post(
                "/upload",
                files={"file": ("test_cooking.mp4", f, "video/mp4")},
                data={"task_type": "cooking"},
            )

        # Search all
        response = client.get("/search")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_by_task_type(self, client, sample_video):
        """Test searching by task type."""
        # Upload videos with different task types
        with open(sample_video, "rb") as f:
            client.post(
                "/upload",
                files={"file": ("test1.mp4", f, "video/mp4")},
                data={"task_type": "cooking"},
            )
        with open(sample_video, "rb") as f:
            client.post(
                "/upload",
                files={"file": ("test2.mp4", f, "video/mp4")},
                data={"task_type": "repair"},
            )

        # Search for cooking
        response = client.get("/search?task_type=cooking")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["task_type"] == "cooking"


class TestAnnotation:
    """Test recipe annotation functionality."""

    def test_annotate_recipe(self, client, sample_video):
        """Test adding an annotation to a recipe."""
        # Upload a video
        with open(sample_video, "rb") as f:
            upload_response = client.post(
                "/upload",
                files={"file": ("test_cooking.mp4", f, "video/mp4")},
                data={"task_type": "cooking"},
            )
        recipe_id = upload_response.json()["recipe"]["recipe_id"]

        # Add annotation
        response = client.post(
            f"/recipe/{recipe_id}/annotate",
            data={"step_index": 0, "user_note": "This step is important"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Verify annotation exists
        recipe_data = store.get_recipe(recipe_id)
        assert recipe_data is not None
        annotations = store.get_annotations(recipe_id)
        assert len(annotations) == 1
        assert annotations[0]["user_note"] == "This step is important"


class TestStore:
    """Test the in-memory store."""

    def test_add_and_get_recipe(self):
        """Test adding and retrieving a recipe."""
        video = Video(
            video_id="test1",
            filename="test.mp4",
            task_type="cooking",
            duration=120,
        )
        recipe = Recipe(
            video_id="test1",
            title="Test Recipe",
            summary="A test recipe",
            steps=[
                RecipeStep(
                    step_index=0,
                    description="Step 1",
                    timestamp=0.0,
                    inferred_tools=["pan"],
                    inferred_materials=["oil"],
                )
            ],
        )
        recipe_id = store.add_recipe(video.video_id, recipe)
        assert recipe_id is not None

        retrieved = store.get_recipe(recipe_id)
        assert retrieved is not None
        assert retrieved["title"] == "Test Recipe"

    def test_search_by_task_type(self):
        """Test searching by task type."""
        video1 = Video(
            video_id="test1",
            filename="test1.mp4",
            task_type="cooking",
            duration=120,
        )
        video2 = Video(
            video_id="test2",
            filename="test2.mp4",
            task_type="repair",
            duration=60,
        )

        recipe1 = Recipe(
            video_id="test1",
            title="Cooking Recipe",
            summary="Cooking",
            steps=[],
        )
        recipe2 = Recipe(
            video_id="test2",
            title="Repair Recipe",
            summary="Repair",
            steps=[],
        )

        store.add_recipe(video1.video_id, recipe1)
        store.add_recipe(video2.video_id, recipe2)

        results = store.search_by_task_type("cooking")
        assert len(results) == 1
        assert results[0]["title"] == "Cooking Recipe"

    def test_clear_store(self):
        """Test clearing the store."""
        video = Video(
            video_id="test1",
            filename="test.mp4",
            task_type="cooking",
            duration=120,
        )
        recipe = Recipe(
            video_id="test1",
            title="Test Recipe",
            summary="A test recipe",
            steps=[],
        )
        store.add_recipe(video.video_id, recipe)
        assert len(store.get_all_videos()) == 1

        store.clear()
        assert len(store.get_all_videos()) == 0


class TestMarkdownExport:
    """Test markdown export functionality."""

    def test_recipe_to_markdown(self):
        """Test converting a recipe to markdown."""
        from video_recipe.app import _recipe_to_markdown

        recipe = {
            "title": "Test Recipe",
            "summary": "A test recipe",
            "steps": [
                {
                    "description": "Step 1",
                    "inferred_tools": ["pan"],
                    "inferred_materials": ["oil"],
                },
                {
                    "description": "Step 2",
                    "inferred_tools": [],
                    "inferred_materials": [],
                },
            ],
        }

        md = _recipe_to_markdown(recipe)
        assert "# Test Recipe" in md
        assert "A test recipe" in md
        assert "## Steps" in md
        assert "1. **Step 1**" in md
        assert "Tools: pan" in md
        assert "Materials: oil" in md
        assert "2. **Step 2**" in md
