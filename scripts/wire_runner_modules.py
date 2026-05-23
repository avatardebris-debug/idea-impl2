"""Remove extracted bodies from runner.py and insert import block."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
RUNNER = ROOT / "pipeline/runner.py"
lines = RUNNER.read_text(encoding="utf-8").splitlines()

DROP = [(1080, 2157), (604, 1063), (357, 364), (1566, 1569)]

def drop_ranges(src: list[str], ranges: list[tuple[int, int]]) -> list[str]:
    out = src[:]
    for start, end in sorted(ranges, key=lambda x: -x[0]):
        out = out[: start - 1] + out[end:]
    return out

kept = drop_ranges(lines, DROP)

IMPORT_BLOCK = """# Ensure project root is on path (pipeline_config)
from pipeline.pipeline_config import (
    AGENT_ROLES,
    AGENTS_DIR,
    DEFAULT_BASE_BUDGET,
    DEFAULT_PHASE_BUDGET,
    MAX_PHASE_RETRIES,
    MAX_PROJECT_LIFETIME_RETRIES,
    PIPELINE_DIR,
    PROJECT_ROOT,
)
from pipeline.slug_util import slugify_title as _slugify
from pipeline.seeding import (
    SEED_BLOCKED,
    SEED_EMPTY,
    SEED_GOAL_QUEUED,
    SEED_SEEDED,
    _SEED_BLOCKED,
    _SEED_EMPTY,
    _SEED_GOAL_QUEUED,
    _SEED_SEEDED,
    _purge_dep_blocked_messages,
    _request_ideation,
    _seeded_this_session,
    check_resume,
    seed_from_master_list,
    seed_idea,
)
from pipeline.project_ops import (
    _advance_phase,
    _append_polish,
    _check_priority_eviction,
    _extract_shared_libs,
    _increment_retries,
    _mark_complete,
    _rebuild_queues_from_state,
    _rebuild_single_project,
    _reset_retries,
    _tick_project,
    _write_state,
    _write_state_dict,
)
from pipeline.startup import resolve_initial_work

_RUNNER_IDEAS_PATH: pathlib.Path | None = None
_run_ctx: \"RunContext | None\" = None
"""

# Replace lines 73-113 (0-index 72:113)
out = kept[:72] + IMPORT_BLOCK.splitlines() + kept[113:]
RUNNER.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"runner.py: {len(lines)} -> {len(out)} lines")
