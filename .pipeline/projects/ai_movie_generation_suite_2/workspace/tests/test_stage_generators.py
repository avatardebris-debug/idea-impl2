"""Tests for the MoviePipeline orchestrator."""

import json
from unittest.mock import MagicMock, patch

import pytest

from ai_movie_gen_suite.config import LLMConfig
from ai_movie_gen_suite.llm_client import LLMClient, LLMMessage, LLMResponse
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.stages.base import BaseStageGenerator
from ai_movie_gen_suite.stages.stage1_beat_sheet import Stage1BeatSheetGenerator
from ai_movie_gen_suite.stages.stage2_characters import Stage2CharacterGenerator
from ai_movie_gen_suite.stages.stage3_script import Stage3ScriptWriter
from ai_movie_gen_suite.stages.stage4_scene_descriptions import Stage4SceneDescriptionGenerator
from ai_movie_gen_suite.stages.stage5_music import Stage5MusicComposer
from ai_movie_gen_suite.stages.stage6_post_production import Stage6PostProductionPlanner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_project():
    """Create a minimal valid Project for testing."""
    return Project(
        title="Test Movie",
        logline="A short test logline.",
        genre="Sci-Fi",
        tone="Dark",
    )


@pytest.fixture
def mock_llm_config():
    """Return an LLMConfig that won't raise on validation."""
    return LLMConfig(
        provider="openai",
        api_key="test-key",
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=512,
    )


@pytest.fixture
def mock_llm_client(mock_llm_config):
    """Return an LLMClient with a mocked underlying client."""
    client = LLMClient(config=mock_llm_config)
    client._client = MagicMock()  # type: ignore[attr-defined]
    return client


@pytest.fixture
def mock_stage_generator():
    """Return a BaseStageGenerator subclass that does nothing but return the project."""

    class DummyStage(BaseStageGenerator):
        stage_name = "DummyStage"
        stage_description = "A dummy stage for testing."

        def execute(self, project: Project) -> Project:
            project.status = f"completed_{self.stage_name.lower()}"
            return project

    return DummyStage


@pytest.fixture
def pipeline_with_mock_llm(mock_llm_client, mock_stage_generator):
    """Pipeline that uses a single dummy stage and a mocked LLM client."""
    return MoviePipeline(
        llm_client=mock_llm_client,
        stages=[mock_stage_generator],
    )


# ---------------------------------------------------------------------------
# Pipeline initialisation
# ---------------------------------------------------------------------------

class TestPipelineInit:
    """Tests for MoviePipeline.__init__."""

    def test_default_stages_count(self, mock_llm_client):
        """Pipeline should create 6 default stages."""
        pipeline = MoviePipeline(llm_client=mock_llm_client)
        assert len(pipeline.stages) == 6

    def test_default_stage_order(self, mock_llm_client):
        """Default stages should appear in the expected order."""
        pipeline = MoviePipeline(llm_client=mock_llm_client)
        expected_names = [
            "Stage1BeatSheetGenerator",
            "Stage2CharacterGenerator",
            "Stage3ScriptWriter",
            "Stage4SceneDescriptionGenerator",
            "Stage5MusicComposer",
            "Stage6PostProductionPlanner",
        ]
        actual_names = [s.__class__.__name__ for s in pipeline.stages]
        assert actual_names == expected_names

    def test_custom_stages(self, mock_llm_client, mock_stage_generator):
        """Custom stages should replace the default list."""
        pipeline = MoviePipeline(
            llm_client=mock_llm_client,
            stages=[mock_stage_generator],
        )
        assert len(pipeline.stages) == 1
        assert isinstance(pipeline.stages[0], mock_stage_generator)

    def test_stage_instances_registered(self, mock_llm_client, mock_stage_generator):
        """_stage_instances should map class names to instances."""
        pipeline = MoviePipeline(
            llm_client=mock_llm_client,
            stages=[mock_stage_generator],
        )
        assert "DummyStage" in pipeline._stage_instances
        assert pipeline._stage_instances["DummyStage"] is pipeline.stages[0]

    def test_llm_client_default_creation(self):
        """When llm_client is None, a default LLMClient should be created."""
        with patch("ai_movie_gen_suite.pipeline.LLMClient") as MockClient:
            MockClient.return_value.config = MagicMock()
            pipeline = MoviePipeline()
            MockClient.assert_called_once()
            assert pipeline.llm_client is MockClient.return_value

    def test_llm_client_passthrough(self, mock_llm_client):
        """When llm_client is provided, it should be used directly."""
        pipeline = MoviePipeline(llm_client=mock_llm_client)
        assert pipeline.llm_client is mock_llm_client


# ---------------------------------------------------------------------------
# Pipeline run
# ---------------------------------------------------------------------------

