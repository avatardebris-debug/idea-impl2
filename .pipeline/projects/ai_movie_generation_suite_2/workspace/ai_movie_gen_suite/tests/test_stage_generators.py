"""Tests for the stage generators module."""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from ai_movie_gen_suite.config import AppConfig, LLMConfig
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator
from ai_movie_gen_suite.stages.concept_generator import ConceptGenerator
from ai_movie_gen_suite.stages.beat_generator import BeatSheetGenerator
from ai_movie_gen_suite.stages.character_generator import CharacterGenerator
from ai_movie_gen_suite.stages.script_generator import ScriptGenerator
from ai_movie_gen_suite.stages.scene_generator import SceneDescriptionGenerator
from ai_movie_gen_suite.stages.summary_generator import SummaryGenerator
from ai_movie_gen_suite.stages.music_generator import MusicGenerator
from ai_movie_gen_suite.stages.post_production_generator import PostProductionGenerator
from ai_movie_gen_suite.stages.marketing_generator import MarketingGenerator
from ai_movie_gen_suite.stages.distribution_generator import DistributionGenerator


def _make_config(**overrides: Any) -> AppConfig:
    """Create an AppConfig with optional overrides."""
    llm = LLMConfig(
        provider=overrides.get("provider", "openai"),
        api_key=overrides.get("api_key", "test-key"),
        model=overrides.get("model", "gpt-4o"),
        use_json_mode=overrides.get("use_json_mode", True),
        temperature=overrides.get("temperature", 0.7),
        max_tokens=overrides.get("max_tokens", 4096),
        base_url=overrides.get("base_url"),
    )
    return AppConfig(
        llm=llm,
        output_dir=overrides.get("output_dir", "./output"),
        log_level=overrides.get("log_level", "INFO"),
        max_retries=overrides.get("max_retries", 3),
        retry_delay=overrides.get("retry_delay", 1.0),
        enable_cache=overrides.get("enable_cache", True),
        cache_ttl=overrides.get("cache_ttl", 3600),
    )


class TestBaseStageGenerator:
    """Tests for the BaseStageGenerator class."""

    def test_create_concrete_subclass(self) -> None:
        """Test that a concrete subclass can be instantiated."""
        config = _make_config()
        generator = ConceptGenerator(config=config)
        assert generator.config == config

    def test_base_class_cannot_be_instantiated(self) -> None:
        """Test that BaseStageGenerator cannot be instantiated directly."""
        config = _make_config()
        with pytest.raises(TypeError):
            BaseStageGenerator(config=config)

    def test_base_class_has_abstract_method(self) -> None:
        """Test that BaseStageGenerator defines get_stage_name."""
        config = _make_config()
        generator = ConceptGenerator(config=config)
        assert generator.get_stage_name() == "Concept Generator"

    def test_base_class_has_abstract_method_execute(self) -> None:
        """Test that BaseStageGenerator defines execute."""
        config = _make_config()
        generator = ConceptGenerator(config=config)
        assert callable(generator.execute)


class TestConceptGenerator:
    """Tests for the ConceptGenerator stage."""

    def test_get_stage_name(self) -> None:
        """Test getting the stage name."""
        config = _make_config()
        generator = ConceptGenerator(config=config)
        assert generator.get_stage_name() == "Concept Generator"

    @patch("ai_movie_gen_suite.stages.concept_generator.LLMClient")
    def test_execute_with_valid_project(self, mock_llm: MagicMock) -> None:
        """Test executing the concept generator with a valid project."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "title": "Test Movie",
            "logline": "A test logline.",
            "genre": "Sci-Fi",
            "tone": "Dark",
        })
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = ConceptGenerator(config=config)

        project = Project(title="Original Title", logline="Original logline.")
        result = generator.execute(project)

        assert result.title == "Test Movie"
        assert result.logline == "A test logline."
        assert result.genre == "Sci-Fi"
        assert result.tone == "Dark"

    @patch("ai_movie_gen_suite.stages.concept_generator.LLMClient")
    def test_execute_with_empty_response(self, mock_llm: MagicMock) -> None:
        """Test executing the concept generator with an empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = ConceptGenerator(config=config)

        project = Project(title="Original Title", logline="Original logline.")
        result = generator.execute(project)

        # Should return original project unchanged
        assert result.title == "Original Title"
        assert result.logline == "Original logline."

    @patch("ai_movie_gen_suite.stages.concept_generator.LLMClient")
    def test_execute_with_invalid_json(self, mock_llm: MagicMock) -> None:
        """Test executing the concept generator with invalid JSON."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Not valid JSON"
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = ConceptGenerator(config=config)

        project = Project(title="Original Title", logline="Original logline.")
        result = generator.execute(project)

        # Should return original project unchanged
        assert result.title == "Original Title"
        assert result.logline == "Original logline."

    @patch("ai_movie_gen_suite.stages.concept_generator.LLMClient")
    def test_execute_with_missing_fields(self, mock_llm: MagicMock) -> None:
        """Test executing the concept generator with missing required fields."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "title": "Test Movie",
            # Missing logline
        })
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = ConceptGenerator(config=config)

        project = Project(title="Original Title", logline="Original logline.")
        result = generator.execute(project)

        # Should return original project unchanged
        assert result.title == "Original Title"
        assert result.logline == "Original logline."


