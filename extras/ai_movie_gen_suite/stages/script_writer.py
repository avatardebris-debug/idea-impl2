"""Script Writer — generates screenplay script from beats and characters."""

from __future__ import annotations

import json
from pathlib import Path

from ai_movie_gen_suite.config import AppConfig
from ai_movie_gen_suite.llm import call_llm_with_template
from ai_movie_gen_suite.models import Project, Script


SYSTEM_PROMPT = (
    "You are an expert screenwriter. Return ONLY valid JSON — "
    "no markdown, no explanation."
)


def generate_script(
    project: Project,
    config: AppConfig | None = None,
    tmp_path: Path | None = None,
    template_path: str | None = None,
) -> Script:
    """Generate a screenplay script from the project's beat sheet and characters."""
    if config is None:
        config = AppConfig()

    if template_path is None:
        template_path = "ai_movie_gen_suite/prompts/script_prompt.jinja2"

    template_vars = {
        "logline": project.logline,
        "genre": project.genre,
        "tone": project.tone,
        "project_id": project.project_id,
    }

    result = call_llm_with_template(config, template_path, template_vars, SYSTEM_PROMPT)
    script = Script(**result)

    if tmp_path is not None:
        save_script(script, tmp_path)

    return script


def save_script(script: Script, output_dir: Path) -> None:
    """Save script to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "script.json"
    path.write_text(script.to_json(indent=2))


def load_script(path: Path) -> Script:
    """Load script from JSON."""
    data = json.loads(path.read_text())
    return Script(**data)
