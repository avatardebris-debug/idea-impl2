"""
One systematic-debugging pass before classic force-advance.

Env:
  PRE_FORCE_SYSTEMATIC_DEBUG=1   (default on)
  Only runs once per phase (state flag systematic_debug_attempted_phase_N).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool
from pipeline.paths import project_dir
from pipeline.skill_load import load_skill_body, skill_available

logger = logging.getLogger(__name__)


def pre_force_debug_enabled() -> bool:
    return env_bool("PRE_FORCE_SYSTEMATIC_DEBUG", default=True)


def already_attempted(proj: Path, phase: int) -> bool:
    state_file = proj / "state" / "current_idea.json"
    if not state_file.is_file():
        return False
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(st.get(f"systematic_debug_attempted_phase_{phase}"))


def mark_attempted(proj: Path, phase: int) -> None:
    state_file = proj / "state" / "current_idea.json"
    if not state_file.is_file():
        return
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
        st[f"systematic_debug_attempted_phase_{phase}"] = True
        state_file.write_text(json.dumps(st, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.debug("mark systematic_debug attempted failed: %s", exc)


def build_systematic_debug_instructions(
    *,
    idea_slug: str,
    phase: int,
    fix_report: str = "",
    validation_excerpt: str = "",
) -> str:
    skill = load_skill_body("systematic-debugging", max_chars=10000)
    header = (
        "# SYSTEMATIC DEBUG (required before force-advance)\n\n"
        "You must follow the systematic-debugging process below. "
        "NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.\n\n"
    )
    if not skill:
        skill = (
            "## Fallback process (skill file not found on disk)\n"
            "1. Read errors fully\n2. Reproduce\n3. One hypothesis\n"
            "4. Minimal fix + verify with tests\n5. Write phases/phase_N/systematic_debug_report.md\n"
        )
    body = (
        f"{header}"
        f"## Skill: systematic-debugging\n\n{skill}\n\n"
        f"## Project context\n"
        f"- Slug: {idea_slug}\n"
        f"- Phase: {phase}\n\n"
        f"## Validation / failure excerpt\n```\n{validation_excerpt[:4000]}\n```\n\n"
        f"## Fix report history\n{fix_report[:6000]}\n\n"
        f"## Deliverables\n"
        f"1. Write `phases/phase_{phase}/systematic_debug_report.md` with:\n"
        f"   root cause, evidence, hypothesis, fix applied, residual risk\n"
        f"2. Apply the **single** minimal root-cause fix under workspace/\n"
        f"3. Do not force-advance; leave work for re-validation\n"
        f"Say DONE when report is written and fix applied (or blocked with evidence).\n"
    )
    return body


def try_enqueue_pre_force_debug(
    *,
    idea_slug: str,
    phase: int,
    tasks_path: str = "",
    workspace_path: str = "",
    fix_report_path: str = "",
    fix_report_content: str = "",
    validation_excerpt: str = "",
    retry_count: int = 0,
) -> dict[str, Any] | None:
    """
    If enabled and not yet attempted this phase, return executor task payload
    for one systematic-debug pass. Caller should enqueue to executor and NOT
    force-advance yet.

    Returns None if force-advance should proceed (disabled / already tried).
    """
    if not pre_force_debug_enabled():
        return None
    if not idea_slug:
        return None
    proj = project_dir(idea_slug)
    phase = int(phase or 0)
    if already_attempted(proj, phase):
        logger.info(
            "[pre_force_debug] already attempted phase %s for %s — allow force-advance",
            phase,
            idea_slug,
        )
        return None

    # Prefer loading skill; still run with fallback process if missing
    if not skill_available("systematic-debugging"):
        logger.warning(
            "[pre_force_debug] systematic-debugging skill not found on disk; "
            "using embedded fallback process"
        )

    if not fix_report_content and fix_report_path:
        fr = proj / fix_report_path
        if fr.is_file():
            try:
                fix_report_content = fr.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass

    instructions = build_systematic_debug_instructions(
        idea_slug=idea_slug,
        phase=phase,
        fix_report=fix_report_content,
        validation_excerpt=validation_excerpt,
    )
    mark_attempted(proj, phase)

    try:
        from pipeline.pipeline_activity import log_activity

        log_activity(
            "pre_force_systematic_debug",
            slug=idea_slug,
            phase=phase,
            skill_found=skill_available("systematic-debugging"),
        )
    except Exception:
        pass

    return {
        "phase": phase,
        "tasks_path": tasks_path or f"phases/phase_{phase}/tasks.md",
        "workspace_path": workspace_path or str(proj / "workspace"),
        "fix_required": True,
        "fix_report_path": fix_report_path or f"phases/phase_{phase}/fix_report.md",
        "fix_instructions": instructions,
        "idea_slug": idea_slug,
        "retry_count": retry_count,
        "systematic_debug": True,
    }
