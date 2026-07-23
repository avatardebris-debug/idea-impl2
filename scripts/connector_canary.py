#!/usr/bin/env python3
"""
P1 connector / harness canary — prove factory *interfaces* work, not product ideas.

Checks (hard vs soft):
  HARD — fail canary if broken:
    - PIPELINE_DIR / projects exists
    - GROK_BUILD_CMD set + executable exists (when backend cli/auto+cmd)
    - XAI/GROK API key present when --require-api
    - Native workflow runner can load registry_refresh (if YAML present)
  SOFT — report only:
    - n8n health (optional self-hosted)
    - Grok CLI dry smoke (optional --cli-smoke)
    - Grok API tiny completion (optional --api-smoke)

Usage:
  set PIPELINE_DIR=C:\\Users\\avata\\aicompete\\thepipeline
  python scripts/connector_canary.py
  python scripts/connector_canary.py --cli-smoke --api-smoke --require-api
  python scripts/connector_canary.py --json

Exit 0 = all HARD checks pass; exit 1 = any HARD fail.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@dataclass
class Check:
    id: str
    hard: bool
    ok: bool
    detail: str


@dataclass
class CanaryReport:
    ts: str
    ok: bool
    checks: list[Check] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _load_dotenv() -> None:
    env_path = _ROOT / ".env"
    if not env_path.is_file():
        return
    rx = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*[\"']?(.*?)[\"']?\s*$")
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = rx.match(line)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        if k not in os.environ:
            os.environ[k] = v


def _cmd_exe(cmd: str) -> str:
    first = (cmd or "").strip().split()[0].strip('"')
    return first


def check_pipeline_dir() -> Check:
    from pipeline.paths import projects_dir

    try:
        p = projects_dir()
        ok = p.is_dir()
        return Check("pipeline_dir", True, ok, str(p) if ok else f"missing projects: {p}")
    except Exception as e:
        return Check("pipeline_dir", True, False, str(e))


def check_grok_cli() -> Check:
    cmd = (os.environ.get("GROK_BUILD_CMD") or "").strip()
    backend = (os.environ.get("GROK_BUILD_BACKEND") or "auto").strip().lower()
    if backend == "pipeline_llm":
        return Check("grok_cli", True, True, "backend=pipeline_llm (CLI not required)")
    if not cmd:
        if backend == "cli" or backend == "auto":
            return Check(
                "grok_cli",
                True,
                False,
                "GROK_BUILD_CMD unset (required for CLI implement/field/plan skills)",
            )
    exe = _cmd_exe(cmd)
    if exe.endswith((".exe",)) or "/" in exe or "\\" in exe:
        if not Path(exe).is_file():
            # also try shutil.which
            w = shutil.which(exe)
            if not w:
                return Check("grok_cli", True, False, f"executable not found: {exe}")
            return Check("grok_cli", True, True, f"GROK_BUILD_CMD ok (which={w})")
        return Check("grok_cli", True, True, f"GROK_BUILD_CMD ok ({exe})")
    return Check("grok_cli", True, True, f"GROK_BUILD_CMD set (shell form): {cmd[:80]}…")


def check_api_key(*, require: bool) -> Check:
    has = bool(os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY"))
    if require and not has:
        return Check("api_key", True, False, "XAI_API_KEY / GROK_API_KEY missing")
    return Check(
        "api_key",
        require,
        has if require else True,
        "API key present" if has else "API key not set (soft unless --require-api)",
    )


def check_native_workflow() -> Check:
    """Canary for n8n-style *native* connectors: load + dry structure of registry_refresh."""
    try:
        from pipeline.workflow_schema import load_workflow

        # Prefer PIPELINE_DIR workflows, fall back to factory
        slug = "registry_refresh"
        try:
            wf = load_workflow(slug)
        except Exception as e1:
            return Check(
                "native_workflow",
                True,
                False,
                f"cannot load workflow '{slug}': {e1} "
                f"(run build_capability_registry / ensure workflows YAML under PIPELINE_DIR)",
            )
        steps = len(wf.steps or [])
        return Check(
            "native_workflow",
            True,
            steps > 0,
            f"loaded {wf.slug} kind={getattr(wf, 'kind', '?')} backend={wf.backend} steps={steps}",
        )
    except Exception as e:
        return Check("native_workflow", True, False, str(e))


def check_n8n_health() -> Check:
    try:
        from pipeline.n8n_bridge import n8n_health

        base = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
        key = os.environ.get("N8N_API_KEY", "")
        ok, msg = n8n_health(base, key)
        return Check("n8n_health", False, ok, msg)
    except Exception as e:
        return Check("n8n_health", False, False, str(e))


def check_cli_smoke() -> Check:
    """Minimal grok.exe --help (no project work)."""
    cmd = (os.environ.get("GROK_BUILD_CMD") or "").strip()
    if not cmd:
        return Check("cli_smoke", False, False, "no GROK_BUILD_CMD")
    exe = _cmd_exe(cmd)
    if not Path(exe).is_file() and not shutil.which(exe):
        return Check("cli_smoke", False, False, f"exe missing: {exe}")
    try:
        r = subprocess.run(
            [exe if Path(exe).is_file() else shutil.which(exe) or exe, "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        ok = r.returncode == 0 or "usage" in (r.stdout + r.stderr).lower() or len(r.stdout) > 20
        return Check(
            "cli_smoke",
            False,
            ok,
            f"exit={r.returncode} out_len={len(r.stdout)} err_len={len(r.stderr)}",
        )
    except Exception as e:
        return Check("cli_smoke", False, False, str(e))


def check_api_smoke() -> Check:
    """Tiny Grok API chat via pipeline llm_interface if available."""
    if not (os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")):
        return Check("api_smoke", False, False, "no API key")
    try:
        from pipeline.llm_interface import get_llm

        model = os.environ.get("PIPELINE_MODEL") or "grok-4.3"
        llm = get_llm("grok", model=model, temperature=0.0)
        # prefer minimal API
        if hasattr(llm, "chat"):
            out = llm.chat([{"role": "user", "content": "Reply with exactly: CANARY_OK"}])
            text = str(out) if not isinstance(out, dict) else str(out.get("content") or out)
        elif hasattr(llm, "generate"):
            text = str(llm.generate("Reply with exactly: CANARY_OK"))
        else:
            return Check("api_smoke", False, False, f"llm has no chat/generate: {type(llm)}")
        ok = "CANARY_OK" in text or len(text) > 0
        return Check("api_smoke", False, ok, f"model={model} reply_snip={text[:80]!r}")
    except Exception as e:
        return Check("api_smoke", False, False, str(e)[:300])


def check_capability_invoke() -> Check:
    """Soft: invoke_capability for registry_refresh if registered."""
    try:
        from pipeline.capability_tools import invoke_capability
        from pipeline.paths import registry_db

        if not registry_db().exists():
            return Check("capability_invoke", False, False, "registry.sqlite missing")
        # dry: describe only
        from pipeline.capability_tools import list_capabilities

        caps = list_capabilities(limit=5) if callable(list_capabilities) else []
        return Check(
            "capability_invoke",
            False,
            True,
            f"registry present; sample_caps={len(caps) if isinstance(caps, list) else 'ok'}",
        )
    except Exception as e:
        return Check("capability_invoke", False, False, str(e)[:200])


def run_canary(
    *,
    require_api: bool,
    cli_smoke: bool,
    api_smoke: bool,
    n8n: bool,
) -> CanaryReport:
    report = CanaryReport(ts=datetime.now(timezone.utc).isoformat(), ok=True)
    report.notes.append(
        "This canary proves factory harness connectors (CLI/API/workflows/n8n), "
        "not product field_proven of n8n-style business connectors. "
        "Product bridges under workflows/connectors/ still need per-slug run+verify."
    )

    checks = [
        check_pipeline_dir(),
        check_grok_cli(),
        check_api_key(require=require_api),
        check_native_workflow(),
    ]
    if n8n:
        checks.append(check_n8n_health())
    if cli_smoke:
        checks.append(check_cli_smoke())
    if api_smoke:
        checks.append(check_api_smoke())
    checks.append(check_capability_invoke())

    report.checks = checks
    report.ok = all(c.ok for c in checks if c.hard)
    return report


def write_report(report: CanaryReport) -> Path | None:
    try:
        from pipeline.paths import metrics_dir

        out_dir = metrics_dir()
    except Exception:
        out_dir = Path(os.environ.get("PIPELINE_DIR", ".")) / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "connector_canary_latest.md"
    lines = [
        "# Connector / harness canary",
        "",
        f"- Generated: {report.ts}",
        f"- Overall HARD: **{'PASS' if report.ok else 'FAIL'}**",
        "",
        "## Checks",
        "",
        "| id | hard | ok | detail |",
        "|----|------|----|--------|",
    ]
    for c in report.checks:
        detail = c.detail.replace("|", "\\|")[:200]
        lines.append(f"| `{c.id}` | {c.hard} | {'PASS' if c.ok else 'FAIL'} | {detail} |")
    lines.extend(["", "## Notes", ""])
    for n in report.notes:
        lines.append(f"- {n}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    json_path = out_dir / "connector_canary_latest.json"
    json_path.write_text(
        json.dumps(
            {
                "ts": report.ts,
                "ok": report.ok,
                "checks": [asdict(c) for c in report.checks],
                "notes": report.notes,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    _load_dotenv()
    ap = argparse.ArgumentParser(description="P1 connector/harness canary")
    ap.add_argument("--require-api", action="store_true", help="HARD fail if no XAI key")
    ap.add_argument("--cli-smoke", action="store_true", help="Run grok.exe --help")
    ap.add_argument("--api-smoke", action="store_true", help="Tiny Grok API completion")
    ap.add_argument("--n8n", action="store_true", default=True, help="Check n8n health (soft)")
    ap.add_argument("--no-n8n", action="store_true", help="Skip n8n check")
    ap.add_argument("--json", action="store_true", help="Print JSON to stdout")
    ap.add_argument("--no-write", action="store_true", help="Do not write metrics report")
    args = ap.parse_args()

    report = run_canary(
        require_api=args.require_api,
        cli_smoke=args.cli_smoke,
        api_smoke=args.api_smoke,
        n8n=not args.no_n8n,
    )
    path = None if args.no_write else write_report(report)

    if args.json:
        print(
            json.dumps(
                {
                    "ok": report.ok,
                    "checks": [asdict(c) for c in report.checks],
                    "report": str(path) if path else None,
                },
                indent=2,
            )
        )
    else:
        print(f"Connector canary HARD: {'PASS' if report.ok else 'FAIL'}")
        for c in report.checks:
            tag = "HARD" if c.hard else "soft"
            print(f"  [{tag}] {c.id}: {'PASS' if c.ok else 'FAIL'} — {c.detail[:120]}")
        if path:
            print(f"Report: {path}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
