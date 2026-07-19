"""
Grok Build CLI adapter — subprocess invoke for one skill/step.

Config (env):
  GROK_BUILD_CMD     Command template with placeholders:
                       {workspace} {prompt_file} {skill} {log_file}
                     Example:
                       grok build --workspace {workspace} --prompt {prompt_file} --skill {skill}
  GROK_BUILD_DRY_RUN Write intended command to log without running (1/true)
  GROK_BUILD_TIMEOUT_S  Subprocess timeout seconds (default 1800)

Logs: projects/<slug>/phases/phase_N/grok_<step>.log

CLI:
  python -m pipeline.engines.grok_build --help
  python -m pipeline.engines.grok_build --slug X --phase 1 --step implement --dry-run
"""

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

from pipeline.engines.base import EngineResult
from pipeline.env_flags import env_bool

# Prompt pack directory (Phase 3)
PROMPTS_DIR = pathlib.Path(__file__).resolve().parent / "prompts"

STEP_PROMPT_MAP: dict[str, str] = {
    "implement": "implement_phase.md",
    "review": "review_phase.md",
    "fix": "fix_from_review.md",
    "debug": "debug_validate_fail.md",
    "deep_review": "deep_review_phase.md",
}

DEFAULT_TIMEOUT_S = 1800


def _timeout_s() -> int:
    raw = os.environ.get("GROK_BUILD_TIMEOUT_S", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_S
    try:
        return max(1, int(float(raw)))
    except ValueError:
        return DEFAULT_TIMEOUT_S


def _dry_run() -> bool:
    return env_bool("GROK_BUILD_DRY_RUN", default=False)


def resolve_prompt_file(step: str, *, explicit: pathlib.Path | None = None) -> pathlib.Path | None:
    """Return pack template path for a logical step, or *explicit* if given."""
    if explicit is not None:
        return pathlib.Path(explicit)
    name = STEP_PROMPT_MAP.get(step)
    if not name:
        return None
    return PROMPTS_DIR / name


def render_prompt_for_phase(
    step: str,
    *,
    project_dir: pathlib.Path,
    workspace: pathlib.Path,
    slug: str,
    phase: int,
    template_path: pathlib.Path | None = None,
) -> tuple[pathlib.Path | None, str]:
    """Render pack template → phases/phase_N/grok_prompt_<step>.md with context.

    Returns (rendered_path_or_None, error_message).
    """
    src = template_path or resolve_prompt_file(step)
    if src is None:
        return None, f"no prompt template mapped for step={step}"
    if not src.is_file():
        return None, f"prompt template missing: {src}"

    try:
        raw = src.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return None, f"cannot read prompt template: {exc}"

    tasks_path = project_dir / "phases" / f"phase_{phase}" / "tasks.md"
    validation_path = project_dir / "phases" / f"phase_{phase}" / "validation_report.md"
    review_path = project_dir / "phases" / f"phase_{phase}" / "review.md"
    master_plan = project_dir / "state" / "master_plan.md"

    # Support both {workspace} style and literal phase_N placeholders in packs
    rendered = raw
    subs = {
        "workspace": str(workspace.resolve()),
        "slug": slug,
        "phase": str(phase),
        "phase_num": str(phase),
        "project_dir": str(project_dir.resolve()),
        "tasks_path": str(tasks_path.resolve()),
        "validation_report_path": str(validation_path.resolve()),
        "review_path": str(review_path.resolve()),
        "master_plan_path": str(master_plan.resolve()),
        "skill": step,
    }
    for key, val in subs.items():
        rendered = rendered.replace("{" + key + "}", val)
    # Common doc placeholders like phase_N
    rendered = rendered.replace("phase_N", f"phase_{phase}")
    rendered = rendered.replace("{N}", str(phase))

    out = project_dir / "phases" / f"phase_{phase}" / f"grok_prompt_{step}.md"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    except OSError as exc:
        return None, f"cannot write rendered prompt: {exc}"
    return out, ""


def phase_log_path(project_dir: pathlib.Path, phase: int, step: str) -> pathlib.Path:
    phase_dir = project_dir / "phases" / f"phase_{phase}"
    phase_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in step)
    return phase_dir / f"grok_{safe}.log"


