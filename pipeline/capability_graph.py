"""
pipeline/capability_graph.py
Phase 5: dependency graph from master_ideas, goal trees, and project state.

Edges: from_slug requires to_slug (prerequisite must be verified before routing).
"""

from __future__ import annotations

import json
import pathlib
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

from pipeline.paths import goals_dir, projects_dir, registry_db, state_dir
from pipeline.pipeline_config import PROJECT_ROOT
from pipeline.pipeline_mode import legacy_mode

MASTER_IDEAS = PROJECT_ROOT / "master_ideas.md"


def _overrides_path() -> pathlib.Path:
    return state_dir() / "capability_overrides.yaml"

REQUIRES_RE = re.compile(
    r"\brequires:\s*([\w,\s_-]+?)(?:[\]\s.]|$)",
    re.IGNORECASE,
)
IDEA_LINE_RE = re.compile(
    r"-?\s*\[ \]\s+\*\*(.+?)\*\*\s*[—–-]\s*(.*)",
)
IDEA_LINE_ALT_RE = re.compile(
    r"-?\s*\[ \]\s+\[(.+?)\]\s*[—–-]\s*(.*)",
)

EDGES_SCHEMA = """
CREATE TABLE IF NOT EXISTS capability_edges (
    from_slug TEXT NOT NULL,
    to_slug TEXT NOT NULL,
    source TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (from_slug, to_slug, source)
);
CREATE INDEX IF NOT EXISTS idx_edges_to ON capability_edges(to_slug);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(title: str) -> str:
    t = title.strip("[] ").lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")[:60]


def parse_requires_from_text(text: str) -> list[str]:
    deps: list[str] = []
    seen: set[str] = set()
    for m in REQUIRES_RE.finditer(text):
        raw = m.group(1)
        for part in re.split(r"[,;]+", raw):
            s = _slugify(part.strip()) if part.strip() else ""
            if s and s not in seen:
                seen.add(s)
                deps.append(s)
    return deps


def _connect() -> sqlite3.Connection:
    registry_db().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(registry_db())
    conn.row_factory = sqlite3.Row
    conn.executescript(EDGES_SCHEMA)
    return conn


def _project_verified(slug: str) -> bool:
    state_file = projects_dir() / slug / "state" / "current_idea.json"
    if not state_file.exists():
        return False
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
        return (
            st.get("status") == "complete"
            and int(st.get("phase", 0)) >= int(st.get("total_phases", 1))
        )
    except Exception:
        return False


def _registry_verified(slug: str) -> bool:
    if not registry_db().exists():
        return _project_verified(slug)
    conn = _connect()
    row = conn.execute(
        "SELECT status FROM capabilities WHERE slug = ?", (slug,)
    ).fetchone()
    conn.close()
    if row:
        return row["status"] == "verified"
    return _project_verified(slug)


def load_overrides() -> dict[str, Any]:
    if not _overrides_path().exists():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    try:
        data = yaml.safe_load(_overrides_path().read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def missing_requires(slug: str, *, extra_requires: list[str] | None = None) -> list[str]:
    """Return prerequisite slugs that are not verified."""
    requires = list(extra_requires or [])
    requires.extend(get_requires(slug))
    missing: list[str] = []
    for dep in requires:
        if not _registry_verified(dep):
            missing.append(dep)
    return missing


def is_routable(slug: str, *, extra_requires: list[str] | None = None) -> bool:
    return len(missing_requires(slug, extra_requires=extra_requires)) == 0


def get_requires(slug: str) -> list[str]:
    if not registry_db().exists():
        return []
    conn = _connect()
    rows = conn.execute(
        "SELECT DISTINCT to_slug FROM capability_edges WHERE from_slug = ?",
        (slug,),
    ).fetchall()
    deps = [r["to_slug"] for r in rows]
    if deps:
        conn.close()
        return deps
    row = conn.execute(
        "SELECT requires FROM capabilities WHERE slug = ?", (slug,)
    ).fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["requires"] or "[]")
        except json.JSONDecodeError:
            pass
    return []


def _iter_master_idea_lines(path: pathlib.Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = IDEA_LINE_RE.match(line) or IDEA_LINE_ALT_RE.match(line)
        if m:
            yield _slugify(m.group(1)), m.group(2)


def _edges_from_master_ideas(path: pathlib.Path = MASTER_IDEAS) -> list[tuple[str, str, str]]:
    edges: list[tuple[str, str, str]] = []
    for from_slug, desc in _iter_master_idea_lines(path):
        for dep in parse_requires_from_text(desc):
            if dep != from_slug:
                edges.append((from_slug, dep, "master_ideas"))
    return edges


def _edges_from_goals() -> list[tuple[str, str, str]]:
    edges: list[tuple[str, str, str]] = []
    if not goals_dir().exists():
        return edges
    for gf in goals_dir().glob("*.json"):
        try:
            data = json.loads(gf.read_text(encoding="utf-8"))
        except Exception:
            continue
        goal_id = _slugify(data.get("goal_id", gf.stem))
        for branch in data.get("branches", []):
            bid = branch.get("id", "")
            from_slug = _slugify(branch.get("subgoal", bid) or bid)
            if not from_slug:
                continue
            for dep in branch.get("requires", []) or []:
                dep_slug = _slugify(str(dep))
                if dep_slug:
                    edges.append((from_slug, dep_slug, "goal_tree"))
            desc = branch.get("description", "")
            for dep in parse_requires_from_text(desc):
                if dep != from_slug:
                    edges.append((from_slug, dep, "goal_tree"))
    return edges


def _edges_from_project_state() -> list[tuple[str, str, str]]:
    edges: list[tuple[str, str, str]] = []
    projects = projects_dir()
    if not projects.exists():
        return edges
    for proj in projects.iterdir():
        sf = proj / "state" / "current_idea.json"
        if not sf.exists():
            continue
        try:
            st = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        from_slug = proj.name
        for dep in st.get("depends_on", []) or []:
            dep_slug = _slugify(str(dep))
            if dep_slug:
                edges.append((from_slug, dep_slug, "state"))
    return edges


def _edges_from_overrides() -> list[tuple[str, str, str]]:
    ov = load_overrides()
    edges: list[tuple[str, str, str]] = []
    req_map = ov.get("requires") or {}
    if isinstance(req_map, dict):
        for from_slug, deps in req_map.items():
            fs = _slugify(str(from_slug))
            if not fs:
                continue
            items = deps if isinstance(deps, list) else [deps]
            for dep in items:
                ds = _slugify(str(dep))
                if ds:
                    edges.append((fs, ds, "override"))
    return edges


def rebuild_edges(conn: sqlite3.Connection | None = None) -> int:
    """Rebuild capability_edges and sync capabilities.requires JSON."""
    if legacy_mode():
        return 0

    own = conn is None
    if own:
        conn = _connect()

    conn.execute("DELETE FROM capability_edges")
    seen: set[tuple[str, str, str]] = set()
    n = 0
    for batch in (
        _edges_from_master_ideas(),
        _edges_from_goals(),
        _edges_from_project_state(),
        _edges_from_overrides(),
    ):
        for from_slug, to_slug, source in batch:
            key = (from_slug, to_slug, source)
            if key in seen:
                continue
            seen.add(key)
            conn.execute(
                """
                INSERT INTO capability_edges (from_slug, to_slug, source, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (from_slug, to_slug, source, _now()),
            )
            n += 1

    # Aggregate requires per from_slug into capabilities table
    by_from: dict[str, list[str]] = {}
    for from_slug, to_slug, _ in seen:
        by_from.setdefault(from_slug, [])
        if to_slug not in by_from[from_slug]:
            by_from[from_slug].append(to_slug)

    for from_slug, deps in by_from.items():
        conn.execute(
            "UPDATE capabilities SET requires = ? WHERE slug = ?",
            (json.dumps(deps), from_slug),
        )

    if own:
        conn.commit()
        conn.close()
    return n