class TestBeatSheetGenerator:
    """Tests for the BeatSheetGenerator stage."""

    def test_get_stage_name(self) -> None:
        """Test getting the stage name."""
        config = _make_config()
        generator = BeatSheetGenerator(config=config)
        assert generator.get_stage_name() == "Beat Sheet Generator"

    @patch("ai_movie_gen_suite.stages.beat_generator.LLMClient")
    def test_execute_with_valid_project(self, mock_llm: MagicMock) -> None:
        """Test executing the beat sheet generator with a valid project."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "beats": [
                {"beat_number": 1, "action": "Opening scene", "emotion": "Excitement"},
                {"beat_number": 2, "action": "Conflict", "emotion": "Tension"},
            ]
        })
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = BeatSheetGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.beat_sheet is not None
        assert len(result.beat_sheet["beats"]) == 2
        assert result.beat_sheet["beats"][0]["beat_number"] == 1

    @patch("ai_movie_gen_suite.stages.beat_generator.LLMClient")
    def test_execute_with_empty_response(self, mock_llm: MagicMock) -> None:
        """Test executing the beat sheet generator with an empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = BeatSheetGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.beat_sheet is None


class TestCharacterGenerator:
    """Tests for the CharacterGenerator stage."""

    def test_get_stage_name(self) -> None:
        """Test getting the stage name."""
        config = _make_config()
        generator = CharacterGenerator(config=config)
        assert generator.get_stage_name() == "Character Generator"

    @patch("ai_movie_gen_suite.stages.character_generator.LLMClient")
    def test_execute_with_valid_project(self, mock_llm: MagicMock) -> None:
        """Test executing the character generator with a valid project."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "characters": [
                {"name": "Hero", "age": 30, "occupation": "Detective"},
                {"name": "Villain", "age": 45, "occupation": "Crime Lord"},
            ]
        })
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = CharacterGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.characters is not None
        assert len(result.characters["characters"]) == 2
        assert result.characters["characters"][0]["name"] == "Hero"

    @patch("ai_movie_gen_suite.stages.character_generator.LLMClient")
    def test_execute_with_empty_response(self, mock_llm: MagicMock) -> None:
        """Test executing the character generator with an empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = CharacterGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.characters is None


class TestScriptGenerator:
    """Tests for the ScriptGenerator stage."""

    def test_get_stage_name(self) -> None:
        """Test getting the stage name."""
        config = _make_config()
        generator = ScriptGenerator(config=config)
        assert generator.get_stage_name() == "Script Generator"

    @patch("ai_movie_gen_suite.stages.script_generator.LLMClient")
    def test_execute_with_valid_project(self, mock_llm: MagicMock) -> None:
        """Test executing the script generator with a valid project."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "scenes": [
                {"number": 1, "location": "Coffee Shop", "description": "Meeting scene"},
            ]
        })
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = ScriptGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.script is not None
        assert len(result.script["scenes"]) == 1
        assert result.script["scenes"][0]["number"] == 1

    @patch("ai_movie_gen_suite.stages.script_generator.LLMClient")
    def test_execute_with_empty_response(self, mock_llm: MagicMock) -> None:
        """Test executing the script generator with an empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = ScriptGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.script is None


class TestSceneDescriptionGenerator:
    """Tests for the SceneDescriptionGenerator stage."""

    def test_get_stage_name(self) -> None:
        """Test getting the stage name."""
        config = _make_config()
        generator = SceneDescriptionGenerator(config=config)
        assert generator.get_stage_name() == "Scene Description Generator"

    @patch("ai_movie_gen_suite.stages.scene_generator.LLMClient")
    def test_execute_with_valid_project(self, mock_llm: MagicMock) -> None:
        """Test executing the scene description generator with a valid project."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps([
            {"number": 1, "visual_description": "Bright morning", "camera_directions": "Wide shot"},
        ])
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = SceneDescriptionGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.scene_descriptions is not None
        assert len(result.scene_descriptions) == 1
        assert result.scene_descriptions[0]["number"] == 1

    @patch("ai_movie_gen_suite.stages.scene_generator.LLMClient")
    def test_execute_with_empty_response(self, mock_llm: MagicMock) -> None:
        """Test executing the scene description generator with an empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = SceneDescriptionGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.scene_descriptions is None


