"""Character Generator — creates character profiles from beat sheet."""

from __future__ import annotations

import json
from pathlib import Path

from ai_movie_gen_suite.config import AppConfig
from ai_movie_gen_suite.llm import call_llm_with_template
from ai_movie_gen_suite.models import CharacterRegistry, Project


SYSTEM_PROMPT = (
    "You are an expert character developer. Return ONLY valid JSON — "
    "no markdown, no explanation."
)


def generate_characters(
    project: Project,
    config: AppConfig | None = None,
    tmp_path: Path | None = None,
    template_path: str | None = None,
) -> CharacterRegistry:
    """Generate character profiles from the project's beat sheet."""
    if config is None:
        config = AppConfig()

    if template_path is None:
        template_path = "ai_movie_gen_suite/prompts/character_prompt.jinja2"

    template_vars = {
        "logline": project.logline,
        "genre": project.genre,
        "tone": project.tone,
        "project_id": project.project_id,
    }

    result = call_llm_with_template(config, template_path, template_vars, SYSTEM_PROMPT)
    character_registry = CharacterRegistry(**result)

    if tmp_path is not None:
        save_characters(character_registry, tmp_path)

    return character_registry


def save_characters(character_registry: CharacterRegistry, output_dir: Path) -> None:
    """Save character registry to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "characters.json"
    path.write_text(character_registry.to_json(indent=2))


def load_characters(path: Path) -> CharacterRegistry:
    """Load character registry from JSON."""
    data = json.loads(path.read_text())
    return CharacterRegistry(**data)
