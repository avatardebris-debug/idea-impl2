"""Backfill phase 2/4 artifacts from an existing combined JSON export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as: python scripts/backfill_visual_artifacts.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_movie_gen_suite.models import (
    BeatSheet,
    CharacterRegistry,
    SceneDescription,
    SceneDescriptionCollection,
    Script,
)
from ai_movie_gen_suite.pipeline.project_exporter import ProjectExporter


def load_project_json(path: Path) -> tuple[Script, CharacterRegistry, SceneDescriptionCollection, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    script = Script(**data["script"])
    chars_data = data.get("characters") or data.get("character_registry", {})
    registry = CharacterRegistry(**chars_data)
    desc_raw = data.get("scene_descriptions", {}).get("descriptions", {})
    collection = SceneDescriptionCollection()
    for scene_id, desc in desc_raw.items():
        collection.add_description(scene_id, SceneDescription(**desc))
    tone = data.get("tone", script.genre)
    return script, registry, collection, tone


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill storyboard and animatic artifacts")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("output/the_lying_city.json"),
        help="Combined pipeline JSON (default: output/the_lying_city.json)",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("."),
        help="Project root to write artifacts (default: workspace root)",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 1

    script, registry, descriptions, tone = load_project_json(args.input)
    exporter = ProjectExporter(
        project_dir=args.project_dir,
        script=script,
        character_registry=registry,
        scene_descriptions=descriptions,
        tone=tone,
    )
    meta = exporter.export_visual_and_animatic()
    n_sb = len(meta["storyboards"])
    n_seg = len(meta["phase4"]["timeline"].segments)
    print(f"Wrote storyboard_prompts ({n_sb} scenes), mood_boards, characters.json")
    print(f"Wrote animatic/ ({n_seg} segments, {meta['phase4']['timeline'].total_duration_ms} ms total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
