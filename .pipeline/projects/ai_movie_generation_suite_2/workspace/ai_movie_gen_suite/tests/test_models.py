"""Tests for the models module."""

import json
from datetime import datetime
from typing import Any, Dict

import pytest

from ai_movie_gen_suite.models import (
    Project,
    get_json_schema,
    validate_json_with_schema,
)


class TestProject:
    """Tests for the Project model."""

    def test_create_project_with_required_fields(self) -> None:
        """Test creating a project with only required fields."""
        project = Project(
            title="Test Movie",
            logline="A simple test logline.",
        )
        assert project.title == "Test Movie"
        assert project.logline == "A simple test logline."
        assert project.genre == "Drama"  # default
        assert project.tone == "Serious"  # default
        assert project.status == "initialized"
        assert project.beat_sheet is None
        assert project.characters is None
        assert project.script is None
        assert project.scene_descriptions is None
        assert project.summary is None
        assert project.music is None
        assert project.post_production is None
        assert project.marketing is None
        assert project.distribution is None
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_create_project_with_all_fields(self) -> None:
        """Test creating a project with all fields."""
        beat_sheet_data = {"beats": [{"number": 1, "action": "Test"}]}
        characters_data = {"characters": [{"name": "Hero"}]}
        script_data = {"scenes": [{"number": 1, "location": "Test"}]}
        scene_descs = [{"number": 1, "description": "Test scene"}]
        summary_data = {"synopsis": "Test synopsis"}
        music_data = {"main_theme": "Test theme"}
        post_prod_data = {"editing_plan": "Test plan"}
        marketing_data = {"campaign_overview": "Test campaign"}
        distribution_data = {"release_strategy": "Theatrical"}

        project = Project(
            title="Full Test Movie",
            logline="Full test logline.",
            genre="Sci-Fi",
            tone="Dark",
            beat_sheet=beat_sheet_data,
            characters=characters_data,
            script=script_data,
            scene_descriptions=scene_descs,
            summary=summary_data,
            music=music_data,
            post_production=post_prod_data,
            marketing=marketing_data,
            distribution=distribution_data,
        )

        assert project.genre == "Sci-Fi"
        assert project.tone == "Dark"
        assert project.beat_sheet == beat_sheet_data
        assert project.characters == characters_data
        assert project.script == script_data
        assert project.scene_descriptions == scene_descs
        assert project.summary == summary_data
        assert project.music == music_data
        assert project.post_production == post_prod_data
        assert project.marketing == marketing_data
        assert project.distribution == distribution_data

    def test_title_validator_rejects_empty_string(self) -> None:
        """Test that title validator rejects empty strings."""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            Project(title="", logline="Test logline.")

    def test_title_validator_rejects_whitespace_only(self) -> None:
        """Test that title validator rejects whitespace-only strings."""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            Project(title="   ", logline="Test logline.")

    def test_title_validator_strips_whitespace(self) -> None:
        """Test that title validator strips leading/trailing whitespace."""
        project = Project(title="  Test Movie  ", logline="Test logline.")
        assert project.title == "Test Movie"

    def test_to_dict(self) -> None:
        """Test converting project to dictionary."""
        project = Project(title="Test", logline="Test logline.")
        d = project.to_dict()

        assert d["title"] == "Test"
        assert d["logline"] == "Test logline."
        assert d["genre"] == "Drama"
        assert d["tone"] == "Serious"
        assert d["status"] == "initialized"
        assert d["beat_sheet"] is None
        assert d["characters"] is None
        assert d["script"] is None
        assert d["scene_descriptions"] is None
        assert d["summary"] is None
        assert d["music"] is None
        assert d["post_production"] is None
        assert d["marketing"] is None
        assert d["distribution"] is None
        assert "created_at" in d
        assert "updated_at" in d

    def test_to_json(self) -> None:
        """Test converting project to JSON string."""
        project = Project(title="Test", logline="Test logline.")
        json_str = project.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["title"] == "Test"
        assert parsed["logline"] == "Test logline."

    def test_to_json_with_indent(self) -> None:
        """Test JSON serialization with custom indent."""
        project = Project(title="Test", logline="Test logline.")
        json_str = project.to_json(indent=4)

        # Should be valid JSON with 4-space indent
        parsed = json.loads(json_str)
        assert parsed["title"] == "Test"

    def test_update_status(self) -> None:
        """Test updating project status."""
        project = Project(title="Test", logline="Test logline.")
        original_updated_at = project.updated_at

        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.01)

        project.update_status("in_progress")
        assert project.status == "in_progress"
        assert project.updated_at != original_updated_at

    def test_update_status_to_complete(self) -> None:
        """Test updating status to complete."""
        project = Project(title="Test", logline="Test logline.")
        project.update_status("pipeline_complete")
        assert project.status == "pipeline_complete"

    def test_update_status_to_failed(self) -> None:
        """Test updating status to failed."""
        project = Project(title="Test", logline="Test logline.")
        project.update_status("failed_at_concept_generator")
        assert project.status == "failed_at_concept_generator"

    def test_project_with_beat_sheet(self) -> None:
        """Test project with beat sheet data."""
        beat_sheet = {
            "beats": [
                {"beat_number": 1, "action": "Opening scene", "emotion": "Excitement"},
                {"beat_number": 2, "action": "Conflict arises", "emotion": "Tension"},
            ]
        }
        project = Project(title="Test", logline="Test logline.", beat_sheet=beat_sheet)
        assert project.beat_sheet == beat_sheet

    def test_project_with_characters(self) -> None:
        """Test project with character data."""
        characters = {
            "characters": [
                {"name": "Hero", "age": 30, "occupation": "Detective"},
                {"name": "Villain", "age": 45, "occupation": "Crime Lord"},
            ]
        }
        project = Project(title="Test", logline="Test logline.", characters=characters)
        assert project.characters == characters

    def test_project_with_script(self) -> None:
        """Test project with script data."""
        script = {
            "scenes": [
                {"number": 1, "location": "Coffee Shop", "description": "Meeting scene"},
            ]
        }
        project = Project(title="Test", logline="Test logline.", script=script)
        assert project.script == script

    def test_project_with_scene_descriptions(self) -> None:
        """Test project with scene descriptions."""
        scene_descs = [
            {"number": 1, "location": "Coffee Shop", "visual_description": "Bright morning"},
        ]
        project = Project(title="Test", logline="Test logline.", scene_descriptions=scene_descs)
        assert project.scene_descriptions == scene_descs

    def test_project_with_summary(self) -> None:
        """Test project with summary data."""
        summary = {"synopsis": "A great story.", "themes": ["Love", "Loss"]}
        project = Project(title="Test", logline="Test logline.", summary=summary)
        assert project.summary == summary

    def test_project_with_music(self) -> None:
        """Test project with music data."""
        music = {"main_theme": "Heroic fanfare", "instrumentation": "Orchestra"}
        project = Project(title="Test", logline="Test logline.", music=music)
        assert project.music == music

    def test_project_with_post_production(self) -> None:
        """Test project with post-production data."""
        post_prod = {"editing_plan": "Fast cuts", "color_grading": "Warm tones"}
        project = Project(title="Test", logline="Test logline.", post_production=post_prod)
        assert project.post_production == post_prod

    def test_project_with_marketing(self) -> None:
        """Test project with marketing data."""
        marketing = {"campaign_overview": "Social media blitz", "key_messages": ["Exciting", "New"]}
        project = Project(title="Test", logline="Test logline.", marketing=marketing)
        assert project.marketing == marketing

    def test_project_with_distribution(self) -> None:
        """Test project with distribution data."""
        distribution = {"release_strategy": "Streaming", "target_platforms": ["Netflix"]}
        project = Project(title="Test", logline="Test logline.", distribution=distribution)
        assert project.distribution == distribution