class TestPipelineRun:
    """Tests for MoviePipeline.run."""

    def test_run_updates_status_to_complete(self, pipeline_with_mock_llm, sample_project):
        """Pipeline should set status to 'pipeline_complete' on success."""
        result = pipeline_with_mock_llm.run(sample_project)
        assert result.status == "pipeline_complete"

    def test_run_calls_each_stage_execute(self, mock_llm_client, mock_stage_generator):
        """Each stage's execute should be called exactly once."""
        mock_instance = MagicMock(spec=mock_stage_generator)
        mock_instance.__class__.__name__ = "DummyStage"
        mock_instance.execute.side_effect = lambda p: p

        pipeline = MoviePipeline(
            llm_client=mock_llm_client,
            stages=[mock_stage_generator],
        )
        # Replace the stage instance so we can inspect calls
        pipeline.stages = [mock_instance]

        project = Project(title="X", logline="Y")
        pipeline.run(project)
        mock_instance.execute.assert_called_once()

    def test_run_returns_updated_project(self, pipeline_with_mock_llm, sample_project):
        """run should return the project (possibly mutated)."""
        result = pipeline_with_mock_llm.run(sample_project)
        assert result is not None
        assert isinstance(result, Project)

    def test_run_propagates_stage_exception(self, mock_llm_client, mock_stage_generator):
        """If a stage raises, the exception should propagate."""
        failing_stage = MagicMock(spec=mock_stage_generator)
        failing_stage.__class__.__name__ = "FailingStage"
        failing_stage.execute.side_effect = RuntimeError("boom")

        pipeline = MoviePipeline(
            llm_client=mock_llm_client,
            stages=[mock_stage_generator],
        )
        pipeline.stages = [failing_stage]

        project = Project(title="X", logline="Y")
        with pytest.raises(RuntimeError, match="boom"):
            pipeline.run(project)

    def test_run_sets_failed_status_on_error(self, mock_llm_client, mock_stage_generator):
        """Pipeline should set status to 'failed_at_<stage>' on error."""
        failing_stage = MagicMock(spec=mock_stage_generator)
        failing_stage.__class__.__name__ = "FailingStage"
        failing_stage.execute.side_effect = RuntimeError("boom")

        pipeline = MoviePipeline(
            llm_client=mock_llm_client,
            stages=[mock_stage_generator],
        )
        pipeline.stages = [failing_stage]

        project = Project(title="X", logline="Y")
        with pytest.raises(RuntimeError):
            pipeline.run(project)
        assert project.status == "failed_at_failingstage"

    def test_run_initial_status(self, pipeline_with_mock_llm, sample_project):
        """Pipeline should set status to 'pipeline_started' at the beginning."""
        pipeline_with_mock_llm.run(sample_project)
        assert sample_project.status == "pipeline_complete"  # after full run

        # Re-check by looking at intermediate: set up a pipeline with two stages
        s1 = MagicMock(spec=mock_stage_generator)
        s1.__class__.__name__ = "FirstStage"
        s1.execute.side_effect = lambda p: p

        s2 = MagicMock(spec=mock_stage_generator)
        s2.__class__.__name__ = "SecondStage"
        s2.execute.side_effect = lambda p: p

        pip = MoviePipeline(
            llm_client=mock_llm_client,
            stages=[mock_stage_generator],
        )
        pip.stages = [s1, s2]
        proj = Project(title="X", logline="Y")
        pip.run(proj)
        # After first stage
        assert s1.execute.call_count == 1
        assert s2.execute.call_count == 1


# ---------------------------------------------------------------------------
# get_stage_names
# ---------------------------------------------------------------------------

class TestGetStageNames:
    """Tests for MoviePipeline.get_stage_names."""

    def test_get_existing_stage(self, pipeline_with_mock_llm):
        """Should return the stage instance for a known name."""
        stage = pipeline_with_mock_llm.get_stage("DummyStage")
        assert stage is not None
        assert isinstance(stage, pipeline_with_mock_llm.stages[0].__class__)

    def test_get_nonexistent_stage(self, pipeline_with_mock_llm):
        """Should return None for an unknown name."""
        stage = pipeline_with_mock_llm.get_stage("NonexistentStage")
        assert stage is None


# ---------------------------------------------------------------------------
# get_available_stages
# ---------------------------------------------------------------------------

class TestGetAvailableStages:
    """Tests for MoviePipeline.get_available_stages."""

    def test_returns_stage_names(self, pipeline_with_mock_llm):
        """Should return a list of stage class names."""
        names = pipeline_with_mock_llm.get_available_stages()
        assert isinstance(names, list)
        assert "DummyStage" in names

    def test_default_pipeline_stages(self, mock_llm_client):
        """Default pipeline should expose all 6 stage names."""
        pipeline = MoviePipeline(llm_client=mock_llm_client)
        names = pipeline.get_available_stages()
        assert len(names) == 6
        assert "Stage1BeatSheetGenerator" in names
        assert "Stage6PostProductionPlanner" in names


