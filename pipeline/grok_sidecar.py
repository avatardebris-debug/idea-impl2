"""
pipeline/grok_sidecar.py
CLI tools for Grok Build (or any external agent) to work alongside the GPU pipeline.

Grok handles planning, implement, debrief, and non-GPU work; the runner keeps executor
on Ollama. Artifacts (tasks.md, workspace/, validation_report.md) stay the contract
for harvest.py and bug_memory.

Usage (from repo root):
    python -m pipeline.grok_sidecar status --slug my_project --phase 1
    python -m pipeline.grok_sidecar context --slug my_project --phase 1
    python -m pipeline.grok_sidecar validate --slug my_project --phase 1
    python -m pipeline.grok_sidecar debrief-template --slug my_project --phase 1
    python -m pipeline.grok_sidecar record-bugs --slug my_project --phase 1 --file grok_debrief.json
    python -m pipeline.grok_sidecar provenance --slug my_project --phase 1 --implementer grok_build
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from datetime import datetime, timezone
from typing import Any

_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
PIPELINE_DIR = _PROJECT_ROOT / ".pipeline"
PROJECTS_DIR = PIPELINE_DIR / "projects"

VERDICT_PASS = re.compile(r"Verdict:\s*PASS", re.IGNORECASE)


def _read(path: pathlib.Path, limit: int = 0) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:limit] if limit > 0 else text


def resolve_project(slug: str) -> pathlib.Path:
    proj = PROJECTS_DIR / slug
    if not proj.is_dir():
        raise SystemExit(f"Project not found: {proj}")
    return proj


def phase_paths(proj: pathlib.Path, phase: int) -> dict[str, pathlib.Path]:
    phase_dir = proj / "phases" / f"phase_{phase}"
    return {
        "proj": proj,
        "phase_dir": phase_dir,
        "workspace": proj / "workspace",
        "tasks": phase_dir / "tasks.md",
        "master_plan": proj / "state" / "master_plan.md",
        "fix_report": phase_dir / "fix_report.md",
        "validation_report": phase_dir / "validation_report.md",
        "grok_debrief": phase_dir / "grok_debrief.json",
        "grok_provenance": phase_dir / "grok_provenance.json",
        "current_idea": proj / "state" / "current_idea.json",
    }


def cmd_status(slug: str, phase: int) -> int:
    paths = phase_paths(resolve_project(slug), phase)
    val = _read(paths["validation_report"])
    passed = bool(VERDICT_PASS.search(val)) if val else False
    state = {}
    if paths["current_idea"].exists():
        try:
            state = json.loads(paths["current_idea"].read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {}
    print(f"slug:       {slug}")
    print(f"phase:      {phase}")
    print(f"status:     {state.get('status', '(unknown)')}")
    print(f"workspace:  {paths['workspace']}")
    print(f"tasks.md:   {'yes' if paths['tasks'].exists() else 'missing'}")
    print(f"validation: {'PASS' if passed else 'FAIL or missing'}")
    print(f"paths:")
    for k, p in paths.items():
        if k in ("proj", "phase_dir"):
            continue
        print(f"  {k}: {p}")
    return 0 if passed else 1


def cmd_context(slug: str, phase: int, as_json: bool = True) -> int:
    paths = phase_paths(resolve_project(slug), phase)
    pack: dict[str, Any] = {
        "slug": slug,
        "phase": phase,
        "workspace_path": str(paths["workspace"].resolve()),
        "tasks_path": str(paths["tasks"].resolve()),
        "tasks_md": _read(paths["tasks"], limit=12000),
        "master_plan_excerpt": _read(paths["master_plan"], limit=8000),
        "fix_report_excerpt": _read(paths["fix_report"], limit=6000),
        "validation_report_excerpt": _read(paths["validation_report"], limit=6000),
        "validation_pass": bool(VERDICT_PASS.search(_read(paths["validation_report"]))),
        "grok_instructions": (
            "After implement: run validate, then fill grok_debrief.json and record-bugs. "
            "Do not mark project complete — runner owns truth/completions."
        ),
    }
    if as_json:
        print(json.dumps(pack, indent=2, ensure_ascii=False))
    else:
        print(pack["tasks_md"] or "(no tasks.md)")
    return 0


def cmd_validate(slug: str, phase: int) -> int:
    sys.path.insert(0, str(_PROJECT_ROOT))
    from pipeline.agents.validator import build_validation_report, run_pytest

    paths = phase_paths(resolve_project(slug), phase)
    ws = paths["workspace"]
    if not ws.is_dir():
        raise SystemExit(f"Workspace missing: {ws}")

    paths["phase_dir"].mkdir(parents=True, exist_ok=True)
    tasks_content = _read(paths["tasks"])
    result = run_pytest(ws)
    report, is_pass = build_validation_report(phase, result, tasks_content, ws)
    paths["validation_report"].write_text(report, encoding="utf-8")

    tag = "PASS" if is_pass else "FAIL"
    print(f"Wrote {paths['validation_report']} — {tag}")
    if result.get("summary_line"):
        print(f"  {result['summary_line']}")
    return 0 if is_pass else 2


def cmd_debrief_template(slug: str, phase: int) -> int:
    paths = phase_paths(resolve_project(slug), phase)
    paths["phase_dir"].mkdir(parents=True, exist_ok=True)
    template = {
        "slug": slug,
        "phase": phase,
        "implementer": "grok_build",
        "session_notes": "",
        "bugs": [
            {
                "type": "resolution",
                "failure_reason": "e.g. ModuleNotFoundError: no module named foo",
                "fix_summary": "e.g. Added foo to requirements and __init__.py",
                "retry_count": 0,
            },
            {
                "type": "mistake",
                "failure_reason": "e.g. Used relative imports outside package root",
                "fix_summary": "Avoid in future phases",
                "retry_count": 0,
            },
        ],
    }
    paths["grok_debrief"].write_text(
        json.dumps(template, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote template: {paths['grok_debrief']}")
    print("Fill bugs[] after implement, then: record-bugs --file ...")
    return 0


def _load_debrief_payload(path: pathlib.Path | None, json_inline: str | None) -> dict:
    if path:
        if not path.exists():
            raise SystemExit(f"File not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))
    if json_inline:
        return json.loads(json_inline)
    raise SystemExit("Provide --file or --json")


def cmd_record_bugs(slug: str, phase: int, file: str | None, json_inline: str | None) -> int:
    sys.path.insert(0, str(_PROJECT_ROOT))
    from pipeline.bug_memory import record_grok_debrief

    payload = _load_debrief_payload(
        pathlib.Path(file) if file else None,
        json_inline,
    )
    entries = payload.get("bugs") or payload.get("resolutions") or payload.get("entries")
    if not isinstance(entries, list):
        raise SystemExit("JSON must contain a 'bugs' (or 'resolutions') array")

    n = record_grok_debrief(slug, phase, entries)
    paths = phase_paths(resolve_project(slug), phase)
    paths["phase_dir"].mkdir(parents=True, exist_ok=True)
    paths["grok_debrief"].write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    notes = (payload.get("session_notes") or payload.get("notes") or "").strip()
    if notes:
        log = paths["phase_dir"] / "grok_session_notes.md"
        log.write_text(f"# Grok session notes — phase {phase}\n\n{notes}\n", encoding="utf-8")
        print(f"Wrote {log}")

    print(f"Recorded {n} bug memory entries (source=grok) for {slug} phase {phase}")
    return 0


def cmd_provenance(
    slug: str,
    phase: int,
    implementer: str,
    session_log: str | None,
) -> int:
    paths = phase_paths(resolve_project(slug), phase)
    paths["phase_dir"].mkdir(parents=True, exist_ok=True)
    record = {
        "slug": slug,
        "phase": phase,
        "implementer": implementer,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "harvest_contract": {
            "input": "phases/phase_N/tasks.md + state/master_plan.md",
            "output": "workspace/ at validator PASS",
            "authority": "phases/phase_N/validation_report.md",
        },
        "session_log": str(pathlib.Path(session_log).resolve()) if session_log else None,
    }
    paths["grok_provenance"].write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {paths['grok_provenance']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Grok Build sidecar — validate, debrief, bug memory (no GPU)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_slug_phase(p: argparse.ArgumentParser) -> None:
        p.add_argument("--slug", required=True, help="Project slug under .pipeline/projects/")
        p.add_argument("--phase", type=int, default=1, help="Phase number (default 1)")

    p_status = sub.add_parser("status", help="Show phase paths and validation state")
    add_slug_phase(p_status)

    p_ctx = sub.add_parser("context", help="Emit JSON context pack for Grok prompt")
    add_slug_phase(p_ctx)

    p_val = sub.add_parser("validate", help="Run deterministic pytest → validation_report.md")
    add_slug_phase(p_val)

    p_tpl = sub.add_parser("debrief-template", help="Write grok_debrief.json template")
    add_slug_phase(p_tpl)

    p_rec = sub.add_parser("record-bugs", help="Import grok_debrief.json → bug_resolutions.jsonl")
    add_slug_phase(p_rec)
    p_rec.add_argument("--file", help="Path to debrief JSON")
    p_rec.add_argument("--json", dest="json_inline", help="Inline JSON string")

    p_prov = sub.add_parser("provenance", help="Record who implemented this phase (harvest metadata)")
    add_slug_phase(p_prov)
    p_prov.add_argument(
        "--implementer",
        default="grok_build",
        help="Label for finetune provenance (default grok_build)",
    )
    p_prov.add_argument("--session-log", help="Optional path to Grok CLI log file")

    args = parser.parse_args(argv)
    if args.command == "status":
        return cmd_status(args.slug, args.phase)
    if args.command == "context":
        return cmd_context(args.slug, args.phase)
    if args.command == "validate":
        return cmd_validate(args.slug, args.phase)
    if args.command == "debrief-template":
        return cmd_debrief_template(args.slug, args.phase)
    if args.command == "record-bugs":
        return cmd_record_bugs(args.slug, args.phase, args.file, args.json_inline)
    if args.command == "provenance":
        return cmd_provenance(args.slug, args.phase, args.implementer, args.session_log)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
