"""Check whether a pipeline project slug is fully complete."""

from __future__ import annotations

import json
import pathlib

from pipeline.pipeline_config import get_pipeline_dir


def is_project_complete(slug: str, *, pipeline_dir: pathlib.Path | None = None) -> bool:
    root = pipeline_dir or get_pipeline_dir()
    state_file = root / "projects" / slug / "state" / "current_idea.json"
    if not state_file.exists():
        return False
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
        return (
            st.get("status") == "complete"
            and int(st.get("phase", 0)) >= int(st.get("total_phases", 1))
        )
    except Exception:
        return False
