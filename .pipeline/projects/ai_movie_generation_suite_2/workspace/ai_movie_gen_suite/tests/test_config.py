"""Tests for the AI Movie Generation Suite configuration."""

import pytest
import os
from unittest.mock import patch
from ai_movie_gen_suite.config import (
    AppConfig,
    LLMConfig,
    PipelineConfig,
    VideoConfig,
    StorageConfig,
)


class TestLLMConfig:
    """Tests for the LLMConfig class."""

    def test_create_llm_config_defaults(self):
        """Test LLMConfig with default values."""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.api_key is None
        assert config.base_url is None

    def test_create_llm_config_with_values(self):
        """Test LLMConfig with custom values."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3-opus",
            temperature=0.8,
            max_tokens=8192,
            api_key="test_key",
            base_url="https://api.anthropic.com",
        )
        assert config.provider == "anthropic"
        assert config.model == "claude-3-opus"
        assert config.temperature == 0.8
        assert config.max_tokens == 8192
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.anthropic.com"

    def test_llm_config_to_dict(self):
        """Test LLMConfig serialization."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4096,
            api_key="test_key",
            base_url="https://api.openai.com",
        )
        data = config.to_dict()
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4o"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 4096
        assert data["api_key"] == "test_key"
        assert data["base_url"] == "https://api.openai.com"

    def test_llm_config_from_dict(self):
        """Test LLMConfig deserialization."""
        data = {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 4096,
            "api_key": "test_key",
            "base_url": "https://api.openai.com",
        }
        config = LLMConfig.from_dict(data)
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.openai.com"

    def test_llm_config_from_dict_partial(self):
        """Test LLMConfig deserialization with partial data."""
        data = {"provider": "openai"}
        config = LLMConfig.from_dict(data)
        assert config.provider == "openai"
        assert config.model == "gpt-4o"  # default
        assert config.temperature == 0.7  # default

    def test_llm_config_from_dict_empty(self):
        """Test LLMConfig deserialization with empty data."""
        config = LLMConfig.from_dict({})
        assert config.provider == "openai"  # default
        assert config.model == "gpt-4o"  # default

    def test_llm_config_from_dict_with_none_values(self):
        """Test LLMConfig deserialization with None values."""
        data = {
            "provider": None,
            "model": None,
            "temperature": None,
            "max_tokens": None,
            "api_key": None,
            "base_url": None,
        }
        config = LLMConfig.from_dict(data)
        assert config.provider == "openai"  # default
        assert config.model == "gpt-4o"  # default
        assert config.temperature == 0.7  # default
        assert config.max_tokens == 4096  # default
        assert config.api_key is None
        assert config.base_url is None


class TestVideoConfig:
    """Tests for the VideoConfig class."""

    def test_create_video_config_defaults(self):
        """Test VideoConfig with default values."""
        config = VideoConfig()
        assert config.resolution == "1080p"
        assert config.frame_rate == 24
        assert config.aspect_ratio == "16:9"
        assert config.output_format == "mp4"
        assert config.quality == "high"
        assert config.duration_seconds == 300

    def test_create_video_config_with_values(self):
        """Test VideoConfig with custom values."""
        config = VideoConfig(
            resolution="4K",
            frame_rate=30,
            aspect_ratio="21:9",
            output_format="mov",
            quality="ultra",
            duration_seconds=600,
        )
        assert config.resolution == "4K"
        assert config.frame_rate == 30
        assert config.aspect_ratio == "21:9"
        assert config.output_format == "mov"
        assert config.quality == "ultra"
        assert config.duration_seconds == 600

    def test_video_config_to_dict(self):
        """Test VideoConfig serialization."""
        config = VideoConfig(
            resolution="4K",
            frame_rate=30,
            aspect_ratio="21:9",
            output_format="mov",
            quality="ultra",
            duration_seconds=600,
        )
        data = config.to_dict()
        assert data["resolution"] == "4K"
        assert data["frame_rate"] == 30
        assert data["aspect_ratio"] == "21:9"
        assert data["output_format"] == "mov"
        assert data["quality"] == "ultra"
        assert data["duration_seconds"] == 600

    def test_video_config_from_dict(self):
        """Test VideoConfig deserialization."""
        data = {
            "resolution": "4K",
            "frame_rate": 30,
            "aspect_ratio": "21:9",
            "output_format": "mov",
            "quality": "ultra",
            "duration_seconds": 600,
        }
        config = VideoConfig.from_dict(data)
        assert config.resolution == "4K"
        assert config.frame_rate == 30
        assert config.aspect_ratio == "21:9"
        assert config.output_format == "mov"
        assert config.quality == "ultra"
        assert config.duration_seconds == 600

    def test_video_config_from_dict_partial(self):
        """Test VideoConfig deserialization with partial data."""
        data = {"resolution": "4K"}
        config = VideoConfig.from_dict(data)
        assert config.resolution == "4K"
        assert config.frame_rate == 24  # default

    def test_video_config_from_dict_empty(self):
        """Test VideoConfig deserialization with empty data."""
        config = VideoConfig.from_dict({})
        assert config.resolution == "1080p"  # default
        assert config.frame_rate == 24  # default


