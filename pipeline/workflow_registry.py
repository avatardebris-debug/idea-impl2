"""
pipeline/workflow_registry.py
Register .pipeline/workflows/*.yaml into capability_registry.sqlite.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from pipeline.capability_registry import PROJECT_ROOT, _connect
from pipeline.workflow_schema import WorkflowDefinition, list_workflow_files


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_workflows(conn: sqlite3.Connection | None = None) -> int:
    """Scan workflow YAML files and upsert capability rows."""
    close = False
    if conn is None:
        conn = _connect()
        close = True
    n = 0
    for path in list_workflow_files():
        try:
            wf = WorkflowDefinition.from_yaml_file(path)
        except Exception:
            continue
        kind = wf.kind if wf.kind in ("workflow", "connector") else "workflow"
        entry = f"python scripts/run_workflow.py {wf.slug}"
        example = f"python scripts/run_workflow.py {wf.slug} --help"
        rel_path = path.relative_to(PROJECT_ROOT).as_posix()
        conn.execute(
            """
            INSERT INTO capabilities (
                slug, title, kind, status, purpose, domains, entrypoint, import_path,
                cwd_template, requires, example_invoke, source_project, phase, total_phases, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title=excluded.title, kind=excluded.kind, status=excluded.status,
                purpose=excluded.purpose, domains=excluded.domains,
                entrypoint=excluded.entrypoint, import_path=excluded.import_path,
                requires=excluded.requires, example_invoke=excluded.example_invoke,
                updated_at=excluded.updated_at
            """,
            (
                wf.slug,
                wf.title,
                kind,
                wf.status if wf.status in ("verified", "draft") else "draft",
                wf.purpose or f"Workflow defined in {rel_path}",
                json.dumps(wf.domains),
                entry,
                rel_path,
                ".",
                json.dumps(wf.requires),
                example,
                f"workflow:{wf.slug}",
                _now(),
            ),
        )
        n += 1
    if close:
        conn.commit()
        conn.close()
    return n
