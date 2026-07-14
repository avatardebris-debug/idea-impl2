"""Seed-time capability reuse evaluation (soft suggestions + optional hard skip)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pipeline.env_flags import env_bool, env_float
from pipeline.paths import project_dir


@dataclass
class SeedReuseDecision:
    suggestions: list[dict[str, Any]] = field(default_factory=list)
    skip_seed: bool = False
    slug: str | None = None
    score: float = 0.0
    summary: str = ""


def evaluate_seed_reuse(title: str, description: str) -> SeedReuseDecision:
    """Soft: always return suggestions when registry matches.

    Hard skip only when PIPELINE_INVOKE_BEFORE_SEED=1 and score meets threshold.
    Hard skip does **not** check off master_ideas — caller records a note only.
    """
    out = SeedReuseDecision()
    try:
        from pipeline.capability_router import format_suggestions, route_task

        suggestions = route_task(
            f"{title} {description}",
            limit=5,
            min_score=1.0,
        )
    except Exception:
        return out
    if not suggestions:
        return out

    out.suggestions = suggestions
    best = suggestions[0]
    score = float(best.get("score") or 0)
    out.slug = best.get("slug")
    out.score = score
    try:
        out.summary = format_suggestions(suggestions[:5])
    except Exception:
        out.summary = ""

    min_score = env_float("CAPABILITY_REUSE_MIN_SCORE", default=4.0)
    if (
        env_bool("PIPELINE_INVOKE_BEFORE_SEED", default=False)
        and score >= min_score
        and best.get("requires_ok", True)
    ):
        out.skip_seed = True
    return out


def write_suggested_reuse(idea_slug: str, decision: SeedReuseDecision) -> None:
    if not decision.suggestions:
        return
    try:
        path = project_dir(idea_slug) / "state" / "suggested_reuse.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "suggestions": decision.suggestions[:5],
            "summary": decision.summary,
            "written_at": datetime.now(timezone.utc).isoformat(),
        }
        import json

        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def format_reuse_context(idea_slug: str) -> str:
    """Prompt fragment from state/suggested_reuse.json, or empty."""
    try:
        import json

        path = project_dir(idea_slug) / "state" / "suggested_reuse.json"
        if not path.exists():
            return ""
        data = json.loads(path.read_text(encoding="utf-8"))
        summary = (data.get("summary") or "").strip()
        if summary:
            return f"## Suggested capability reuse\n{summary}"
    except Exception:
        pass
    return ""
