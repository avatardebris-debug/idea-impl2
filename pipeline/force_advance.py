"""Single implementation for manager force-advance past a stuck phase."""

from __future__ import annotations

import json
import logging
from typing import Any

from pipeline.env_flags import env_bool
from pipeline.paths import project_dir

logger = logging.getLogger(__name__)


def force_advance_phase(
    idea_slug: str,
    phase: int,
    reason: str,
    *,
    tasks_path: str | None = None,
    workspace_path: str | None = None,
    review_path: str | None = None,
    retry_count: int = 3,
) -> bool:
    """Mark phase_N_reviewed with force_advanced so runner advances.

    Sets quality_risk when PIPELINE_FORCE_ADVANCE_QUALITY_RISK is on (default).
    Records bug_memory observation + activity event.
    Returns True on success.
    """
    if not idea_slug:
        return False
    phase = int(phase or 0)
    proj = project_dir(idea_slug)
    state_file = proj / "state" / "current_idea.json"
    retry_file = proj / "state" / "phase_retries.json"
    if not state_file.exists():
        return False

    try:
        state: dict[str, Any] = json.loads(state_file.read_text(encoding="utf-8"))
        state["status"] = f"phase_{phase}_reviewed"
        if env_bool("PIPELINE_FORCE_ADVANCE_QUALITY_RISK", default=True):
            state["quality_risk"] = True
            state["force_advanced"] = True
        state["review_result"] = {
            "blocking_bugs": 0,
            "force_advanced": True,
            "non_blocking_notes": reason[:800],
            "tasks_path": tasks_path or f"phases/phase_{phase}/tasks.md",
            "workspace_path": workspace_path or str(proj / "workspace"),
            "review_path": review_path or f"phases/phase_{phase}/review.md",
        }
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        if retry_file.exists():
            try:
                retries = json.loads(retry_file.read_text(encoding="utf-8"))
                for key in list(retries.keys()):
                    if f"phase_{phase}" in key:
                        retries.pop(key)
                retry_file.write_text(json.dumps(retries, indent=2), encoding="utf-8")
            except Exception:
                pass

        try:
            from pipeline.bug_memory import record_failure_observation

            record_failure_observation(
                idea_slug,
                phase,
                reason[:500],
                retry_count=max(int(retry_count or 0), 3),
            )
        except Exception:
            pass

        from pipeline.pipeline_activity import log_activity

        log_activity(
            "force_advance",
            slug=idea_slug,
            phase=phase,
            reason=reason[:200],
        )
        logger.info(
            "[force_advance] '%s' past phase %d: %s",
            idea_slug,
            phase,
            reason[:120],
        )
        return True
    except Exception as exc:
        logger.error("[force_advance] failed for '%s': %s", idea_slug, exc)
        return False