def blocked_unchecked_ideas(
    ideas_path: pathlib.Path = MASTER_IDEAS,
) -> list[dict[str, Any]]:
    """Unchecked master_ideas lines whose requires: deps are not all verified."""
    blocked: list[dict[str, Any]] = []
    for from_slug, desc in _iter_master_idea_lines(ideas_path):
        deps = parse_requires_from_text(desc)
        if not deps:
            continue
        missing = [d for d in deps if not _registry_verified(d)]
        if missing:
            blocked.append({
                "slug": from_slug,
                "requires": deps,
                "missing": missing,
            })
    return blocked


def stale_requires_in_markdown(
    ideas_path: pathlib.Path = MASTER_IDEAS,
) -> list[dict[str, Any]]:
    """requires: slugs that don't exist as projects or capabilities."""
    stale: list[dict[str, Any]] = []
    known: set[str] = set()
    if registry_db().exists():
        conn = _connect()
        rows = conn.execute("SELECT slug FROM capabilities").fetchall()
        conn.close()
        known = {r["slug"] for r in rows}
    projects = projects_dir()
    if projects.exists():
        known |= {d.name for d in projects.iterdir() if d.is_dir()}

    for from_slug, desc in _iter_master_idea_lines(ideas_path):
        for dep in parse_requires_from_text(desc):
            if dep not in known:
                stale.append({
                    "from_slug": from_slug,
                    "unknown_dep": dep,
                    "line_hint": desc[:80],
                })
    return stale


def write_graphviz_dot(path: pathlib.Path | None = None) -> pathlib.Path:
    """Emit scripts/capability_graph.dot for Graphviz."""
    out = path or (PROJECT_ROOT / "scripts" / "capability_graph.dot")
    out.parent.mkdir(parents=True, exist_ok=True)

    nodes: set[str] = set()
    edges: list[tuple[str, str]] = []
    if registry_db().exists():
        conn = _connect()
        for row in conn.execute(
            "SELECT from_slug, to_slug FROM capability_edges"
        ).fetchall():
            nodes.add(row["from_slug"])
            nodes.add(row["to_slug"])
            edges.append((row["from_slug"], row["to_slug"]))
        conn.close()

    verified = set()
    if registry_db().exists():
        conn = _connect()
        for row in conn.execute(
            "SELECT slug FROM capabilities WHERE status = 'verified'"
        ).fetchall():
            verified.add(row["slug"])
        conn.close()

    lines = ["digraph capability_deps {", '  rankdir=LR;']
    for n in sorted(nodes):
        label = n.replace("_", "\\n")
        color = "palegreen" if n in verified else "lightyellow"
        lines.append(f'  "{n}" [label="{label}", style=filled, fillcolor={color}];')
    for a, b in edges:
        lines.append(f'  "{a}" -> "{b}";')
    lines.append("}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
