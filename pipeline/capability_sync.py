"""
pipeline/capability_sync.py
Phase 8: multi-instance capability registry sync (local ↔ cloud via export JSON or SQLite).

Workflow:
  1. Instance A: python scripts/sync_capability_registry.py export
  2. Git commit capability_registry_export.json OR include in pipeline_extract zip
  3. Instance B: python scripts/sync_capability_registry.py merge [--from PATH]
     or import_zip.py (auto-merges export from zip)
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.pipeline_mode import legacy_mode

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
PIPELINE_DIR = PROJECT_ROOT / ".pipeline"
REGISTRY_DB = PIPELINE_DIR / "state" / "capability_registry.sqlite"
EXPORT_JSON = PIPELINE_DIR / "state" / "capability_registry_export.json"
EXPORT_JSON_ALT = PROJECT_ROOT / "capability_registry_export.json"  # repo root handoff


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def instance_id() -> str:
    return (
        os.environ.get("CAPABILITY_SYNC_INSTANCE", "").strip()
        or os.environ.get("VAST_INSTANCE_ID", "").strip()
        or socket.gethostname()
    )


def export_snapshot(
    path: Path | None = None,
    *,
    include_metrics: bool = False,
) -> Path:
    """Export capabilities + edges to JSON for merge across machines."""
    if legacy_mode():
        raise RuntimeError("Cannot export registry in legacy mode")

    out = path or EXPORT_JSON
    out.parent.mkdir(parents=True, exist_ok=True)

    if not REGISTRY_DB.exists():
        payload = {
            "meta": {
                "exported_at": _now(),
                "instance": instance_id(),
                "version": 1,
                "capabilities": 0,
                "edges": 0,
            },
            "capabilities": [],
            "edges": [],
        }
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return out

    conn = sqlite3.connect(REGISTRY_DB)
    conn.row_factory = sqlite3.Row
    caps = [dict(r) for r in conn.execute("SELECT * FROM capabilities").fetchall()]
    try:
        edges = [
            dict(r)
            for r in conn.execute(
                "SELECT from_slug, to_slug, source, updated_at FROM capability_edges"
            ).fetchall()
        ]
    except sqlite3.OperationalError:
        edges = []
    conn.close()

    payload: dict[str, Any] = {
        "meta": {
            "exported_at": _now(),
            "instance": instance_id(),
            "version": 1,
            "capabilities": len(caps),
            "edges": len(edges),
        },
        "capabilities": caps,
        "edges": edges,
    }

    if include_metrics:
        metrics_path = PIPELINE_DIR / "state" / "capability_metrics.jsonl"
        if metrics_path.exists():
            lines = metrics_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-2000:]
            payload["metrics_tail"] = [json.loads(l) for l in lines if l.strip()]

    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def _newer(a: str, b: str) -> bool:
    """True if a is strictly newer than b (ISO timestamps)."""
    return (a or "") > (b or "")


def _pick_capability(local: dict | None, remote: dict) -> dict:
    if not local:
        return remote
    # Prefer verified over draft when timestamps equal
    if remote.get("status") == "verified" and local.get("status") != "verified":
        if not _newer(local.get("updated_at", ""), remote.get("updated_at", "")):
            return remote
    if _newer(remote.get("updated_at", ""), local.get("updated_at", "")):
        return remote
    return local


def merge_snapshot(
    path: Path,
    *,
    rebuild_fts: bool = True,
) -> dict[str, int]:
    """
    Merge exported JSON into local capability_registry.sqlite.
    Row-level: keep newer updated_at; verified wins ties vs draft.
    """
    if legacy_mode():
        return {"skipped": 1}

    if not path.exists():
        raise FileNotFoundError(path)

    data = json.loads(path.read_text(encoding="utf-8"))
    remote_caps: list[dict] = data.get("capabilities") or []
    remote_edges: list[dict] = data.get("edges") or []

    from pipeline.capability_registry import SCHEMA_SQL, _connect

    conn = _connect()
    local_map: dict[str, dict] = {}
    for row in conn.execute("SELECT * FROM capabilities").fetchall():
        local_map[row["slug"]] = dict(row)

    merged_caps = 0
    inserted_caps = 0
    for rc in remote_caps:
        slug = rc.get("slug")
        if not slug:
            continue
        chosen = _pick_capability(local_map.get(slug), rc)
        if slug not in local_map:
            inserted_caps += 1
        elif chosen is not local_map.get(slug):
            merged_caps += 1
        local_map[slug] = chosen

    conn.execute("DELETE FROM capabilities")
    for cap in local_map.values():
        cols = [
            "slug", "title", "kind", "status", "purpose", "domains", "entrypoint",
            "import_path", "cwd_template", "requires", "example_invoke", "source_project",
            "phase", "total_phases", "updated_at",
        ]
        conn.execute(
            f"""
            INSERT INTO capabilities ({", ".join(cols)})
            VALUES ({", ".join("?" for _ in cols)})
            """,
            [cap.get(c, "") for c in cols],
        )

    # Merge edges: union with newest updated_at per (from, to, source)
    edge_key: dict[tuple[str, str, str], str] = {}
    try:
        for row in conn.execute(
            "SELECT from_slug, to_slug, source, updated_at FROM capability_edges"
        ).fetchall():
            k = (row["from_slug"], row["to_slug"], row["source"])
            edge_key[k] = row["updated_at"]
    except sqlite3.OperationalError:
        conn.executescript(
            "CREATE TABLE IF NOT EXISTS capability_edges ("
            "from_slug TEXT, to_slug TEXT, source TEXT, updated_at TEXT, "
            "PRIMARY KEY (from_slug, to_slug, source));"
        )

    for e in remote_edges:
        k = (e.get("from_slug", ""), e.get("to_slug", ""), e.get("source", ""))
        if not k[0] or not k[1]:
            continue
        prev = edge_key.get(k, "")
        if _newer(e.get("updated_at", ""), prev):
            edge_key[k] = e.get("updated_at", _now())

    conn.execute("DELETE FROM capability_edges")
    for (fs, ts, src), upd in edge_key.items():
        conn.execute(
            """
            INSERT INTO capability_edges (from_slug, to_slug, source, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (fs, ts, src, upd),
        )

    # Sync requires JSON on capabilities from edges
    by_from: dict[str, list[str]] = {}
    for (fs, ts, _src), _upd in edge_key.items():
        by_from.setdefault(fs, [])
        if ts not in by_from[fs]:
            by_from[fs].append(ts)
    for slug, deps in by_from.items():
        conn.execute(
            "UPDATE capabilities SET requires = ? WHERE slug = ?",
            (json.dumps(deps), slug),
        )

    # Append metrics tail if present
    metrics_merged = 0
    for ev in data.get("metrics_tail") or []:
        try:
            mpath = PIPELINE_DIR / "state" / "capability_metrics.jsonl"
            mpath.parent.mkdir(parents=True, exist_ok=True)
            with mpath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
            metrics_merged += 1
        except Exception:
            pass

    conn.commit()
    conn.close()

    stats = {
        "inserted_capabilities": inserted_caps,
        "updated_capabilities": merged_caps,
        "total_capabilities": len(local_map),
        "edges": len(edge_key),
        "metrics_events": metrics_merged,
        "from_instance": (data.get("meta") or {}).get("instance", "?"),
    }

    if rebuild_fts:
        try:
            from pipeline.capability_graph import rebuild_edges
            from pipeline.capability_search import rebuild_fts_index
            from pipeline.capability_registry import write_capabilities_md

            rebuild_edges()
            rebuild_fts_index()
            write_capabilities_md()
        except Exception:
            pass

    return stats


def replace_from_sqlite(remote_db: Path) -> Path:
    """Full replace local registry DB from another machine's sqlite (fast path)."""
    if not remote_db.exists():
        raise FileNotFoundError(remote_db)
    REGISTRY_DB.parent.mkdir(parents=True, exist_ok=True)
    backup = REGISTRY_DB.with_suffix(".sqlite.bak")
    if REGISTRY_DB.exists():
        shutil.copy2(REGISTRY_DB, backup)
    shutil.copy2(remote_db, REGISTRY_DB)
    return REGISTRY_DB


def find_export_file(start: Path | None = None) -> Path | None:
    """Locate export JSON in standard locations."""
    for p in (
        start,
        EXPORT_JSON,
        EXPORT_JSON_ALT,
        PROJECT_ROOT / "capability_registry_export.json",
    ):
        if p and p.exists():
            return p
    return None