class TestStorageConfig:
    """Tests for the StorageConfig class."""

    def test_create_storage_config_defaults(self):
        """Test StorageConfig with default values."""
        config = StorageConfig()
        assert config.type == "local"
        assert config.path == "./storage"
        assert config.bucket_name is None
        assert config.region is None

    def test_create_storage_config_with_values(self):
        """Test StorageConfig with custom values."""
        config = StorageConfig(
            type="s3",
            bucket_name="my-bucket",
            region="us-east-1",
        )
        assert config.type == "s3"
        assert config.path == "./storage"  # default
        assert config.bucket_name == "my-bucket"
        assert config.region == "us-east-1"

    def test_storage_config_to_dict(self):
        """Test StorageConfig serialization."""
        config = StorageConfig(
            type="s3",
            bucket_name="my-bucket",
            region="us-east-1",
        )
        data = config.to_dict()
        assert data["type"] == "s3"
        assert data["path"] == "./storage"
        assert data["bucket_name"] == "my-bucket"
        assert data["region"] == "us-east-1"

    def test_storage_config_from_dict(self):
        """Test StorageConfig deserialization."""
        data = {
            "type": "s3",
            "bucket_name": "my-bucket",
            "region": "us-east-1",
        }
        config = StorageConfig.from_dict(data)
        assert config.type == "s3"
        assert config.bucket_name == "my-bucket"
        assert config.region == "us-east-1"

    def test_storage_config_from_dict_partial(self):
        """Test StorageConfig deserialization with partial data."""
        data = {"type": "s3"}
        config = StorageConfig.from_dict(data)
        assert config.type == "s3"
        assert config.bucket_name is None  # default

    def test_storage_config_from_dict_empty(self):
        """Test StorageConfig deserialization with empty data."""
        config = StorageConfig.from_dict({})
        assert config.type == "local"  # default
        assert config.path == "./storage"  # default


class TestPipelineConfig:
    """Tests for the PipelineConfig class."""

    def test_create_pipeline_config_defaults(self):
        """Test PipelineConfig with default values."""
        config = PipelineConfig()
        assert config.llm is not None
        assert config.video is not None
        assert config.storage is not None
        assert config.max_retries == 3
        assert config.timeout_seconds == 300
        assert config.parallel_processing is False
        assert config.enable_cache is True

    def test_create_pipeline_config_with_values(self):
        """Test PipelineConfig with custom values."""
        llm_config = LLMConfig(provider="anthropic", model="claude-3-opus")
        video_config = VideoConfig(resolution="4K", frame_rate=30)
        storage_config = StorageConfig(type="s3", bucket_name="my-bucket")

        config = PipelineConfig(
            llm=llm_config,
            video=video_config,
            storage=storage_config,
            max_retries=5,
            timeout_seconds=600,
            parallel_processing=True,
            enable_cache=False,
        )
        assert config.llm.provider == "anthropic"
        assert config.video.resolution == "4K"
        assert config.storage.type == "s3"
        assert config.max_retries == 5
        assert config.timeout_seconds == 600
        assert config.parallel_processing is True
        assert config.enable_cache is False

    def test_pipeline_config_to_dict(self):
        """Test PipelineConfig serialization."""
        config = PipelineConfig(
            max_retries=5,
            timeout_seconds=600,
            parallel_processing=True,
            enable_cache=False,
        )
        data = config.to_dict()
        assert "llm" in data
        assert "video" in data
        assert "storage" in data
        assert data["max_retries"] == 5
        assert data["timeout_seconds"] == 600
        assert data["parallel_processing"] is True
        assert data["enable_cache"] is False

    def test_pipeline_config_from_dict(self):
        """Test PipelineConfig deserialization."""
        data = {
            "llm": {
                "provider": "anthropic",
                "model": "claude-3-opus",
            },
            "video": {
                "resolution": "4K",
                "frame_rate": 30,
            },
            "storage": {
                "type": "s3",
                "bucket_name": "my-bucket",
            },
            "max_retries": 5,
            "timeout_seconds": 600,
            "parallel_processing": True,
            "enable_cache": False,
        }
        config = PipelineConfig.from_dict(data)
        assert config.llm.provider == "anthropic"
        assert config.video.resolution == "4K"
        assert config.storage.type == "s3"
        assert config.max_retries == 5
        assert config.timeout_seconds == 600
        assert config.parallel_processing is True
        assert config.enable_cache is False

    def test_pipeline_config_from_dict_partial(self):
        """Test PipelineConfig deserialization with partial data."""
        data = {"max_retries": 5}
        config = PipelineConfig.from_dict(data)
        assert config.max_retries == 5
        assert config.llm.provider == "openai"  # default

    def test_pipeline_config_from_dict_empty(self):
        """Test PipelineConfig deserialization with empty data."""
        config = PipelineConfig.from_dict({})
        assert config.llm.provider == "openai"  # default
        assert config.max_retries == 3  # default


