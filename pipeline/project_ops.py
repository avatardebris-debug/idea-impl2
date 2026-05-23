"""
pipeline/project_ops.py
Thin re-export facade for project state machine helpers.
"""

from pipeline.project_phase import (
    _advance_phase,
    _extract_shared_libs,
    _mark_complete,
)
from pipeline.project_rebuild import (
    _rebuild_queues_from_state,
    _rebuild_single_project,
)
from pipeline.project_state import (
    _append_polish,
    _check_priority_eviction,
    _increment_retries,
    _reset_retries,
    _write_state,
    _write_state_dict,
)
from pipeline.project_tick import _tick_project

__all__ = [
    "_advance_phase",
    "_append_polish",
    "_check_priority_eviction",
    "_extract_shared_libs",
    "_increment_retries",
    "_mark_complete",
    "_rebuild_queues_from_state",
    "_rebuild_single_project",
    "_reset_retries",
    "_tick_project",
    "_write_state",
    "_write_state_dict",
]
