"""Corpus record lineage: generation, canonical flag, and supersession."""

from __future__ import annotations

from typing import Any

LINEAGE_FIELDS = ("corpus_generation", "is_canonical", "supersedes")


def sequence_id_of(rec: dict[str, Any]) -> str:
    """Stable sequence id for a logical training unit (phase/task/project chain)."""
    sid = rec.get("sequence_id")
    if sid:
        return str(sid)
    return str(rec.get("id", ""))


def lineage_group_key(rec: dict[str, Any]) -> str:
    """Unique key for one collectable unit within a granularity file."""
    gran = str(rec.get("granularity", "task"))
    slug = str(rec.get("project_slug") or rec.get("source_slug") or "")
    return f"{gran}:{slug}:{sequence_id_of(rec)}"


def ensure_lineage_defaults(rec: dict[str, Any]) -> dict[str, Any]:
    """Fill missing lineage fields for legacy rows (does not change generation)."""
    if "corpus_generation" not in rec:
        rec["corpus_generation"] = 1
    if "is_canonical" not in rec:
        rec["is_canonical"] = True
    if "supersedes" not in rec:
        rec["supersedes"] = None
    if not rec.get("sequence_id") and rec.get("id"):
        rec["sequence_id"] = rec["id"]
    return rec


def stamp_new_generation(
    rec: dict[str, Any],
    *,
    generation: int,
    supersedes: str | None = None,
    is_canonical: bool = True,
) -> dict[str, Any]:
    """Attach lineage to a freshly collected record."""
    ensure_lineage_defaults(rec)
    rec["corpus_generation"] = generation
    rec["is_canonical"] = is_canonical
    rec["supersedes"] = supersedes
    return rec


def max_generation_for_keys(
    records: list[dict[str, Any]],
    keys: set[str],
) -> dict[str, int]:
    """Return max corpus_generation per lineage_group_key for the given keys."""
    out: dict[str, int] = {}
    for rec in records:
        key = lineage_group_key(rec)
        if key not in keys:
            continue
        gen = int(rec.get("corpus_generation", 1))
        out[key] = max(out.get(key, 0), gen)
    return out


def pick_preferred_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Choose the training-export winner among rows sharing the same id."""

    def _score(r: dict[str, Any]) -> tuple[int, int, int]:
        canonical = 1 if r.get("is_canonical", True) else 0
        gen = int(r.get("corpus_generation", 1))
        tier = r.get("train_tier", "D")
        tier_rank = {"A": 4, "B": 3, "C": 2, "D": 1}.get(str(tier), 0)
        return (canonical, gen, tier_rank)

    return max(records, key=_score)


def dedupe_by_id(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse duplicate ids, keeping the preferred generation/canonical row."""
    by_id: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for rec in records:
        rid = rec.get("id")
        if not rid:
            continue
        if rid not in by_id:
            order.append(rid)
            by_id[rid] = []
        by_id[rid].append(rec)
    out: list[dict[str, Any]] = []
    for rid in order:
        out.append(pick_preferred_record(by_id[rid]))
    for rec in records:
        if not rec.get("id"):
            out.append(rec)
    return out


def plan_refresh_generations(
    existing: list[dict[str, Any]],
    incoming_keys: set[str],
) -> dict[str, tuple[int, str | None]]:
    """
    For each incoming lineage key, compute (new_generation, supersedes_sequence_id).

    supersedes is the sequence_id of the prior canonical generation when gen > 1.
    """
    max_gen = max_generation_for_keys(existing, incoming_keys)
    plan: dict[str, tuple[int, str | None]] = {}
    for key in incoming_keys:
        prev = max_gen.get(key, 0)
        new_gen = prev + 1 if prev else 1
        supersedes: str | None = None
        if prev:
            for rec in existing:
                if lineage_group_key(rec) != key:
                    continue
                if int(rec.get("corpus_generation", 1)) == prev:
                    supersedes = sequence_id_of(rec)
                    break
        plan[key] = (new_gen, supersedes)
    return plan
