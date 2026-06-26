"""Ship-prove provenance and maturity stage (M1–M4) on project state."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MATURITY_STAGES = ("M1", "M2", "M3", "M4")

MATURITY_MULTIPLIER: dict[str, float] = {
    "M1": 1.0,
    "M2": 1.25,
    "M3": 1.5,
    "M4": 2.0,
}


def default_provenance() -> dict[str, Any]:
    return {
        "maturity_stage": "M1",
        "field_test_loops": 0,
        "debug_loops": 0,
        "thermo_reviewed": False,
        "goal_proven": False,
        "goal_id": "",
        "system_id": "",
        "mission_tags": [],
        "value_tags": [],
        "updated_at": "",
    }


def provenance_path(project_dir: Path) -> Path:
    return project_dir / "state" / "ship_provenance.json"


def load_provenance(project_dir: Path) -> dict[str, Any]:
    path = provenance_path(project_dir)
    if not path.exists():
        return default_provenance()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        base = default_provenance()
        base.update(data)
        return base
    except Exception:
        return default_provenance()


def save_provenance(project_dir: Path, data: dict[str, Any]) -> None:
    data = {**default_provenance(), **data}
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    path = provenance_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def merge_idea_tags(project_dir: Path, tags: dict[str, Any]) -> None:
    """Persist master_ideas tags into ship_provenance."""
    prov = load_provenance(project_dir)
    if tags.get("goal_id"):
        prov["goal_id"] = tags["goal_id"]
    if tags.get("system_id"):
        prov["system_id"] = tags["system_id"]
    if tags.get("mission"):
        prov["mission_tags"] = tags["mission"]
    if tags.get("values"):
        prov["value_tags"] = tags["values"]
    save_provenance(project_dir, prov)


def set_maturity(project_dir: Path, stage: str) -> None:
    if stage not in MATURITY_STAGES:
        return
    prov = load_provenance(project_dir)
    prov["maturity_stage"] = stage
    save_provenance(project_dir, prov)


def maturity_multiplier(project_dir: Path) -> float:
    prov = load_provenance(project_dir)
    return MATURITY_MULTIPLIER.get(prov.get("maturity_stage", "M1"), 1.0)