def build_command(
    *,
    workspace: pathlib.Path,
    prompt_file: pathlib.Path | None,
    skill: str,
    log_file: pathlib.Path,
    cmd_template: str | None = None,
) -> tuple[str, str]:
    """Expand GROK_BUILD_CMD template. Returns (command, error).

    On unknown placeholders, error is set and command should not be executed.
    """
    template = (cmd_template if cmd_template is not None else os.environ.get("GROK_BUILD_CMD", "")).strip()
    if not template:
        # Default placeholder — operators set GROK_BUILD_CMD for real invokes
        template = (
            'echo "GROK_BUILD_CMD unset; skill={skill} workspace={workspace} '
            'prompt={prompt_file}" >> "{log_file}"'
        )
    mapping = {
        "workspace": str(workspace.resolve()),
        "prompt_file": str(prompt_file.resolve()) if prompt_file else "",
        "skill": skill,
        "log_file": str(log_file.resolve()),
    }
    try:
        return template.format(**mapping), ""
    except KeyError as exc:
        return "", f"GROK_BUILD_CMD format error: missing placeholder {exc}"


def run_phase_step(
    slug: str,
    phase: int,
    step: str,
    *,
    project_dir: pathlib.Path | None = None,
    workspace: pathlib.Path | None = None,
    prompt_file: pathlib.Path | None = None,
    extra: dict[str, Any] | None = None,
    dry_run: bool | None = None,
    timeout_s: int | None = None,
    cmd_template: str | None = None,
    subprocess_run=None,
) -> EngineResult:
    """Invoke Grok Build CLI for one step. *subprocess_run* injects for tests."""
    from pipeline.paths import project_dir as resolve_project_dir

    run = subprocess_run or subprocess.run
    proj = pathlib.Path(project_dir) if project_dir else resolve_project_dir(slug)
    ws = pathlib.Path(workspace) if workspace else (proj / "workspace")
    ws.mkdir(parents=True, exist_ok=True)

    prompt_err = ""
    if prompt_file is not None:
        pfile = pathlib.Path(prompt_file)
        if not pfile.is_file():
            prompt_err = f"explicit prompt file missing: {pfile}"
            pfile = None
    else:
        pfile, prompt_err = render_prompt_for_phase(
            step,
            project_dir=proj,
            workspace=ws,
            slug=slug,
            phase=phase,
        )
        # Missing pack is a warning in result, not always hard-fail (dry-run still ok)

    log_path = phase_log_path(proj, phase, step)
    command, cmd_err = build_command(
        workspace=ws,
        prompt_file=pfile,
        skill=step,
        log_file=log_path,
        cmd_template=cmd_template,
    )

    is_dry = _dry_run() if dry_run is None else bool(dry_run)
    timeout = _timeout_s() if timeout_s is None else int(timeout_s)
    ts = datetime.now(timezone.utc).isoformat()
    header = (
        f"# grok_build step={step} slug={slug} phase={phase}\n"
        f"# ts={ts}\n"
        f"# dry_run={is_dry}\n"
        f"# timeout_s={timeout}\n"
        f"# prompt_file={pfile or ''}\n"
        f"# prompt_note={prompt_err or 'ok'}\n"
        f"# command:\n{command or '(none — format error)'}\n"
        f"# ---\n"
    )

    if cmd_err:
        try:
            log_path.write_text(header + f"# error: {cmd_err}\n", encoding="utf-8")
        except OSError:
            pass
        return EngineResult(
            success=False,
            step=step,
            exit_code=2,
            log_path=str(log_path),
            error=cmd_err,
            command=command,
            dry_run=is_dry,
            extra={"prompt_error": prompt_err} if prompt_err else {},
        )

    if is_dry:
        try:
            log_path.write_text(header + "# dry-run: not executed\n", encoding="utf-8")
        except OSError as exc:
            return EngineResult(
                success=False,
                step=step,
                log_path=str(log_path),
                error=f"failed to write dry-run log: {exc}",
                command=command,
                dry_run=True,
            )
        return EngineResult(
            success=True,
            step=step,
            exit_code=0,
            log_path=str(log_path),
            summary="dry-run: command logged, not executed",
            dry_run=True,
            command=command,
        )

    if not os.environ.get("GROK_BUILD_CMD", "").strip() and cmd_template is None:
        # No real CLI configured — treat as hard invoke failure for driver fallback
        try:
            log_path.write_text(
                header + "# error: GROK_BUILD_CMD is not set\n",
                encoding="utf-8",
            )
        except OSError:
            pass
        return EngineResult(
            success=False,
            step=step,
            exit_code=127,
            log_path=str(log_path),
            error="GROK_BUILD_CMD is not set",
            command=command,
            dry_run=False,
        )

    try:
        # Prefer list form when simple; shell=True for templates with redirects
        use_shell = True
        proc = run(
            command,
            shell=use_shell,
            cwd=str(ws),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        body = header + out
        try:
            log_path.write_text(body, encoding="utf-8")
        except OSError:
            pass
        ok = proc.returncode == 0
        return EngineResult(
            success=ok,
            step=step,
            exit_code=int(proc.returncode),
            log_path=str(log_path),
            summary=(out[:500] if out else f"exit={proc.returncode}"),
            command=command,
            error="" if ok else f"exit code {proc.returncode}",
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"timeout after {timeout}s"
        try:
            log_path.write_text(header + f"# {msg}\n{exc}", encoding="utf-8")
        except OSError:
            pass
        return EngineResult(
            success=False,
            step=step,
            exit_code=124,
            log_path=str(log_path),
            error=msg,
            command=command,
        )
    except OSError as exc:
        try:
            log_path.write_text(header + f"# OSError: {exc}\n", encoding="utf-8")
        except OSError:
            pass
        return EngineResult(
            success=False,
            step=step,
            exit_code=1,
            log_path=str(log_path),
            error=str(exc),
            command=command,
        )


class GrokBuildEngine:
    """Engine protocol wrapper around run_phase_step."""

    name = "grok_build"

    def run_phase_step(
        self,
        slug: str,
        phase: int,
        step: str,
        *,
        project_dir: pathlib.Path | None = None,
        workspace: pathlib.Path | None = None,
        prompt_file: pathlib.Path | None = None,
        extra: dict[str, Any] | None = None,
    ) -> EngineResult:
        return run_phase_step(
            slug,
            phase,
            step,
            project_dir=project_dir,
            workspace=workspace,
            prompt_file=prompt_file,
            extra=extra,
        )


def get_grok_build_engine() -> GrokBuildEngine:
    return GrokBuildEngine()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline.engines.grok_build",
        description="Grok Build CLI adapter (dry-run / invoke one skill step).",
    )
    parser.add_argument("--slug", required=False, help="Project slug")
    parser.add_argument("--phase", type=int, default=1, help="Phase number")
    parser.add_argument(
        "--step",
        default="implement",
        choices=sorted(STEP_PROMPT_MAP.keys()) + ["custom"],
        help="Logical skill step",
    )
    parser.add_argument("--workspace", default="", help="Override workspace path")
    parser.add_argument("--project-dir", default="", help="Override project dir")
    parser.add_argument("--prompt-file", default="", help="Override prompt file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log command only (also GROK_BUILD_DRY_RUN=1)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="Timeout seconds (0 = env/default)",
    )
    args = parser.parse_args(argv)

    if not args.slug and not args.project_dir:
        parser.print_help()
        print("\nError: --slug or --project-dir is required to run a step.", file=sys.stderr)
        return 2

    slug = args.slug or pathlib.Path(args.project_dir).name
    result = run_phase_step(
        slug,
        args.phase,
        args.step if args.step != "custom" else "implement",
        project_dir=pathlib.Path(args.project_dir) if args.project_dir else None,
        workspace=pathlib.Path(args.workspace) if args.workspace else None,
        prompt_file=pathlib.Path(args.prompt_file) if args.prompt_file else None,
        dry_run=True if args.dry_run else None,
        timeout_s=args.timeout if args.timeout > 0 else None,
    )
    print(f"success={result.success} dry_run={result.dry_run} log={result.log_path}")
    if result.command:
        print(f"command={result.command}")
    if result.error:
        print(f"error={result.error}", file=sys.stderr)
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
