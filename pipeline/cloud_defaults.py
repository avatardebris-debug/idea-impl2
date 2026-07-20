"""
Cloud-oriented parallel defaults for classic multi-agent (not Grok-Build).

When PIPELINE_CLOUD=1 and the operator did not pass aggressive CLI values,
apply sensible defaults:

  PIPELINE_CLOUD_PARALLEL_SEEDS  (default 2)
  PIPELINE_CLOUD_EXECUTORS       (default 2)

Explicit CLI always wins. Non-cloud stays at serial defaults (1/1).

Also documents project-level locking: the SQLite message bus serializes
*message* claim (BEGIN IMMEDIATE) but not *per-project* work. Use
pipeline.project_lock when two executors might hold different messages
for the same slug.
"""

from __future__ import annotations

import os
from typing import Any

from pipeline.env_flags import env_bool, env_int
from pipeline.output_bootstrap import is_cloud_environment


# Documented cloud defaults (overridable via env)
DEFAULT_CLOUD_PARALLEL_SEEDS = 2
DEFAULT_CLOUD_EXECUTORS = 2


def cloud_parallel_seeds_default() -> int:
    return max(1, env_int("PIPELINE_CLOUD_PARALLEL_SEEDS", default=DEFAULT_CLOUD_PARALLEL_SEEDS))


def cloud_executors_default() -> int:
    return max(1, env_int("PIPELINE_CLOUD_EXECUTORS", default=DEFAULT_CLOUD_EXECUTORS))


def resolve_parallelism(
    *,
    parallel_seeds: int | None,
    num_executors: int | None,
    seeds_explicit: bool = False,
    executors_explicit: bool = False,
) -> tuple[int, int]:
    """
    Resolve final (parallel_seeds, num_executors).

    * Explicit CLI always wins.
    * Under PIPELINE_CLOUD=1 with no CLI override → cloud env defaults (2/2).
    * Local / non-cloud with no CLI → 1/1.
    """
    cloud = is_cloud_environment()

    if seeds_explicit and parallel_seeds is not None:
        seeds = max(1, int(parallel_seeds))
    elif cloud and not seeds_explicit:
        seeds = cloud_parallel_seeds_default()
    else:
        seeds = max(1, int(parallel_seeds)) if parallel_seeds is not None else 1

    if executors_explicit and num_executors is not None:
        execs = max(1, int(num_executors))
    elif cloud and not executors_explicit:
        execs = cloud_executors_default()
    else:
        execs = max(1, int(num_executors)) if num_executors is not None else 1

    return seeds, execs


def cloud_bus_wake_default() -> bool:
    """PIPELINE_BUS_WAKE defaults on under PIPELINE_CLOUD=1 when unset."""
    raw = os.environ.get("PIPELINE_BUS_WAKE")
    if raw is not None and str(raw).strip() != "":
        return env_bool("PIPELINE_BUS_WAKE", default=False)
    return is_cloud_environment()


def describe_cloud_parallel_config(seeds: int, executors: int) -> dict[str, Any]:
    return {
        "pipeline_cloud": is_cloud_environment(),
        "parallel_seeds": seeds,
        "executors": executors,
        "env_seeds": os.environ.get("PIPELINE_CLOUD_PARALLEL_SEEDS", ""),
        "env_executors": os.environ.get("PIPELINE_CLOUD_EXECUTORS", ""),
        "bus_wake": cloud_bus_wake_default(),
    }
