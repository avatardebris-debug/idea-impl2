"""Check whether a pipeline project slug is fully complete."""

from __future__ import annotations

import json
import pathlib

from pipeline.dep_policy import is_full_complete
from pipeline.paths import project_state_file


def is_project_complete(slug: str, *, pipeline_dir: pathlib.Path | None = None) -> bool:
    """True only for full completion (all phases) or field_proven — not mvp_complete."""
    if pipeline_dir is not None:
        state_file = pipeline_dir / "projects" / slug / "state" / "current_idea.json"
    else:
        state_file = project_state_file(slug)
    if not state_file.exists():
        return False
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
        return is_full_complete(st)
    except Exception:
        return False