class TestAppConfig:
    """Tests for the AppConfig class."""

    def test_create_app_config_defaults(self):
        """Test AppConfig with default values."""
        config = AppConfig()
        assert config.pipeline is not None
        assert config.project_name == "Untitled Project"
        assert config.output_dir == "./output"
        assert config.log_level == "INFO"

    def test_create_app_config_with_values(self):
        """Test AppConfig with custom values."""
        pipeline_config = PipelineConfig(max_retries=5)
        config = AppConfig(
            pipeline=pipeline_config,
            project_name="My Movie",
            output_dir="./my_output",
            log_level="DEBUG",
        )
        assert config.pipeline.max_retries == 5
        assert config.project_name == "My Movie"
        assert config.output_dir == "./my_output"
        assert config.log_level == "DEBUG"

    def test_app_config_to_dict(self):
        """Test AppConfig serialization."""
        config = AppConfig(
            project_name="My Movie",
            output_dir="./my_output",
            log_level="DEBUG",
        )
        data = config.to_dict()
        assert "pipeline" in data
        assert data["project_name"] == "My Movie"
        assert data["output_dir"] == "./my_output"
        assert data["log_level"] == "DEBUG"

    def test_app_config_from_dict(self):
        """Test AppConfig deserialization."""
        data = {
            "pipeline": {
                "llm": {"provider": "anthropic"},
                "video": {"resolution": "4K"},
                "storage": {"type": "s3"},
                "max_retries": 5,
            },
            "project_name": "My Movie",
            "output_dir": "./my_output",
            "log_level": "DEBUG",
        }
        config = AppConfig.from_dict(data)
        assert config.pipeline.llm.provider == "anthropic"
        assert config.pipeline.video.resolution == "4K"
        assert config.pipeline.storage.type == "s3"
        assert config.pipeline.max_retries == 5
        assert config.project_name == "My Movie"
        assert config.output_dir == "./my_output"
        assert config.log_level == "DEBUG"

    def test_app_config_from_dict_partial(self):
        """Test AppConfig deserialization with partial data."""
        data = {"project_name": "My Movie"}
        config = AppConfig.from_dict(data)
        assert config.project_name == "My Movie"
        assert config.pipeline.llm.provider == "openai"  # default

    def test_app_config_from_dict_empty(self):
        """Test AppConfig deserialization with empty data."""
        config = AppConfig.from_dict({})
        assert config.project_name == "Untitled Project"  # default
        assert config.pipeline.llm.provider == "openai"  # default

    @patch.dict(os.environ, {"AI_MOVIE_GEN_SUITE_CONFIG": '{"project_name": "Env Project"}'})
    def test_app_config_from_env(self):
        """Test AppConfig loading from environment variable."""
        config = AppConfig.from_env()
        assert config.project_name == "Env Project"

    @patch.dict(os.environ, {}, clear=True)
    def test_app_config_from_env_no_config(self):
        """Test AppConfig loading from environment variable with no config."""
        config = AppConfig.from_env()
        assert config.project_name == "Untitled Project"  # default

    def test_app_config_from_file(self, tmp_path):
        """Test AppConfig loading from file."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"project_name": "File Project"}')
        config = AppConfig.from_file(str(config_file))
        assert config.project_name == "File Project"

    def test_app_config_from_file_invalid_json(self, tmp_path):
        """Test AppConfig loading from file with invalid JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json")
        with pytest.raises(Exception):
            AppConfig.from_file(str(config_file))

    def test_app_config_from_file_not_found(self):
        """Test AppConfig loading from file that doesn't exist."""
        with pytest.raises(Exception):
            AppConfig.from_file("/nonexistent/path/config.json")

    def test_app_config_merge(self):
        """Test AppConfig merging."""
        config1 = AppConfig(project_name="Project 1", output_dir="./output1")
        config2 = AppConfig(project_name="Project 2", log_level="DEBUG")
        merged = config1.merge(config2)
        assert merged.project_name == "Project 2"
        assert merged.output_dir == "./output1"
        assert merged.log_level == "DEBUG"

    def test_app_config_merge_empty(self):
        """Test AppConfig merging with empty config."""
        config1 = AppConfig(project_name="Project 1")
        config2 = AppConfig()
        merged = config1.merge(config2)
        assert merged.project_name == "Project 1"

    def test_app_config_merge_none(self):
        """Test AppConfig merging with None."""
        config1 = AppConfig(project_name="Project 1")
        merged = config1.merge(None)
        assert merged.project_name == "Project 1"