class TestJSONSchemaHelpers:
    """Tests for JSON schema helper functions."""

    def test_get_json_schema(self) -> None:
        """Test getting JSON schema for Project model."""
        schema = get_json_schema(Project)

        assert "title" in schema["properties"]
        assert "logline" in schema["properties"]
        assert "genre" in schema["properties"]
        assert "tone" in schema["properties"]
        assert "status" in schema["properties"]
        assert "required" in schema
        assert "title" in schema["required"]
        assert "logline" in schema["required"]

    def test_get_json_schema_has_properties(self) -> None:
        """Test that schema has all expected properties."""
        schema = get_json_schema(Project)
        properties = schema["properties"]

        expected_props = [
            "title", "logline", "genre", "tone",
            "created_at", "updated_at", "status",
            "beat_sheet", "characters", "script",
            "scene_descriptions", "summary", "music",
            "post_production", "marketing", "distribution",
        ]
        for prop in expected_props:
            assert prop in properties, f"Missing property: {prop}"

    def test_validate_json_with_schema_valid_data(self) -> None:
        """Test validating valid JSON data against schema."""
        data = {
            "title": "Valid Movie",
            "logline": "A valid logline.",
            "genre": "Action",
            "tone": "Exciting",
        }
        project = validate_json_with_schema(data, Project)
        assert isinstance(project, Project)
        assert project.title == "Valid Movie"
        assert project.logline == "A valid logline."

    def test_validate_json_with_schema_invalid_data(self) -> None:
        """Test validating invalid JSON data against schema."""
        data = {
            "title": "",  # Empty title should fail
            "logline": "A logline.",
        }
        with pytest.raises(ValueError):
            validate_json_with_schema(data, Project)

    def test_validate_json_with_schema_missing_required_field(self) -> None:
        """Test validating data missing required fields."""
        data = {
            "logline": "A logline.",
            # Missing title
        }
        with pytest.raises(ValueError):
            validate_json_with_schema(data, Project)

    def test_validate_json_with_schema_extra_fields(self) -> None:
        """Test that extra fields are ignored during validation."""
        data = {
            "title": "Test Movie",
            "logline": "Test logline.",
            "extra_field": "Should be ignored",
        }
        project = validate_json_with_schema(data, Project)
        assert project.title == "Test Movie"
        assert project.logline == "Test logline."
        # Extra fields should not be in the model
        assert not hasattr(project, "extra_field") or getattr(project, "extra_field", None) is None


