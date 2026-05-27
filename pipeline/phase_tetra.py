"""
pipeline/phase_tetra.py
Optional phase template: validate Throng6 tetra_meta_learn toolcall (Phase 6).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

from pipeline.tools.tetra_meta_learn import default_request, run_tetra_meta_learn


def run_phase_tetra_validation(
    project_dir: pathlib.Path,
    *,
    env_type: str = "mario_ascii",
    budget_steps: int = 300,
    outer_cycles: int = 2,
) -> dict[str, Any]:
    """Run tetra toolcall smoke test; return response with grounding_score."""
    slug = project_dir.name
    request = default_request(
        env_type=env_type,
        budget_steps=budget_steps,
        outer_cycles=outer_cycles,
        pipeline_project=slug,
    )
    response = run_tetra_meta_learn(request)
    out_path = project_dir / "state" / "tetra_validation.json"
    out_path.write_text(json.dumps(response, indent=2), encoding="utf-8")
    return response


def maybe_run_phase_tetra_hook(project_dir: pathlib.Path, state: dict) -> bool:
    """
    If project uses phase_template=phase_tetra and is on final phase executing,
    run validation and update capability registry grounding.
    """
    if state.get("phase_template") != "phase_tetra":
        return False
    phase = int(state.get("phase", 0))
    total = int(state.get("total_phases", 0))
    if phase < total:
        return False

    env_type = state.get("tetra_env", "mario_ascii")
    response = run_phase_tetra_validation(project_dir, env_type=env_type)
    gscore = float(response.get("grounding_score", 0.0))

    try:
        from pipeline.capability_registry import (
            promote_if_grounded,
            register_tetra_meta_learn_capability,
        )

        register_tetra_meta_learn_capability(grounding_score=gscore)
        promote_if_grounded("tetra_meta_learn", gscore)
    except Exception:
        pass

    state["tetra_grounding_score"] = gscore
    state["tetra_validation"] = response.get("success", False)
    return True
