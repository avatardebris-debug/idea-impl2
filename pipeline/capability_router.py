"""
pipeline/capability_router.py
Rank registry capabilities for a task description (Phase 3).

Disabled when PIPELINE_LEGACY=1.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pipeline.capability_graph import is_routable, missing_requires
from pipeline.capability_registry import _connect
from pipeline.paths import registry_db
from pipeline.pipeline_mode import legacy_mode

# Keyword → domain boost
_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "robotics": ("robot", "mujoco", "urdf", "primitive", "sim-to-real", "manipulation"),
    "video": ("video", "movie", "animatic", "storyboard", "screenplay", "scene"),
    "finance": ("financial", "portfolio", "betting", "market", "trading", "ohlcv"),
    "dropship": ("drop", "shopify", "ecommerce", "seo", "product"),
    "learning": ("learning", "course", "udemy", "language", "lesson"),
    "devops": ("pipeline", "health", "import", "extract", "registry"),
}


def _project_satisfied(slug: str) -> bool:
    """True if slug exists and is complete at max phase."""
    from pipeline.project_complete import is_project_complete

    return is_project_complete(slug)


def _requires_satisfied(requires_json: str) -> tuple[bool, list[str]]:
    try:
        reqs = json.loads(requires_json or "[]")
    except json.JSONDecodeError:
        reqs = []
    if not reqs:
        return True, []
    missing = [r for r in reqs if not _project_satisfied(r)]
    return len(missing) == 0, missing


def _score_row(task_text: str, row: Any) -> float:
    text = task_text.lower()
    score = 0.0
    slug = row["slug"] or ""
    title = (row["title"] or "").lower()
    purpose = (row["purpose"] or "").lower()

    for word in re.findall(r"[a-z0-9_]{3,}", text):
        if word in slug.replace("_", " "):
            score += 2.0
        if word in title:
            score += 1.5
        if word in purpose:
            score += 1.0

    try:
        domains = json.loads(row["domains"] or "[]")
    except json.JSONDecodeError:
        domains = []
    for domain, keys in _DOMAIN_KEYWORDS.items():
        if domain in domains or any(k in text for k in keys):
            if any(k in slug + title + purpose for k in keys):
                score += 1.5
            elif any(k in text for k in keys):
                score += 0.5

    if row["entrypoint"]:
        score += 0.3
    if row["kind"] == "shared_lib":
        score += 0.2
    return score


def route_task(
    task_text: str,
    *,
    domain: str | None = None,
    limit: int = 5,
    min_score: float = 1.0,
    include_blocked: bool = False,
) -> list[dict[str, Any]]:
    """
    Return ranked capability suggestions for a natural-language task.

    Each item: slug, title, score, reason, entrypoint, requires_ok, missing_requires
    """
    if legacy_mode() or not registry_db().exists():
        return []

    conn = _connect()
    q = """
        SELECT slug, title, kind, status, purpose, domains, entrypoint, example_invoke, requires
        FROM capabilities
        WHERE status = 'verified'
          AND (entrypoint != '' OR kind IN ('shared_lib', 'hermes_task', 'workflow', 'connector'))
    """
    params: list[Any] = []
    if domain:
        q += " AND domains LIKE ?"
        params.append(f"%{domain}%")
    rows = conn.execute(q, params).fetchall()
    conn.close()

    fts_hits: dict[str, float] = {}
    try:
        from pipeline.capability_search import search_capabilities

        for hit in search_capabilities(task_text, limit=limit * 2):
            slug = hit["slug"]
            # bm25 lower is better in SQLite → invert to boost
            fts_hits[slug] = max(fts_hits.get(slug, 0.0), 3.0 + min(2.0, abs(hit.get("fts_rank", 0)) * 0.1))
    except Exception:
        pass

    bandit_boost: dict[str, float] = {}
    try:
        from pipeline.capability_metrics import read_metrics

        ok_count: dict[str, int] = {}
        fail_count: dict[str, int] = {}
        for ev in read_metrics(limit=3000):
            if ev.get("event") != "invoke":
                continue
            s = ev.get("slug") or ""
            if not s:
                continue
            if ev.get("ok"):
                ok_count[s] = ok_count.get(s, 0) + 1
            else:
                fail_count[s] = fail_count.get(s, 0) + 1
        for s, ok in ok_count.items():
            fail = fail_count.get(s, 0)
            if ok + fail >= 2:
                rate = ok / (ok + fail)
                if rate >= 0.8:
                    bandit_boost[s] = 0.8
                elif rate < 0.4:
                    bandit_boost[s] = -0.5
    except Exception:
        pass

    ranked: list[dict[str, Any]] = []
    for row in rows:
        score = _score_row(task_text, row)
        score += fts_hits.get(row["slug"], 0.0)
        score += bandit_boost.get(row["slug"], 0.0)
        if score < min_score:
            continue
        ok, missing = _requires_satisfied(row["requires"])
        if not ok and not include_blocked:
            continue
        if not ok:
            score *= 0.25
        if not is_routable(row["slug"]):
            if not include_blocked:
                continue
            missing = list(set(missing + missing_requires(row["slug"])))
            ok = False
        ranked.append({
            "slug": row["slug"],
            "title": row["title"],
            "kind": row["kind"],
            "score": round(score, 2),
            "entrypoint": row["entrypoint"],
            "example_invoke": row["example_invoke"],
            "requires_ok": ok,
            "missing_requires": missing,
            "reason": (
                f"match (score={score:.1f}"
                + (" +fts" if row["slug"] in fts_hits else "")
                + (" +bandit" if row["slug"] in bandit_boost else "")
                + ")"
            ),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    out = ranked[:limit]
    try:
        from pipeline.capability_metrics import log_capability_event

        for item in out[:3]:
            log_capability_event(
                "route",
                item["slug"],
                ok=item.get("requires_ok"),
                detail=item.get("reason", "")[:120],
            )
    except Exception:
        pass
    return out


def format_suggestions(suggestions: list[dict[str, Any]]) -> str:
    if not suggestions:
        return ""
    lines = ["Suggested capabilities to reuse (invoke_capability or read source):"]
    for s in suggestions:
        flag = "" if s["requires_ok"] else f" [blocked: needs {s['missing_requires']}]"
        lines.append(
            f"  - `{s['slug']}` ({s['score']}){flag}: {s['title']}"
            + (f" — `{s['entrypoint']}`" if s.get("entrypoint") else "")
        )
    return "\n".join(lines)
