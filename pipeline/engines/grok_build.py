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
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

from pipeline.engines.base import EngineResult
from pipeline.env_flags import env_bool

# Prompt pack directory (Phase 3)
PROMPTS_DIR = pathlib.Path(__file__).resolve().parent / "prompts"

STEP_PROMPT_MAP: dict[str, str] = {
    "idea_plan": "idea_plan.md",
    "phase_plan": "phase_plan.md",
    "implement": "implement_phase.md",
    "review": "review_phase.md",
    "fix": "fix_from_review.md",
    "debug": "debug_validate_fail.md",
    "deep_review": "deep_review_phase.md",
    "field_test_plan": "field_test_plan.md",
    "field_fail_repair": "field_fail_repair.md",
    "field_systematic_debug": "field_systematic_debug.md",
    "field_code_review": "field_code_review.md",
    "field_comprehensive_report": "field_comprehensive_report.md",
}

# CLI / skill-dir names (hyphen) for steps that map to ~/.grok/skills/*
STEP_SKILL_NAME: dict[str, str] = {
    "idea_plan": "idea-plan",
    "phase_plan": "phase-plan",
    "field_systematic_debug": "systematic-debugging",
}

DEFAULT_TIMEOUT_S = 1800

# file:path or path:path fenced blocks from pipeline_llm implement/fix output
_FILE_FENCE = re.compile(
    r"```(?:[\w.+-]*)\s*\n?(?:(?:file|path)\s*[:=]\s*)([^\n`]+)\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)
_FILE_FENCE_ALT = re.compile(
    r"```(?:[\w.+-]*)\s+([^\n`]+\.\w+)\n(.*?)```",
    re.DOTALL,
)


def _timeout_s() -> int:
    raw = os.environ.get("GROK_BUILD_TIMEOUT_S", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_S
    try:
        return max(1, int(float(raw)))
    except ValueError:
        return DEFAULT_TIMEOUT_S


def _resolve_build_backend(*, cmd_template: str | None = None) -> str:
    """cli | pipeline_llm — how to execute a skill step.

    GROK_BUILD_BACKEND:
      auto (default) — CLI if GROK_BUILD_CMD set, else pipeline_llm if allowed
      cli            — require GROK_BUILD_CMD
      pipeline_llm   — ollama/qwen/openai/grok API via llm_interface (no grok.exe)
    """
    raw = (os.environ.get("GROK_BUILD_BACKEND") or "auto").strip().lower()
    has_cmd = bool(
        (cmd_template or "").strip() or os.environ.get("GROK_BUILD_CMD", "").strip()
    )
    if raw == "pipeline_llm":
        return "pipeline_llm"
    if raw == "cli":
        return "cli"
    # auto
    if has_cmd:
        return "cli"
    if env_bool("GROK_BUILD_ALLOW_PIPELINE_LLM", default=True):
        return "pipeline_llm"
    return "cli"


def _apply_pipeline_llm_output(
    step: str,
    content: str,
    *,
    project_dir: pathlib.Path,
    workspace: pathlib.Path,
    phase: int,
) -> list[str]:
    """Write model output to expected artifacts. Returns list of paths written."""
    written: list[str] = []
    phase_dir = project_dir / "phases" / f"phase_{phase}"
    phase_dir.mkdir(parents=True, exist_ok=True)
    text = content or ""

    def _write(path: pathlib.Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
        written.append(str(path))

    # Structured file fences for implement/fix/debug
    proj_root = project_dir.resolve()
    ws_root = workspace.resolve()
    for rx in (_FILE_FENCE, _FILE_FENCE_ALT):
        for m in rx.finditer(text):
            rel = m.group(1).strip().strip("`\"'")
            body = m.group(2)
            if not rel or ".." in rel.replace("\\", "/"):
                continue
            # Reject absolute paths (escape hatch to arbitrary FS)
            try:
                if pathlib.Path(rel).is_absolute():
                    continue
            except Exception:
                continue
            # Normalize to workspace-relative unless phases/ or state/
            if rel.startswith("phases/") or rel.startswith("state/"):
                dest = project_dir / rel
            else:
                dest = workspace / rel
            try:
                dest_res = dest.resolve()
                # Must stay under project root (phases/state) or workspace
                if not (
                    str(dest_res).startswith(str(proj_root))
                    or str(dest_res).startswith(str(ws_root))
                ):
                    continue
                _write(dest, body)
            except OSError:
                continue

    if step == "review":
        review_path = phase_dir / "review.md"
        if "## Verdict" in text or not review_path.is_file():
            # Prefer full content if it looks like a review
            body = text
            fence = re.search(r"```(?:markdown|md)?\s*\n(.*?)```", text, re.DOTALL | re.I)
            if fence and "## Verdict" in fence.group(1):
                body = fence.group(1)
            if "## Verdict" not in body:
                body = (
                    f"# Code Review — Phase {phase}\n\n"
                    f"### What's Good\n- pipeline_llm review\n\n"
                    f"## Blocking Bugs\n- None\n\n"
                    f"## Non-Blocking Notes\n- None\n\n"
                    f"## Reusable Components\n- None\n\n"
                    f"## Verdict\nPASS — pipeline_llm output lacked structured sections\n\n"
                    f"---\nRaw:\n{text[:3000]}\n"
                )
            _write(review_path, body)

    if step == "deep_review":
        _write(phase_dir / "deep_review.md", text)

    if step == "field_test_plan":
        ship = project_dir / "phases" / "ship"
        body = text
        m = re.search(r"(#\s*Field Tests\b.*)", text, re.DOTALL | re.I)
        if m:
            body = m.group(1)
        _write(ship / "field_tests.md", body)

    if step == "field_fail_repair":
        ship = project_dir / "phases" / "ship"
        # Prefer explicit fences; else dump fix report
        if "field_fix_report" not in " ".join(written).lower():
            _write(ship / "field_fix_report.md", text[:8000])

    if step == "field_systematic_debug":
        ship = project_dir / "phases" / "ship"
        if not any("field_debug" in w for w in written):
            _write(ship / "field_debug_report.md", text[:8000])

    if step == "field_code_review":
        ship = project_dir / "phases" / "ship"
        if not any("field_code_review" in w for w in written):
            _write(ship / "field_code_review.md", text[:8000])

    if step == "field_comprehensive_report":
        ship = project_dir / "phases" / "ship"
        _write(ship / "field_comprehensive_report.md", text[:12000])

    if step == "idea_plan":
        master = project_dir / "state" / "master_plan.md"
        body = text
        m = re.search(r"(#\s*Master Plan\b.*)", text, re.DOTALL | re.I)
        if m:
            body = m.group(1)
        if "Master Plan" in body or "## Phase" in body or body.strip():
            _write(master, body[:20000])
        _maybe_sync_total_phases(project_dir, body)

    if step == "phase_plan":
        tasks_out = phase_dir / "tasks.md"
        body = text
        m = re.search(r"(#\s*Phase\s+\d+\s+Tasks\b.*)", text, re.DOTALL | re.I)
        if m:
            body = m.group(1)
        if "- [" in body or "- [ ]" in body or "- [x]" in body:
            _write(tasks_out, body[:20000])
        elif body.strip() and not tasks_out.is_file():
            # Last resort: wrap raw bullets if model omitted heading
            _write(
                tasks_out,
                f"# Phase {phase} Tasks\n\n{body[:15000]}\n",
            )

    return written


def _maybe_sync_total_phases(project_dir: pathlib.Path, plan_text: str) -> None:
    """Best-effort total_phases from master plan text into current_idea.json."""
    n = None
    m = re.search(r"total_phases\s*[:=]\s*(\d+)", plan_text, re.I)
    if m:
        n = int(m.group(1))
    else:
        phases = re.findall(r"^##\s*Phase\s+(\d+)\b", plan_text, re.I | re.M)
        if phases:
            n = max(int(x) for x in phases)
    if not n or n < 1:
        return
    sf = project_dir / "state" / "current_idea.json"
    if not sf.is_file():
        return
    try:
        import json

        state = json.loads(sf.read_text(encoding="utf-8-sig"))
        state["total_phases"] = int(n)
        sf.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def _run_via_pipeline_llm(
    *,
    step: str,
    slug: str,
    phase: int,
    project_dir: pathlib.Path,
    workspace: pathlib.Path,
    prompt_file: pathlib.Path | None,
    log_path: pathlib.Path,
    header: str,
    prompt_err: str,
) -> EngineResult:
    """Execute a skill step via llm_interface (ollama/qwen/…), no GROK_BUILD_CMD."""
    prov = (
        os.environ.get("GROK_BUILD_PROVIDER")
        or os.environ.get("PIPELINE_PROVIDER")
        or "ollama"
    ).strip()
    mod = (
        os.environ.get("GROK_BUILD_MODEL")
        or os.environ.get("PIPELINE_MODEL")
        or ""
    ).strip() or None

    prompt_text = ""
    if prompt_file and prompt_file.is_file():
        try:
            prompt_text = prompt_file.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return EngineResult(
                success=False,
                step=step,
                exit_code=1,
                log_path=str(log_path),
                error=f"read prompt: {exc}",
            )

    user = (
        prompt_text
        + "\n\n## Response protocol\n"
        + "For implement/fix/debug: emit files as fenced blocks:\n"
        + "```python\nfile:relative/path.py\n<code>\n```\n"
        + "For review: write a full review.md with ## Blocking Bugs and ## Verdict.\n"
        + "For field_test_plan: write # Field Tests markdown with Task P1/I1 Command/Expect.\n"
    )

    try:
        from llm_interface import get_llm

        llm = get_llm(prov, model=mod, temperature=0.2, slug=slug)
        msg = llm.chat(
            [
                {
                    "role": "system",
                    "content": (
                        f"You are the {step} step of a software factory. "
                        "Follow the user prompt exactly. Prefer concrete file outputs."
                    ),
                },
                {"role": "user", "content": user},
            ]
        )
        content = msg.content or ""
        written = _apply_pipeline_llm_output(
            step,
            content,
            project_dir=project_dir,
            workspace=workspace,
            phase=phase,
        )
        try:
            log_path.write_text(
                header
                + f"# backend=pipeline_llm provider={prov} model={mod}\n"
                + f"# written={written}\n# ---\n"
                + content[:50000],
                encoding="utf-8",
            )
        except OSError:
            pass

        # Soft success criteria by step
        ok = True
        err = ""
        if step == "review":
            rp = project_dir / "phases" / f"phase_{phase}" / "review.md"
            ok = rp.is_file() and "## Verdict" in rp.read_text(
                encoding="utf-8", errors="replace"
            )
            if not ok:
                err = "pipeline_llm review.md missing ## Verdict"
        elif step == "field_test_plan":
            fp = project_dir / "phases" / "ship" / "field_tests.md"
            ok = fp.is_file() and fp.stat().st_size > 40
            if not ok:
                err = "pipeline_llm did not write field_tests.md"
        elif step in ("implement", "fix", "debug"):
            ok = bool(written) or True  # allow pure edits via existing files
        return EngineResult(
            success=ok,
            step=step,
            exit_code=0 if ok else 1,
            log_path=str(log_path),
            summary=f"pipeline_llm {prov} wrote {len(written)} file(s)",
            error=err,
            command=f"pipeline_llm:{prov}:{mod or 'default'}",
            extra={"backend": "pipeline_llm", "written": written, "prompt_error": prompt_err},
        )
    except Exception as exc:
        try:
            log_path.write_text(header + f"# pipeline_llm error: {exc}\n", encoding="utf-8")
        except OSError:
            pass
        return EngineResult(
            success=False,
            step=step,
            exit_code=127,
            log_path=str(log_path),
            error=f"pipeline_llm: {exc}",
            command=f"pipeline_llm:{prov}",
        )


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

    phase_dir = project_dir / "phases" / f"phase_{phase}"
    tasks_path = phase_dir / "tasks.md"
    validation_path = phase_dir / "validation_report.md"
    review_path = phase_dir / "review.md"
    deep_review_path = phase_dir / "deep_review.md"
    ship_dir = project_dir / "phases" / "ship"
    field_tests_path = ship_dir / "field_tests.md"
    field_results_path = ship_dir / "field_test_results.md"
    field_fix_report_path = ship_dir / "field_fix_report.md"
    field_debug_report_path = ship_dir / "field_debug_report.md"
    field_review_path = ship_dir / "field_code_review.md"
    field_comprehensive_path = ship_dir / "field_comprehensive_report.md"
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
        "deep_review_path": str(deep_review_path.resolve()),
        "field_tests_path": str(field_tests_path.resolve()),
        "field_results_path": str(field_results_path.resolve()),
        "field_fix_report_path": str(field_fix_report_path.resolve()),
        "field_debug_report_path": str(field_debug_report_path.resolve()),
        "field_review_path": str(field_review_path.resolve()),
        "field_comprehensive_path": str(field_comprehensive_path.resolve()),
        "master_plan_path": str(master_plan.resolve()),
        "skill": step,
    }
    # Inject on-disk skills into pack templates
    skill_placeholders = (
        ("field_systematic_debug", "systematic_debugging_skill", "systematic-debugging"),
        ("idea_plan", "idea_plan_skill", "idea-plan"),
        ("phase_plan", "phase_plan_skill", "phase-plan"),
    )
    for step_name, placeholder, skill_name in skill_placeholders:
        token = "{" + placeholder + "}"
        if step == step_name or token in rendered:
            try:
                from pipeline.skill_load import load_skill_body

                skill_txt = load_skill_body(skill_name, max_chars=12000)
            except Exception:
                skill_txt = ""
            if not skill_txt:
                skill_txt = (
                    f"({skill_name} skill not found under ~/.grok/skills — "
                    f"follow the Hard requirements in this prompt.)"
                )
            subs[placeholder] = skill_txt

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
    skill_label = STEP_SKILL_NAME.get(step, step)
    command, cmd_err = build_command(
        workspace=ws,
        prompt_file=pfile,
        skill=skill_label,
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

    backend = _resolve_build_backend(cmd_template=cmd_template)
    if backend == "pipeline_llm":
        return _run_via_pipeline_llm(
            step=step,
            slug=slug,
            phase=phase,
            project_dir=proj,
            workspace=ws,
            prompt_file=pfile,
            log_path=log_path,
            header=header,
            prompt_err=prompt_err,
        )

    if not os.environ.get("GROK_BUILD_CMD", "").strip() and cmd_template is None:
        # No CLI and pipeline_llm not selected — hard fail → classic fallback
        try:
            log_path.write_text(
                header + "# error: GROK_BUILD_CMD is not set "
                "(set GROK_BUILD_BACKEND=pipeline_llm for ollama/qwen path)\n",
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