class TestSummaryGenerator:
    """Tests for the SummaryGenerator stage."""

    def test_get_stage_name(self) -> None:
        """Test getting the stage name."""
        config = _make_config()
        generator = SummaryGenerator(config=config)
        assert generator.get_stage_name() == "Summary Generator"

    @patch("ai_movie_gen_suite.stages.summary_generator.LLMClient")
    def test_execute_with_valid_project(self, mock_llm: MagicMock) -> None:
        """Test executing the summary generator with a valid project."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "synopsis": "A great story.",
            "themes": ["Love", "Loss"],
        })
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = SummaryGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.summary is not None
        assert result.summary["synopsis"] == "A great story."

    @patch("ai_movie_gen_suite.stages.summary_generator.LLMClient")
    def test_execute_with_empty_response(self, mock_llm: MagicMock) -> None:
        """Test executing the summary generator with an empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = SummaryGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.summary is None


class TestMusicGenerator:
    """Tests for the MusicGenerator stage."""

    def test_get_stage_name(self) -> None:
        """Test getting the stage name."""
        config = _make_config()
        generator = MusicGenerator(config=config)
        assert generator.get_stage_name() == "Music Generator"

    @patch("ai_movie_gen_suite.stages.music_generator.LLMClient")
    def test_execute_with_valid_project(self, mock_llm: MagicMock) -> None:
        """Test executing the music generator with a valid project."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "soundtrack": [{"track": "Main Theme", "mood": "Epic"}],
        })
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = MusicGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.music is not None
        assert len(result.music["soundtrack"]) == 1

    @patch("ai_movie_gen_suite.stages.music_generator.LLMClient")
    def test_execute_with_empty_response(self, mock_llm: MagicMock) -> None:
        """Test executing the music generator with an empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = MusicGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.music is None


class TestPostProductionGenerator:
    """Tests for the PostProductionGenerator stage."""

    def test_get_stage_name(self) -> None:
        """Test getting the stage name."""
        config = _make_config()
        generator = PostProductionGenerator(config=config)
        assert generator.get_stage_name() == "Post-Production Generator"

    @patch("ai_movie_gen_suite.stages.post_production_generator.LLMClient")
    def test_execute_with_valid_project(self, mock_llm: MagicMock) -> None:
        """Test executing the post-production generator with a valid project."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "effects": [{"type": "VFX", "description": "Explosion"}],
        })
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = PostProductionGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.post_production is not None
        assert len(result.post_production["effects"]) == 1

    @patch("ai_movie_gen_suite.stages.post_production_generator.LLMClient")
    def test_execute_with_empty_response(self, mock_llm: MagicMock) -> None:
        """Test executing the post-production generator with an empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = PostProductionGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.post_production is None


class TestMarketingGenerator:
    """Tests for the MarketingGenerator stage."""

    def test_get_stage_name(self) -> None:
        """Test getting the stage name."""
        config = _make_config()
        generator = MarketingGenerator(config=config)
        assert generator.get_stage_name() == "Marketing Generator"

    @patch("ai_movie_gen_suite.stages.marketing_generator.LLMClient")
    def test_execute_with_valid_project(self, mock_llm: MagicMock) -> None:
        """Test executing the marketing generator with a valid project."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "tagline": "A great tagline.",
            "poster_description": "Epic poster.",
        })
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = MarketingGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.marketing is not None
        assert result.marketing["tagline"] == "A great tagline."

    @patch("ai_movie_gen_suite.stages.marketing_generator.LLMClient")
    def test_execute_with_empty_response(self, mock_llm: MagicMock) -> None:
        """Test executing the marketing generator with an empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = MarketingGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.marketing is None


class TestDistributionGenerator:
    """Tests for the DistributionGenerator stage."""

    def test_get_stage_name(self) -> None:
        """Test getting the stage name."""
        config = _make_config()
        generator = DistributionGenerator(config=config)
        assert generator.get_stage_name() == "Distribution Generator"

    @patch("ai_movie_gen_suite.stages.distribution_generator.LLMClient")
    def test_execute_with_valid_project(self, mock_llm: MagicMock) -> None:
        """Test executing the distribution generator with a valid project."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "platforms": ["Netflix", "Amazon Prime"],
            "strategy": "Wide release.",
        })
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = DistributionGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.distribution is not None
        assert len(result.distribution["platforms"]) == 2

    @patch("ai_movie_gen_suite.stages.distribution_generator.LLMClient")
    def test_execute_with_empty_response(self, mock_llm: MagicMock) -> None:
        """Test executing the distribution generator with an empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.generate.return_value = mock_response
        mock_llm.return_value = mock_client

        config = _make_config()
        generator = DistributionGenerator(config=config)

        project = Project(title="Test Movie", logline="Test logline.")
        result = generator.execute(project)

        assert result.distribution is None