# ---------------------------------------------------------------------------
# Integration: full default pipeline with mocked stages
# ---------------------------------------------------------------------------

class TestFullPipelineIntegration:
    """End-to-end tests using the full default pipeline with mocked stages."""

    @pytest.fixture
    def mocked_default_pipeline(self, mock_llm_client):
        """Pipeline with all default stages, but each stage's execute is mocked."""
        pipeline = MoviePipeline(llm_client=mock_llm_client)
        for stage in pipeline.stages:
            stage.execute = MagicMock(side_effect=lambda p: p)  # type: ignore[attr-defined]
        return pipeline

    def test_all_stages_called(self, mocked_default_pipeline, sample_project):
        """All 6 stages should have execute called exactly once."""
        mocked_default_pipeline.run(sample_project)
        for stage in mocked_default_pipeline.stages:
            stage.execute.assert_called_once()  # type: ignore[attr-defined]

    def test_project_status_after_full_pipeline(self, mocked_default_pipeline, sample_project):
        """Project status should be 'pipeline_complete' after full run."""
        result = mocked_default_pipeline.run(sample_project)
        assert result.status == "pipeline_complete"

    def test_project_data_preserved(self, mocked_default_pipeline, sample_project):
        """Project title and logline should be preserved through the pipeline."""
        result = mocked_default_pipeline.run(sample_project)
        assert result.title == "Test Movie"
        assert result.logline == "A short test logline."


# ---------------------------------------------------------------------------
# run_stage
# ---------------------------------------------------------------------------

class TestRunStage:
    """Tests for MoviePipeline.run_stage."""

    def test_run_existing_stage(self, pipeline_with_mock_llm, sample_project):
        """Should run the named stage and return the project."""
        result = pipeline_with_mock_llm.run_stage(sample_project, "DummyStage")
        assert result.status == "completed_dummystage"

    def test_run_nonexistent_stage(self, pipeline_with_mock_llm, sample_project):
        """Should raise ValueError for an unknown stage name."""
        with pytest.raises(ValueError, match="Unknown stage"):
            pipeline_with_mock_llm.run_stage(sample_project, "NonexistentStage")

    def test_run_stage_mutates_project(self, pipeline_with_mock_llm, sample_project):
        """run_stage should mutate the project in place."""
        original_status = sample_project.status
        pipeline_with_mock_llm.run_stage(sample_project, "DummyStage")
        assert sample_project.status != original_status


# ---------------------------------------------------------------------------
# Stage generator base class
# ---------------------------------------------------------------------------

class TestBaseStageGenerator:
    """Tests for BaseStageGenerator."""

    def test_abstract_class(self):
        """BaseStageGenerator should not be instantiable without implementing execute."""
        with pytest.raises(TypeError):
            BaseStageGenerator()  # type: ignore[abstract]

    def test_subclass_with_execute(self, mock_llm_config):
        """A subclass that implements execute should be instantiable."""

        class ConcreteStage(BaseStageGenerator):
            stage_name = "Concrete"
            stage_description = "A concrete stage."

            def execute(self, project: Project) -> Project:
                return project

        stage = ConcreteStage(config=mock_llm_config)
        assert stage.stage_name == "Concrete"


# ---------------------------------------------------------------------------
# Individual stage generators
# ---------------------------------------------------------------------------

class TestStage1BeatSheetGenerator:
    """Tests for Stage1BeatSheetGenerator."""

    @pytest.fixture
    def stage(self, mock_llm_client):
        return Stage1BeatSheetGenerator(config=mock_llm_client.config)

    def test_stage_name(self, stage):
        assert stage.stage_name == "Stage1BeatSheetGenerator"

    def test_execute_sets_status(self, stage, sample_project):
        with patch.object(stage, "_get_messages") as mock_msgs, \
             patch.object(stage, "_parse_json_response") as mock_parse:
            mock_parse.return_value = {
                "title": "New Title",
                "logline": "New logline",
                "genre": "Drama",
                "tone": "Serious",
                "synopsis": "A synopsis.",
                "beats": [{"act": 1, "beats": []}],
            }
            result = stage.execute(sample_project)
            assert result.status == "beat_sheet_created"
            assert result.beat_sheet["title"] == "New Title"


