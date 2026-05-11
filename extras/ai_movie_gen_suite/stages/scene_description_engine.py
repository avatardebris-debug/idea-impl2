"""Scene Description Engine — generates visual descriptions for each scene."""

from __future__ import annotations

import json
from pathlib import Path

from ai_movie_gen_suite.config import AppConfig
from ai_movie_gen_suite.llm import call_llm_with_template
from ai_movie_gen_suite.models import Project, SceneDescription


SYSTEM_PROMPT = (
    "You are an expert cinematographer. Return ONLY valid JSON — "
    "no markdown, no explanation."
)


def generate_scenes(
    project: Project,
    config: AppConfig | None = None,
    tmp_path: Path | None = None,
    template_path: str | None = None,
) -> list[SceneDescription]:
    """Generate scene descriptions for each scene in the script."""
    if config is None:
        config = AppConfig()

    if template_path is None:
        template_path = "ai_movie_gen_suite/prompts/scene_prompt.jinja2"

    template_vars = {
        "logline": project.logline,
        "genre": project.genre,
        "tone": project.tone,
        "project_id": project.project_id,
    }

    result = call_llm_with_template(config, template_path, template_vars, SYSTEM_PROMPT)
    scene_descriptions = [SceneDescription(**sd) for sd in result]

    if tmp_path is not None:
        save_scenes(scene_descriptions, tmp_path)

    return scene_descriptions


def save_scenes(scene_descriptions: list[SceneDescription], output_dir: Path) -> None:
    """Save scene descriptions to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "scene_descriptions.json"
    path.write_text(json.dumps([sd.to_dict() for sd in scene_descriptions], indent=2))


def load_scenes(path: Path) -> list[SceneDescription]:
    """Load scene descriptions from JSON."""
    data = json.loads(path.read_text())
    return [SceneDescription(**sd) for sd in data]
