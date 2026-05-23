"""Extract project_ops, seeding, startup helpers from runner.py."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
RUNNER = ROOT / "pipeline/runner.py"
lines = RUNNER.read_text(encoding="utf-8").splitlines()


def slice_lines(start_1based: int, end_1based: int) -> str:
    return "\n".join(lines[start_1based - 1 : end_1based]) + "\n"


CONFIG_BODY = slice_lines(74, 113) + slice_lines(1566, 1569)

PROJECT_OPS_HEADER = '''"""
pipeline/project_ops.py
Project state machine: rebuild queues, tick phases, advance, complete.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pipeline.message_bus import Message, MessageBus
from pipeline.pipeline_config import (
    AGENT_ROLES,
    MAX_PHASE_RETRIES,
    MAX_PROJECT_LIFETIME_RETRIES,
    PIPELINE_DIR,
    PROJECT_ROOT,
)
from pipeline.slug_util import slugify_title as _slugify

if TYPE_CHECKING:
    pass

'''

SEEDING_HEADER = '''"""
pipeline/seeding.py
Seed ideas from master list, ideation, dep-aware queue purge.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pipeline.message_bus import Message, MessageBus
from pipeline.pipeline_config import AGENT_ROLES, PIPELINE_DIR, PROJECT_ROOT
from pipeline.slug_util import slugify_title as _slugify

if TYPE_CHECKING:
    pass

# Return values for seed_from_master_list
SEED_SEEDED = "seeded"
SEED_BLOCKED = "blocked"
SEED_EMPTY = "empty"
SEED_GOAL_QUEUED = "goal_queued"

# Back-compat aliases for runner imports
_SEED_SEEDED = SEED_SEEDED
_SEED_BLOCKED = SEED_BLOCKED
_SEED_EMPTY = SEED_EMPTY
_SEED_GOAL_QUEUED = SEED_GOAL_QUEUED

_seeded_this_session: set[str] = set()

'''

# project_ops: rename public functions for clarity but keep _ names for runner re-export
po_body = slice_lines(1080, 2157)
# seeding body includes purge + seeds
seed_body = slice_lines(604, 676) + "\n" + slice_lines(682, 1062)

(ROOT / "pipeline/pipeline_config.py").write_text(
    '"""Shared pipeline paths and constants."""\nfrom __future__ import annotations\nimport pathlib\nimport sys\n\n'
    + CONFIG_BODY.replace("PROJECT_ROOT = pathlib.Path(__file__).parent.parent\nsys.path.insert(0, str(PROJECT_ROOT))\n", "PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()\n")
    + "\nMAX_PHASE_RETRIES = 5\nMAX_PROJECT_LIFETIME_RETRIES = 80\n",
    encoding="utf-8",
)

(ROOT / "pipeline/slug_util.py").write_text(
    slice_lines(357, 364).replace("def _slugify", "def slugify_title"),
    encoding="utf-8",
)

(ROOT / "pipeline/project_ops.py").write_text(PROJECT_OPS_HEADER + po_body, encoding="utf-8")
(ROOT / "pipeline/seeding.py").write_text(SEEDING_HEADER + seed_body, encoding="utf-8")

print("Wrote pipeline_config, slug_util, project_ops, seeding")