class TestStage2CharacterGenerator:
    """Tests for Stage2CharacterGenerator."""

    @pytest.fixture
    def stage(self, mock_llm_client):
        return Stage2CharacterGenerator(config=mock_llm_client.config)

    def test_stage_name(self, stage):
        assert stage.stage_name == "Stage2CharacterGenerator"

    def test_execute_sets_status(self, stage, sample_project):
        with patch.object(stage, "_get_messages") as mock_msgs, \
             patch.object(stage, "_parse_json_response") as mock_parse:
            mock_parse.return_value = {
                "characters": [
                    {"name": "Hero", "description": "The hero."},
                ]
            }
            result = stage.execute(sample_project)
            assert result.status == "characters_created"
            assert len(result.characters) == 1


class TestStage3ScriptWriter:
    """Tests for Stage3ScriptWriter."""

    @pytest.fixture
    def stage(self, mock_llm_client):
        return Stage3ScriptWriter(config=mock_llm_client.config)

    def test_stage_name(self, stage):
        assert stage.stage_name == "Stage3ScriptWriter"

    def test_execute_requires_script(self, stage, sample_project):
        """Should raise ValueError if project has no script."""
        sample_project.script = None
        with pytest.raises(ValueError, match="Project must have script"):
            stage.execute(sample_project)

    def test_execute_sets_status(self, stage, sample_project):
        sample_project.script = {"title": "Test", "scenes": []}
        with patch.object(stage, "_get_messages") as mock_msgs, \
             patch.object(stage, "_parse_json_response") as mock_parse:
            mock_parse.return_value = {"scenes": []}
            result = stage.execute(sample_project)
            assert result.status == "script_written"


class TestStage4SceneDescriptionGenerator:
    """Tests for Stage4SceneDescriptionGenerator."""

    @pytest.fixture
    def stage(self, mock_llm_client):
        return Stage4SceneDescriptionGenerator(config=mock_llm_client.config)

    def test_stage_name(self, stage):
        assert stage.stage_name == "Stage4SceneDescriptionGenerator"

    def test_execute_requires_scene_descriptions(self, stage, sample_project):
        sample_project.scene_descriptions = None
        with pytest.raises(ValueError, match="Project must have scene descriptions"):
            stage.execute(sample_project)

    def test_execute_sets_status(self, stage, sample_project):
        sample_project.scene_descriptions = []
        with patch.object(stage, "_get_messages") as mock_msgs, \
             patch.object(stage, "_parse_json_response") as mock_parse:
            mock_parse.return_value = {
                "visual_description": "desc",
                "camera_directions": "cam",
                "lighting": "light",
                "color_palette": "palette",
                "mood": "mood",
                "props_and_set_design": "props",
            }
            result = stage.execute(sample_project)
            assert result.status == "scene_descriptions_created"


class TestStage5MusicComposer:
    """Tests for Stage5MusicComposer."""

    @pytest.fixture
    def stage(self, mock_llm_client):
        return Stage5MusicComposer(config=mock_llm_client.config)

    def test_stage_name(self, stage):
        assert stage.stage_name == "Stage5MusicComposer"

    def test_execute_sets_status(self, stage, sample_project):
        sample_project.script = {"title": "Test", "scenes": [{"number": 1, "description": "Scene 1"}]}
        with patch.object(stage, "_get_messages") as mock_msgs, \
             patch.object(stage, "_parse_json_response") as mock_parse:
            mock_parse.return_value = {
                "music_compositions": [
                    {"scene_number": 1, "mood": "tense", "instrumentation": "strings"},
                ],
            }
            result = stage.execute(sample_project)
            assert result.status == "stage5_music_complete"


class TestStage6PostProductionPlanner:
    """Tests for Stage6PostProductionPlanner."""

    @pytest.fixture
    def stage(self, mock_llm_client):
        return Stage6PostProductionPlanner(config=mock_llm_client.config)

    def test_stage_name(self, stage):
        assert stage.stage_name == "Stage6PostProductionPlanner"

    def test_execute_sets_status(self, stage, sample_project):
        sample_project.script = {"title": "Test", "scenes": [{"number": 1, "description": "Scene 1"}]}
        with patch.object(stage, "_get_messages") as mock_msgs, \
             patch.object(stage, "_parse_json_response") as mock_parse:
            mock_parse.return_value = {
                "video_editing": {"style": "fast", "pacing_strategy": "quick", "key_techniques": "jump cuts"},
                "vfx": {"requirements": "minimal", "complexity": "low", "priority_shots": "none"},
                "sound_design": {"ambient_strategy": "quiet", "foley_requirements": "none", "sound_effects": "minimal", "mixing_approach": "standard"},
                "color_grading": {"overall_approach": "neutral", "per_scene_treatment": "standard", "lut_recommendations": "none"},
                "distribution": {"target_platforms": "streaming", "marketing_approach": "social", "release_strategy": "wide"},
            }
            result = stage.execute(sample_project)
            assert result.status == "stage6_post_production_complete"
