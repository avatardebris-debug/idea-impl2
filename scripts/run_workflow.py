#!/usr/bin/env python3
"""Run a pipeline workflow or connector from .pipeline/workflows/*.yaml."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.n8n_bridge import export_to_n8n_json, n8n_health  # noqa: E402
from pipeline.pipeline_mode import legacy_mode, set_legacy_mode  # noqa: E402
from pipeline.workflow_runner import run_workflow  # noqa: E402
from pipeline.workflow_schema import load_workflow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run workflow/connector YAML (native, hybrid, or n8n backend)"
    )
    parser.add_argument("slug", nargs="?", help="Workflow slug (see build_capability_registry --list)")
    parser.add_argument("--legacy", action="store_true", help="No-op message (workflows require registry)")
    parser.add_argument("--force", action="store_true", help="Skip requires: checks and allow draft capabilities")
    parser.add_argument(
        "--backend",
        choices=("native", "n8n", "hybrid"),
        default="",
        help="Override workflow YAML backend",
    )
    parser.add_argument("--step", default="", help="Run only one step id (for n8n Execute Command nodes)")
    parser.add_argument("--args", default="", help="Opaque args passed as input.args")
    parser.add_argument("--json-input", default="", help='JSON object for workflow input, e.g. {"key":"v"}')
    parser.add_argument("--export-n8n", metavar="FILE", help="Export workflow to n8n-importable JSON and exit")
    parser.add_argument("--n8n-health", action="store_true", help="Check N8N_BASE_URL / API and exit")
    args = parser.parse_args()

    if args.legacy:
        set_legacy_mode(True)
        print("Workflows disabled in legacy mode.")
        return

    set_legacy_mode(False)

    if args.n8n_health:
        import os

        base = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
        key = os.environ.get("N8N_API_KEY", "")
        ok, msg = n8n_health(base, key)
        print(("OK: " if ok else "FAIL: ") + msg)
        sys.exit(0 if ok else 1)

    if not args.slug:
        parser.error("slug is required unless using --n8n-health")

    if args.export_n8n:
        wf = load_workflow(args.slug)
        out = export_to_n8n_json(wf)
        path = Path(args.export_n8n)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"Exported n8n workflow JSON -> {path}")
        print(f"  Import in n8n UI; webhook path suggestion: /webhook/{wf.slug.replace('_', '-')}")
        return

    json_input = None
    if args.json_input:
        try:
            json_input = json.loads(args.json_input)
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid --json-input: {e}")
            sys.exit(1)

    result = run_workflow(
        args.slug,
        args=args.args,
        json_input=json_input,
        step_id=args.step,
        force=args.force,
        backend_override=args.backend,
    )
    print(result)
    sys.exit(0 if result.startswith("OK") else 1)


if __name__ == "__main__":
    main()
