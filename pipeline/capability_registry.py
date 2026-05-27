"""
pipeline/capability_registry.py
SQLite catalog of pipeline capabilities (projects, shared_libs, repo scripts).

Skipped when PIPELINE_LEGACY=1 (see pipeline.pipeline_mode).
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

from pipeline.paths import (
    capabilities_md,
    get_pipeline_dir,
    goals_dir,
    projects_dir,
    registry_db,
    shared_libs_dir,
)
from pipeline.pipeline_config import PROJECT_ROOT
from pipeline.pipeline_mode import legacy_mode
from pipeline.slug_util import slugify_title as _slugify

AICOMPETE_ROOT = PROJECT_ROOT.parent


def __getattr__(name: str) -> pathlib.Path:
    """Lazy paths for importers that still use REGISTRY_DB / PROJECTS_DIR constants."""
    _map = {
        "REGISTRY_DB": registry_db,
        "CAPABILITIES_MD": capabilities_md,
        "PROJECTS_DIR": projects_dir,
        "SHARED_LIBS_DIR": shared_libs_dir,
        "GOALS_DIR": goals_dir,
    }
    if name in _map:
        return _map[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Phase 6: minimum grounding_score to promote tetra-linked capabilities to verified
TETRA_GROUNDING_THRESHOLD = float(os.environ.get("TETRA_GROUNDING_THRESHOLD", "0.35"))

# Phase 5 edges table (see capability_graph.EDGES_SCHEMA)
from pipeline.capability_graph import EDGES_SCHEMA  # noqa: E402

SCHEMA_SQL = (
    EDGES_SCHEMA
    + """
