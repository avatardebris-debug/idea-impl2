"""Configuration system for the AI Movie Generation Suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = "openai"  # openai, anthropic, ollama
    model: str = "gpt-4o"
    api_key_env_var: str = "OPENAI_API_KEY"
    temperature: float = 0.7
    max_tokens: int = 4096
    base_url: Optional[str] = None


class ProjectConfig(BaseModel):
    """Configuration for a single movie project."""
    project_dir: str
    title: str
    logline: str
    genre: str
    tone: str = ""
    llm: LLMConfig = Field(default_factory=LLMConfig)

    def save(self, path: Optional[Path] = None) -> Path:
        """Save config to project_dir/config.json."""
        target = path or Path(self.project_dir) / "config.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.model_dump(), indent=2))
        return target

    @classmethod
    def load(cls, path: Path) -> ProjectConfig:
        """Load config from a project directory."""
        config_path = path / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        return cls(**json.loads(config_path.read_text()))


class SuiteConfig(BaseModel):
    """Global suite configuration."""
    default_llm: LLMConfig = Field(default_factory=LLMConfig)
    output_format: str = "json"  # json, yaml
    scenes_dir: str = "scenes"
    storyboard_dir: str = "storyboard_prompts"
    mood_board_dir: str = "mood_boards"
    animatic_dir: str = "animatic"
    characters_3d_dir: str = "characters_3d"
    ue5_export_dir: str = "ue5_export"

    def save(self, path: Optional[Path] = None) -> Path:
        target = path or Path.home() / ".ai_movie_gen" / "config.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.model_dump(), indent=2))
        return target

    @classmethod
    def load(cls, path: Optional[Path] = None) -> SuiteConfig:
        config_path = path or Path.home() / ".ai_movie_gen" / "config.json"
        if not config_path.exists():
            return cls()
        return cls(**json.loads(config_path.read_text()))