class TestProjectIntegration:
    """Integration tests for Project model."""

    def test_project_lifecycle(self) -> None:
        """Test a full lifecycle of project creation and updates."""
        # Create project
        project = Project(title="Lifecycle Test", logline="Testing lifecycle.")
        assert project.status == "initialized"

        # Convert to dict and back
        d = project.to_dict()
        project2 = validate_json_with_schema(d, Project)
        assert project2.title == "Lifecycle Test"

        # Update status
        project2.update_status("in_progress")
        assert project2.status == "in_progress"

        # Convert to JSON and back
        json_str = project2.to_json()
        d2 = json.loads(json_str)
        project3 = validate_json_with_schema(d2, Project)
        assert project3.status == "in_progress"

    def test_project_with_complex_data(self) -> None:
        """Test project with complex nested data structures."""
        complex_data = {
            "title": "Complex Test",
            "logline": "Complex logline.",
            "beat_sheet": {
                "beats": [
                    {"beat_number": 1, "action": "Action 1", "dialogue": "Line 1", "emotion": "Happy"},
                    {"beat_number": 2, "action": "Action 2", "dialogue": None, "emotion": "Sad"},
                ]
            },
            "characters": {
                "characters": [
                    {"name": "Hero", "personality": ["Brave", "Smart"]},
                    {"name": "Villain", "personality": ["Cunning", "Ruthless"]},
                ]
            },
            "script": {
                "scenes": [
                    {"number": 1, "location": "Park", "description": "Meeting"},
                ]
            },
            "scene_descriptions": [
                {"number": 1, "visual_description": "Sunny day", "camera_directions": "Wide shot"},
            ],
            "summary": {"synopsis": "A story.", "themes": ["Friendship"]},
            "music": {"main_theme": "Theme", "leitmotifs": ["Hero theme"]},
            "post_production": {"editing_plan": "Plan", "vfx_requirements": "VFX"},
            "marketing": {"campaign_overview": "Campaign", "key_messages": ["Message"]},
            "distribution": {"release_strategy": "Theatrical", "target_platforms": ["Cinema"]},
        }

        project = validate_json_with_schema(complex_data, Project)

        assert project.beat_sheet["beats"][0]["beat_number"] == 1
        assert project.characters["characters"][0]["name"] == "Hero"
        assert project.script["scenes"][0]["number"] == 1
        assert project.scene_descriptions[0]["number"] == 1
        assert project.summary["synopsis"] == "A story."
        assert project.music["main_theme"] == "Theme"
        assert project.post_production["editing_plan"] == "Plan"
        assert project.marketing["campaign_overview"] == "Campaign"
        assert project.distribution["release_strategy"] == "Theatrical"