CREATE TABLE IF NOT EXISTS capabilities (
    slug TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    purpose TEXT DEFAULT '',
    domains TEXT DEFAULT '[]',
    entrypoint TEXT DEFAULT '',
    import_path TEXT DEFAULT '',
    cwd_template TEXT DEFAULT '',
    requires TEXT DEFAULT '[]',
    example_invoke TEXT DEFAULT '',
    source_project TEXT DEFAULT '',
    phase INTEGER DEFAULT 0,
    total_phases INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_capabilities_status ON capabilities(status);
CREATE INDEX IF NOT EXISTS idx_capabilities_kind ON capabilities(kind);
"""
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    registry_db().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(registry_db())
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    return conn


def _guess_domains(title: str, description: str) -> list[str]:
    text = f"{title} {description}".lower()
    domains: list[str] = []
    rules = [
        ("robotics", ("robot", "mujoco", "urdf", "sim-to-real", "primitive")),
        ("video", ("video", "movie", "animatic", "storyboard", "screenplay")),
        ("finance", ("financial", "portfolio", "betting", "market", "trading")),
        ("dropship", ("drop", "shopify", "ecommerce", "seo")),
        ("learning", ("learning", "course", "udemy", "language")),
        ("devops", ("pipeline", "health", "import", "extract")),
    ]
    for domain, keys in rules:
        if any(k in text for k in keys):
            domains.append(domain)
    return domains or ["general"]


def _project_status(state: dict) -> tuple[str, int, int]:
    phase = int(state.get("phase", 0))
    total = int(state.get("total_phases", 1))
    status = state.get("status", "")
    if status == "complete" and phase >= total:
        return "verified", phase, total
    if status in ("budget_exceeded", "dep_waiting"):
        return "draft", phase, total
    if status:
        return "draft", phase, total
    return "draft", phase, total


def _find_cli_entry(workspace: pathlib.Path, slug: str) -> tuple[str, str]:
    """Return (entrypoint, example_invoke)."""
    candidates = [
        workspace / "cli.py",
        workspace / slug / "cli.py",
        workspace / slug.replace("_", "") / "cli.py",
    ]
    for c in candidates:
        if c.is_file():
            rel = c.relative_to(PROJECT_ROOT).as_posix()
            return f"python {rel}", f"python {rel} --help"
    pyproject = workspace / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'\[project\.scripts\]\s*\n((?:[^\[]+\n)*)', text)
        if m:
            line = m.group(1).strip().splitlines()[0] if m.group(1).strip() else ""
            if "=" in line:
                script = line.split("=", 1)[1].strip().strip('"').strip("'")
                return f"python -m {script}", f"python -m {script}"
    return "", ""


def _scan_projects(conn: sqlite3.Connection) -> int:
    n = 0
    if not PROJECTS_DIR.exists():
        return 0
    for proj in PROJECTS_DIR.iterdir():
        if not proj.is_dir():
            continue
        slug = proj.name
        state_file = proj / "state" / "current_idea.json"
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        title = state.get("title", slug).strip("[] ")
        desc = (state.get("description") or "")[:400]
        status, phase, total = _project_status(state)
        workspace = proj / "workspace"
        entry, example = _find_cli_entry(workspace, slug) if workspace.is_dir() else ("", "")
        domains = _guess_domains(title, desc)
        deps = [_slugify(str(d)) for d in (state.get("depends_on") or []) if str(d).strip()]
        conn.execute(
            """
            INSERT INTO capabilities (
                slug, title, kind, status, purpose, domains, entrypoint, import_path,
                cwd_template, requires, example_invoke, source_project, phase, total_phases, updated_at
            ) VALUES (?, ?, 'project', ?, ?, ?, ?, '', ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title=excluded.title, status=excluded.status, purpose=excluded.purpose,
                domains=excluded.domains, entrypoint=excluded.entrypoint,
                cwd_template=excluded.cwd_template, example_invoke=excluded.example_invoke,
                source_project=excluded.source_project, phase=excluded.phase,
                total_phases=excluded.total_phases, updated_at=excluded.updated_at
            """,
            (
                slug,
                title,
                status,
                desc[:300],
                json.dumps(domains),
                entry,
                f".pipeline/projects/{slug}/workspace",
                json.dumps(deps),
                example,
                slug,
                phase,
                total,
                _now(),
            ),
        )
        n += 1
    return n


def register_hermes_capability(
    title: str,
    *,
    purpose: str = "",
    goal_check: str = "",
    achieved: bool = False,
    output_excerpt: str = "",
) -> bool:
    """Phase 6: register Hermes research tasks in the capability catalog."""
    if legacy_mode():
        return False
    slug = _slugify(title)
    status = "verified" if achieved else "draft"
    desc = (purpose or goal_check or title)[:300]
    example = f"# hermes_task — goal_check: {(goal_check or '')[:120]}"
    if output_excerpt:
        example += f"\n# output: {output_excerpt[:200]}"
    conn = _connect()
    conn.execute(
        """
        INSERT INTO capabilities (
            slug, title, kind, status, purpose, domains, entrypoint, import_path,
            cwd_template, requires, example_invoke, source_project, phase, total_phases, updated_at
        ) VALUES (?, ?, 'hermes_task', ?, ?, '["general"]', '', '', ?, '[]', ?, 'hermes', 0, 0, ?)
        ON CONFLICT(slug) DO UPDATE SET
            status=excluded.status, purpose=excluded.purpose,
            example_invoke=excluded.example_invoke, updated_at=excluded.updated_at
        """,
        (
            slug,
            title.strip("[] "),
            status,
            desc,
            str(GOALS_DIR),
            example,
            _now(),
        ),
    )
    conn.commit()
    conn.close()
    try:
        from pipeline.capability_metrics import log_capability_event

        log_capability_event("register", slug, ok=achieved, detail="hermes_task")
    except Exception:
        pass
    return True


def promote_draft_shared_libs_for_project(source_project: str) -> int:
    """Phase 6: after project verified, promote shared_libs sourced from that project."""
    if legacy_mode() or not source_project:
        return 0
    conn = _connect()
    cur = conn.execute(
        """
        UPDATE capabilities SET status = 'verified', updated_at = ?
        WHERE kind = 'shared_lib' AND source_project = ? AND status = 'draft'
        """,
        (_now(), source_project),
    )
    n = cur.rowcount
    conn.commit()
    conn.close()
    if n:
        try:
            from pipeline.capability_metrics import log_capability_event

            log_capability_event("promote", source_project, detail=f"shared_libs={n}")
        except Exception:
            pass
    return n


def register_tetra_meta_learn_capability(
    *,
    grounding_score: float | None = None,
    achieved: bool = False,
) -> bool:
    """Phase 6: register Throng6 tetra_meta_learn toolcall in capability catalog."""
    if legacy_mode():
        return False
    slug = "tetra_meta_learn"
    threshold = TETRA_GROUNDING_THRESHOLD
    verified = achieved or (
        grounding_score is not None and grounding_score >= threshold
    )
    status = "verified" if verified else "draft"
    entry = "python -m throng6 toolcall"
    example = (
        '{"tool":"tetra_meta_learn","env":{"type":"mario_ascii"},'
        '"budget_steps":400,"outer_cycles":2} | python -m throng6 toolcall'
    )
    purpose = (
        "Throng6 outer+inner meta-learning session via JSON toolcall. "
        f"Promotes to verified when grounding_score >= {threshold}."
    )
    if grounding_score is not None:
        purpose += f" Last score: {grounding_score:.3f}."

    conn = _connect()
    conn.execute(
        """
        INSERT INTO capabilities (
            slug, title, kind, status, purpose, domains, entrypoint, import_path,
            cwd_template, requires, example_invoke, source_project, phase, total_phases, updated_at
        ) VALUES (?, ?, 'pipeline_tool', ?, ?, '["learning","tetra"]', ?, ?, ?, '[]', ?, 'throng6', 0, 0, ?)
        ON CONFLICT(slug) DO UPDATE SET
            status=excluded.status, purpose=excluded.purpose,
            entrypoint=excluded.entrypoint, example_invoke=excluded.example_invoke,
            updated_at=excluded.updated_at
        """,
        (
            slug,
            "tetra_meta_learn",
            status,
            purpose,
            entry,
            "pipeline.tools.tetra_meta_learn",
            str(AICOMPETE_ROOT / "throng6"),
            example,
            _now(),
        ),
    )
    conn.commit()
    conn.close()
    try:
        from pipeline.capability_metrics import log_capability_event

        log_capability_event(
            "register",
            slug,
            ok=verified,
            detail=f"grounding={grounding_score}",
        )
    except Exception:
        pass
    return True


def promote_if_grounded(slug: str, grounding_score: float) -> bool:
    """Promote capability to verified when grounding_score meets threshold."""
    if legacy_mode() or grounding_score < TETRA_GROUNDING_THRESHOLD:
        return False
    conn = _connect()
    cur = conn.execute(
        """
        UPDATE capabilities SET status = 'verified', updated_at = ?, purpose = purpose || ?
        WHERE slug = ? AND status = 'draft'
        """,
        (_now(), f" [grounded:{grounding_score:.3f}]", slug),
    )
    n = cur.rowcount
    conn.commit()
    conn.close()
    return n > 0


def register_shared_lib_capability(
    component_name: str,
    *,
    source_project: str = "",
    purpose: str = "",
    status: str = "draft",
) -> bool:
    """Phase 6: register promoted shared_lib after reviewer extraction."""
    if legacy_mode():
        return False
    slug = f"shared_{_slugify(component_name)}"
    import_path = f"shared_libs.{component_name}"
    conn = _connect()
    conn.execute(
        """
        INSERT INTO capabilities (
            slug, title, kind, status, purpose, domains, entrypoint, import_path,
            cwd_template, requires, example_invoke, source_project, phase, total_phases, updated_at
        ) VALUES (?, ?, 'shared_lib', ?, ?, '["general"]', '', ?, ?, '[]', ?, ?, 0, 0, ?)
        ON CONFLICT(slug) DO UPDATE SET
            status=excluded.status, purpose=excluded.purpose,
            import_path=excluded.import_path, source_project=excluded.source_project,
            updated_at=excluded.updated_at
        """,
        (
            slug,
            f"shared_lib:{component_name}",
            status,
            purpose or f"Promoted from {source_project or 'review'}",
            import_path,
            str(SHARED_LIBS_DIR),
            f"# from shared_libs.{component_name}",
            source_project,
            _now(),
        ),
    )
    conn.commit()
    conn.close()
    return True


def _scan_shared_libs(conn: sqlite3.Connection) -> int:
    n = 0
    if not SHARED_LIBS_DIR.exists():
        return 0
    for d in SHARED_LIBS_DIR.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        slug = f"shared_{d.name}"
        py_files = list(d.rglob("*.py"))
        if not py_files:
            continue
        import_path = ""
        init = d / "__init__.py"
        if init.exists():
            import_path = f"shared_libs.{d.name}"
        entry = ""
        example = f"# import from {d.as_posix()}"
        conn.execute(
            """
            INSERT INTO capabilities (
                slug, title, kind, status, purpose, domains, entrypoint, import_path,
                cwd_template, requires, example_invoke, source_project, phase, total_phases, updated_at
            ) VALUES (?, ?, 'shared_lib', 'verified', ?, '["general"]', '', ?, ?, '[]', ?, '', 0, 0, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title=excluded.title, purpose=excluded.purpose, import_path=excluded.import_path,
                updated_at=excluded.updated_at
            """,
            (
                slug,
                f"shared_lib:{d.name}",
                f"Promoted shared library at .pipeline/shared_libs/{d.name}/",
                import_path,
                str(SHARED_LIBS_DIR),
                example,
                _now(),
            ),
        )
        n += 1
    return n


def _scan_pipeline_scripts(conn: sqlite3.Connection) -> int:
    scripts = [
        ("pipeline_runner", "pipeline/runner.py", "Main multi-agent pipeline orchestrator"),
        ("pipeline_extract", "extract.py", "Zip pipeline state for cloud transfer"),
        ("pipeline_import_zip", "import_zip.py", "Import pipeline_extract zip into local state"),
        ("pipeline_health_check", "health_check.py", "Cross-project health check and --fix"),
        ("pipeline_reset_budget", "reset_budget_exceeded.py", "Reset budget_exceeded projects and polish queue"),
        ("pipeline_grok_sidecar", "pipeline/grok_sidecar.py", "Grok validation sidecar CLI"),
    ]
    for slug, rel, purpose in scripts:
        path = PROJECT_ROOT / rel.replace("/", os.sep)
        if not path.is_file():
            continue
        conn.execute(
            """
            INSERT INTO capabilities (
                slug, title, kind, status, purpose, domains, entrypoint, import_path,
                cwd_template, requires, example_invoke, source_project, phase, total_phases, updated_at
            ) VALUES (?, ?, 'pipeline_script', 'verified', ?, '["devops"]', ?, '', ?, '[]', ?, '', 0, 0, ?)
            ON CONFLICT(slug) DO UPDATE SET
                purpose=excluded.purpose, entrypoint=excluded.entrypoint,
                example_invoke=excluded.example_invoke, updated_at=excluded.updated_at
            """,
            (
                slug,
                rel,
                purpose,
                f"python {rel}",
                str(PROJECT_ROOT),
                f"python {rel} --help",
                _now(),
            ),
        )
    return len(scripts)


def refresh_capability(slug: str) -> bool:
    """Upsert one project row after completion. No-op in legacy mode."""
    if legacy_mode():
        return False
    proj = PROJECTS_DIR / slug
    state_file = proj / "state" / "current_idea.json"
    if not state_file.exists():
        return False
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return False
    title = state.get("title", slug).strip("[] ")
    desc = (state.get("description") or "")[:400]
    status, phase, total = _project_status(state)
    workspace = proj / "workspace"
    entry, example = _find_cli_entry(workspace, slug) if workspace.is_dir() else ("", "")
    domains = _guess_domains(title, desc)
    deps = [_slugify(str(d)) for d in (state.get("depends_on") or []) if str(d).strip()]
    conn = _connect()
    conn.execute(
        """
        INSERT INTO capabilities (
            slug, title, kind, status, purpose, domains, entrypoint, import_path,
            cwd_template, requires, example_invoke, source_project, phase, total_phases, updated_at
        ) VALUES (?, ?, 'project', ?, ?, ?, ?, '', ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            title=excluded.title, status=excluded.status, purpose=excluded.purpose,
            domains=excluded.domains, entrypoint=excluded.entrypoint,
            cwd_template=excluded.cwd_template, example_invoke=excluded.example_invoke,
            source_project=excluded.source_project, phase=excluded.phase,
            total_phases=excluded.total_phases, updated_at=excluded.updated_at
        """,
        (
            slug,
            title,
            status,
            desc[:300],
            json.dumps(domains),
            entry,
            f".pipeline/projects/{slug}/workspace",
            json.dumps(deps),
            example,
            slug,
            phase,
            total,
            _now(),
        ),
    )
    conn.commit()
    conn.close()
    from pipeline.capability_graph import rebuild_edges

    rebuild_edges()
    if status == "verified":
        promote_draft_shared_libs_for_project(slug)
    write_capabilities_md()
    return True


def _prune_orphan_capabilities(conn: sqlite3.Connection) -> int:
    """Remove project rows (and edges) when .pipeline/projects/<slug>/ is gone."""
    live: set[str] = set()
    if PROJECTS_DIR.exists():
        for p in PROJECTS_DIR.iterdir():
            if p.is_dir() and (p / "state" / "current_idea.json").exists():
                live.add(p.name)
    removed = 0
    for row in conn.execute("SELECT slug FROM capabilities WHERE kind = 'project'").fetchall():
        slug = row["slug"]
        if slug not in live:
            conn.execute("DELETE FROM capabilities WHERE slug = ?", (slug,))
            conn.execute(
                "DELETE FROM capability_edges WHERE from_slug = ? OR to_slug = ?",
                (slug, slug),
            )
            removed += 1
    return removed


def _apply_status_overrides() -> int:
    """Apply capability_overrides.yaml status: entries."""
    from pipeline.capability_graph import load_overrides

    ov = load_overrides()
    status_map = ov.get("status") or {}
    if not isinstance(status_map, dict) or not status_map:
        return 0
    conn = _connect()
    n = 0
    for slug, st in status_map.items():
        s = _slugify(str(slug))
        if s and str(st) in ("verified", "draft"):
            conn.execute(
                "UPDATE capabilities SET status = ?, updated_at = ? WHERE slug = ?",
                (str(st), _now(), s),
            )
            n += 1
    conn.commit()
    conn.close()
    return n


def rebuild_registry() -> dict[str, int]:
    """Full scan → SQLite + CAPABILITIES.md. No-op in legacy mode."""
    if legacy_mode():
        return {"skipped": 1, "reason": "legacy_mode"}

    conn = _connect()
    pruned = _prune_orphan_capabilities(conn)
    projects = _scan_projects(conn)
    libs = _scan_shared_libs(conn)
    scripts = _scan_pipeline_scripts(conn)
    from pipeline.workflow_registry import register_workflows

    workflows = register_workflows(conn)
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM capabilities").fetchone()[0]
    conn.close()

    tetra_tool = register_tetra_meta_learn_capability()

    from pipeline.capability_graph import rebuild_edges

    edges = rebuild_edges()
    _apply_status_overrides()
    fts_rows = 0
    try:
        from pipeline.capability_search import rebuild_fts_index

        conn = _connect()
        fts_rows = rebuild_fts_index(conn)
        conn.commit()
        conn.close()
    except Exception:
        pass
    write_capabilities_md()
    return {
        "projects": projects,
        "shared_libs": libs,
        "pipeline_scripts": scripts,
        "workflows": workflows,
        "tetra_tool": int(bool(tetra_tool)),
        "edges": edges,
        "pruned": pruned,
        "fts_indexed": fts_rows,
        "total": total,
    }


def write_capabilities_md() -> None:
    if legacy_mode() or not registry_db().exists():
        return
    conn = _connect()
    rows = conn.execute(
        """
        SELECT slug, title, kind, status, purpose, entrypoint, example_invoke, domains
        FROM capabilities
        ORDER BY
            CASE status WHEN 'verified' THEN 0 ELSE 1 END,
            kind, title
        """
    ).fetchall()
    conn.close()

    lines = [
        "# Pipeline capabilities (generated)",
        "",
        f"Updated: {_now()}",
        "",
        "Regenerate: `python scripts/build_capability_registry.py`",
        "",
        "Database: `.pipeline/state/capability_registry.sqlite`",
        "",
        "Use `--legacy` on the runner to disable capability injection (pre-registry behavior).",
        "",
        "---",
        "",
    ]
    current_kind = ""
    for row in rows:
        if row["kind"] != current_kind:
            current_kind = row["kind"]
            lines.append(f"## {current_kind}")
            lines.append("")
        lines.append(f"- **{row['title']}** (`{row['slug']}`) — _{row['status']}_")
        if row["purpose"]:
            lines.append(f"  - {row['purpose'][:200]}")
        if row["entrypoint"]:
            lines.append(f"  - run: `{row['entrypoint']}`")
        if row["example_invoke"]:
            lines.append(f"  - example: `{row['example_invoke']}`")
        lines.append("")

    CAPABILITIES_MD.parent.mkdir(parents=True, exist_ok=True)
    CAPABILITIES_MD.write_text("\n".join(lines), encoding="utf-8")


def capabilities_summary(
    project_slug: str = "",
    *,
    max_rows: int = 25,
    max_chars: int = 4000,
) -> str:
    """Short markdown block for agent context. Empty in legacy mode."""
    if legacy_mode() or not registry_db().exists():
        return ""

    conn = _connect()
    if project_slug:
        domains_row = conn.execute(
            "SELECT domains FROM capabilities WHERE slug = ?", (project_slug,)
        ).fetchone()
        domain_hint = []
        if domains_row:
            try:
                domain_hint = json.loads(domains_row["domains"] or "[]")
            except json.JSONDecodeError:
                pass
        rows = conn.execute(
            """
            SELECT slug, title, kind, status, purpose, entrypoint, example_invoke
            FROM capabilities
            WHERE status = 'verified'
            ORDER BY
                CASE WHEN domains LIKE ? THEN 0 ELSE 1 END,
                kind, title
            LIMIT ?
            """,
            (f"%{domain_hint[0] if domain_hint else 'general'}%", max_rows),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT slug, title, kind, status, purpose, entrypoint, example_invoke
            FROM capabilities
            WHERE status = 'verified'
            ORDER BY kind, title
            LIMIT ?
            """,
            (max_rows,),
        ).fetchall()
    conn.close()

    if not rows:
        return ""

    parts = [
        "## Capability registry (reuse before building)",
        f"Full catalog: `{CAPABILITIES_MD.relative_to(PROJECT_ROOT)}`",
        "",
    ]
    for row in rows:
        line = f"- `{row['slug']}` ({row['kind']}): {row['title']}"
        if row["entrypoint"]:
            line += f" — `{row['entrypoint']}`"
        elif row["purpose"]:
            line += f" — {row['purpose'][:80]}"
        parts.append(line)
        if sum(len(p) for p in parts) > max_chars:
            parts.append("- ... (truncated; see CAPABILITIES.md)")
            break

    parts.append("")
    parts.append(
        "Prefer shared_libs and verified project CLIs (see entrypoint) over reimplementing."
    )
    return "\n".join(parts)[:max_chars]


def list_capabilities(domain: str | None = None, status: str = "verified") -> list[dict[str, Any]]:
    if not registry_db().exists():
        return []
    conn = _connect()
    q = "SELECT slug, title, kind, status, purpose, entrypoint FROM capabilities WHERE 1=1"
    params: list[Any] = []
    if status:
        q += " AND status = ?"
        params.append(status)
    if domain:
        q += " AND domains LIKE ?"
        params.append(f"%{domain}%")
    q += " ORDER BY title"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows
