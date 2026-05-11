"""Beat Sheet Generator — creates beat sheets from project logline."""

from __future__ import annotations

import json
from pathlib import Path

from ai_movie_gen_suite.config import AppConfig
from ai_movie_gen_suite.llm import call_llm_with_template
from ai_movie_gen_suite.models import BeatSheet, Project


SYSTEM_PROMPT = (
    "You are an expert screenwriter. Return ONLY valid JSON — "
    "no markdown, no explanation."
)


def generate_beats(
    project: Project,
    config: AppConfig | None = None,
    tmp_path: Path | None = None,
    template_path: str | None = None,
) -> BeatSheet:
    """Generate a beat sheet from the project's logline and genre."""
    if config is None:
        config = AppConfig()

    if template_path is None:
        template_path = "ai_movie_gen_suite/prompts/beat_prompt.jinja2"

    template_vars = {
        "logline": project.logline,
        "genre": project.genre,
        "tone": project.tone,
        "project_id": project.project_id,
    }

    result = call_llm_with_template(config, template_path, template_vars, SYSTEM_PROMPT)
    beat_sheet = BeatSheet(**result)

    if tmp_path is not None:
        save_beats(beat_sheet, tmp_path)

    return beat_sheet


def save_beats(beat_sheet: BeatSheet, output_dir: Path) -> None:
    """Save beat sheet to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "beat_sheet.json"
    path.write_text(beat_sheet.to_json(indent=2))


def load_beats(path: Path) -> BeatSheet:
    """Load beat sheet from JSON."""
    data = json.loads(path.read_text())
    return BeatSheet(**data)
