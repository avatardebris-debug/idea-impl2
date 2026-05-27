"""
pipeline/tools/tetra_meta_learn.py
Callable wrapper for Throng6 tetra_meta_learn toolcall (Phase 6).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

IDEA_IMPL_ROOT = Path(__file__).resolve().parents[2]
AICOMPETE_ROOT = IDEA_IMPL_ROOT.parent
THRONG6_ROOT = AICOMPETE_ROOT / "throng6"


def _run_via_import(request: dict[str, Any]) -> dict[str, Any]:
    if str(THRONG6_ROOT) not in sys.path:
        sys.path.insert(0, str(THRONG6_ROOT))
    from throng6.tetra.toolcall import run_toolcall

    return run_toolcall(request)


def _run_via_subprocess(request: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "throng6", "toolcall"],
        input=json.dumps(request),
        cwd=str(THRONG6_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "toolcall failed")
    return json.loads(proc.stdout)


def run_tetra_meta_learn(
    request: dict[str, Any],
    *,
    prefer_subprocess: bool = False,
) -> dict[str, Any]:
    """
    Execute tetra_meta_learn toolcall.

    Returns TetraSessionResponse-shaped dict including grounding_score.
    """
    if prefer_subprocess or os.environ.get("TETRA_TOOLCALL_SUBPROCESS") == "1":
        return _run_via_subprocess(request)
    try:
        return _run_via_import(request)
    except ImportError:
        return _run_via_subprocess(request)


def default_request(
    *,
    env_type: str = "mario_ascii",
    game_id: str | None = None,
    budget_steps: int = 400,
    outer_cycles: int = 2,
    pipeline_project: str = "",
) -> dict[str, Any]:
    env: dict[str, Any] = {"type": env_type}
    if game_id:
        env["game_id"] = game_id
    req: dict[str, Any] = {
        "tool": "tetra_meta_learn",
        "env": env,
        "budget_steps": budget_steps,
        "outer_cycles": outer_cycles,
    }
    if pipeline_project:
        req["context"] = {"pipeline_project": pipeline_project, "reason": "pipeline validation"}
    return req


if __name__ == "__main__":
    payload = default_request()
    if len(sys.argv) > 1:
        payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(run_tetra_meta_learn(payload), indent=2))
