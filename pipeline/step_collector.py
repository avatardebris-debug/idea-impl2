"""Collect finetune step pairs after each agent handle() call."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.paths import finetune_corpus_dir
from pipeline.ship_provenance import load_provenance, maturity_multiplier

DEFAULT_AGENTS = (
    "idea_planner",
    "phase_planner",
    "executor",
    "validator",
    "reviewer",
    "field_test_planner",
    "debug_loop",
    "thermo_reviewer",
    "ship_evaluator",
)


def collect_enabled() -> bool:
    return os.environ.get("PIPELINE_COLLECT_EVERY_STEP", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def allowed_agents() -> frozenset[str]:
    raw = os.environ.get("PIPELINE_COLLECT_AGENTS", "").strip()
    if not raw:
        return frozenset(DEFAULT_AGENTS)
    return frozenset(a.strip() for a in raw.split(",") if a.strip())


def steps_path(slug: str) -> Path:
    return finetune_corpus_dir() / "raw" / "steps" / f"{slug}.jsonl"


def collect_agent_step(
    *,
    slug: str,
    agent_role: str,
    msg_type: str,
    payload: dict[str, Any],
    answer: str,
    tokens_used: int,
    steps_used: int,
    success: bool,
    project_dir: Path | None = None,
) -> None:
    if not collect_enabled():
        return
    if agent_role not in allowed_agents():
        return
    if not slug or slug == "unknown":
        return

    maturity = "M1"
    weight_bonus = 1.0
    if project_dir is not None:
        prov = load_provenance(project_dir)
        maturity = prov.get("maturity_stage", "M1")
        weight_bonus = maturity_multiplier(project_dir)

    phase = payload.get("phase", payload.get("ship_phase", ""))
    record: dict[str, Any] = {
        "id": f"{slug}__{agent_role}__{datetime.now(timezone.utc).timestamp():.0f}",
        "source_slug": slug,
        "agent": agent_role,
        "msg_type": msg_type,
        "phase": phase,
        "payload_summary": {
            k: (str(v)[:500] if v is not None else "")
            for k, v in payload.items()
            if k in (
                "phase",
                "idea_slug",
                "fix_required",
                "ship_fix",
                "tasks_path",
            )
        },
        "output": (answer or "")[:8000],
        "tokens": tokens_used,
        "steps": steps_used,
        "success": success,
        "maturity_stage": maturity,
        "maturity_weight_bonus": weight_bonus,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }

    out = steps_path(slug)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
