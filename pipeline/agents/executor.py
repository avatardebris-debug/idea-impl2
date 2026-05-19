"""
pipeline/agents/executor.py
Executor agent — implements coding tasks from the Phase Planner.

Receives: task list (phase_N/tasks.md path + content)
Produces: code files in .pipeline/workspace/, sends result to Validator
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.message_bus import Message


class ExecutorAgent(AgentProcess):
    role = "executor"
    model_tier = "heavy"
    num_ctx = 16384
    max_steps = 30
    temperature = 0.2    # deterministic code writing
    think = False        # no chain-of-thought: just execute the task list

    @property
    def _shared_libs_dir(self) -> pathlib.Path:
        """Global shared library pool, accessible to all projects."""
        d = self._run_dir / ".pipeline" / "shared_libs"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def build_context(self, msg) -> str:  # type: ignore[override]
        """Inject shared library index into every executor task automatically."""
        parts: list[str] = []

        # 1. Reusable tools index (written by manager from ideator output + reviewer)
        tools_file = self._run_dir / ".pipeline" / "state" / "reusable_tools.md"
        if tools_file.exists():
            content = tools_file.read_text(encoding="utf-8").strip()
            if content:
                parts.append(f"## Reusable Tools Index\n{content}")

        # 2. Shared libs directory listing
        shared = self._shared_libs_dir
        libs = sorted(shared.iterdir()) if shared.exists() else []
        lib_dirs = [d for d in libs if d.is_dir()]
        if lib_dirs:
            listing = "\n".join(f"  - {d.name}/  ({len(list(d.rglob('*.py')))} .py files)"
                                 for d in lib_dirs)
            parts.append(
                f"## Shared Libraries Available\n"
                f"Path: {shared}\n{listing}\n"
                f"Read any of these files before reimplementing similar functionality."
            )

        return "\n\n".join(parts)

    def handle(self, msg: Message) -> AgentOutput:
        phase_num = msg.payload.get("phase", 1)
        idea_slug = msg.payload.get("idea_slug", self._current_slug)
        tasks_path = msg.payload.get("tasks_path", f"phases/phase_{phase_num}/tasks.md")
        fix_required = msg.payload.get("fix_required", False)
        review_path = msg.payload.get("review_path", "")

        # Always read these upfront — scoped to current phase only
        raw_tasks = self.read_state_file(tasks_path)
        tasks_content = self._extract_phase_tasks(raw_tasks, phase_num)
        master_plan = self.read_state_file("state/master_plan.md")
        pending_fixes = self.read_state_file("state/pending_fixes.md")
        workspace = self.get_workspace_path()
        tasks_full_path = pathlib.Path(self._project_path(tasks_path))

        self._update_idea_status(f"phase_{phase_num}_executing", phase_num=phase_num)

        # Snapshot workspace BEFORE so we only report newly created files
        before_files = (
            {p for p in workspace.rglob("*") if p.is_file()}
            if workspace.exists() else set()
        )

        if fix_required:
            # Read the persistent fix report (full history of all attempts)
            fix_report_path = msg.payload.get("fix_report_path", "")
            fix_report_content = ""
            if fix_report_path:
                fix_report_content = self.read_state_file(fix_report_path)
            if not fix_report_content:
                # Fallback to inline context (legacy messages)
                fix_report_content = (msg.payload.get("validation_report", "")
                                      or msg.payload.get("fix_instructions", ""))

            review_content = self.read_state_file(review_path) if review_path else ""
            pending_section = ""
            if pending_fixes:
                pending_section = f"## ⚠️ Health Check Findings (fix these FIRST)\n{pending_fixes[:1500]}\n\n"
            task_prompt = (
                f"You are fixing Phase {phase_num} code that failed validation/review.\n\n"
                f"## Workspace\n{workspace}\n\n"
                + pending_section
                + f"## Fix Report (read ALL previous attempts before making changes)\n"
                f"{fix_report_content[:8000]}\n\n"
                + (f"## Review Details\n{review_content[:2000]}\n\n" if review_content else "")
                + "## Instructions\n"
                  "**FOCUS RULE: Fix ONLY what the Fix Report says is broken. "
                  "Do NOT refactor, explore alternatives, or add features.**\n"
                  "1. Read the Fix Report above carefully — especially Previous Attempts.\n"
                  "2. Do NOT repeat a fix that was already tried and failed.\n"
                  f"3. Use `list_tree` then `read_file` on each relevant source file.\n"
                  "4. Fix ONLY the blocking issues described. Don't rewrite working code.\n"
                  "5. If the report mentions file path issues, verify your workspace path first.\n"
                  f"6. Update tasks file at `{tasks_full_path}` marking fixed tasks [x].\n"
                  "7. Say DONE and list every file you changed.\n"
            )
        elif not tasks_content:
            return AgentOutput(
                success=False,
                error=f"No tasks file found at {tasks_full_path}",
            )
        else:
            shared_libs_path = str(self._shared_libs_dir)
            pending_section = ""
            if pending_fixes:
                pending_section = (
                    f"## ⚠️ Health Check Findings (fix these FIRST)\n"
                    f"{pending_fixes[:1500]}\n\n"
                )
            task_prompt = (
                f"You are implementing Phase {phase_num} of a project.\n"
                f"IMPORTANT: Only implement Phase {phase_num} tasks below. "
                f"Do NOT implement tasks from other phases.\n\n"
                + pending_section
                + f"## Master Plan\n{master_plan[:2000]}\n\n"
                f"## Phase {phase_num} Tasks\n{tasks_content}\n\n"
                "## Instructions\n"
                "**EXECUTION RULES — follow strictly:**\n"
                "- Work ONLY through the tasks listed below, in order.\n"
                "- Do NOT explore alternative designs, refactor unrelated code, or add features\n"
                "  not in the task list. Every tool call must serve the current task.\n"
                "- After completing each task, immediately mark it [x] in the tasks file.\n"
                "- Do NOT call list_tree or read_file repeatedly on the same path.\n"
                "  Read a file once, then act on it.\n"
                f"0a. CHECK SHARED LIBS FIRST: run `list_tree` on `{shared_libs_path}` (once).\n"
                "    If any existing library is relevant, read and reuse it — don't reimplement.\n"
                "    The 'Reusable Tools Index' and 'Shared Libraries' sections above list what exists.\n"
                "0b. INSTALL DEPENDENCIES: identify every third-party Python package needed.\n"
                "    Run `pip install <pkg1> <pkg2> ...` via run_shell BEFORE writing any code.\n"
                "    Common mappings: bs4→beautifulsoup4, PIL→Pillow, cv2→opencv-python,\n"
                "    yaml→pyyaml, dotenv→python-dotenv, sklearn→scikit-learn.\n"
                "1. Work through each unchecked task in order. One task at a time.\n"
                f"2. WORKSPACE PATH (use this EXACT absolute path for ALL files):\n"
                f"   {workspace}\n"
                f"   ⚠️  CRITICAL: NEVER create a directory called 'workspace/' — the path above\n"
                f"   IS the workspace. All shell commands must use 'cd {workspace} && ...' first.\n"
                f"   If you use write_file, the path MUST start with: {workspace}/\n"
                f"   WRONG: workspace/email_tool/parser.py\n"
                f"   RIGHT: {workspace}/email_tool/parser.py\n"
                "3. After completing each task, update the tasks file at "
                f"`{tasks_full_path}` marking it [x]. Do this immediately after each task.\n"
                "4. When ALL tasks are complete, say DONE and list every file you created.\n"
            )

        result = self.call_agent(task=task_prompt, verbose=False)

        # --- Phase overlap at 75%: pre-queue planning for next phase ---
        # When 75%+ of tasks are done, start planning the next phase in the
        # background so it's ready when this phase completes (zero planning wait).
        if not fix_required:
            try:
                import re as _re
                _raw_tasks_check = self.read_state_file(tasks_path)
                _scoped = self._extract_phase_tasks(_raw_tasks_check, phase_num)
                _total = len(_re.findall(r'^\s*- \[[ xX]\]', _scoped, _re.MULTILINE))
                _done = len(_re.findall(r'^\s*- \[[xX]\]', _scoped, _re.MULTILINE))
                _idea_state_check = self.read_json_state("state/current_idea.json")
                _total_phases = _idea_state_check.get("total_phases", 1)
                _preplan_sent_key = f"preplan_sent_phase_{phase_num}"
                _already_sent = _idea_state_check.get(_preplan_sent_key, False)

                if (
                    _total > 0
                    and _done / _total >= 0.75
                    and not _already_sent
                    and phase_num < _total_phases
                ):
                    # Check if next phase spec already exists
                    _next_spec = self.read_state_file(f"phases/phase_{phase_num + 1}/spec.md")
                    if not _next_spec:
                        from pipeline.message_bus import Message as _Msg
                        _preplan_msg = _Msg.create(
                            from_agent=self.role,
                            to_agent="phase_planner",
                            type="task",
                            payload={
                                "phase": phase_num + 1,
                                "idea_slug": idea_slug,
                                "preplan_mode": True,
                            },
                            priority=2,   # lower priority — don't interrupt current work
                        )
                        self.bus.send(_preplan_msg)
                        # Mark that we sent the preplan to avoid duplicates
                        _idea_state_check[_preplan_sent_key] = True
                        self.write_json_state("state/current_idea.json", _idea_state_check)
                        import logging as _log
                        _log.getLogger(__name__).info(
                            "[executor] Pre-queued phase %d planning at %.0f%% completion",
                            phase_num + 1, (_done/_total*100)
                        )
            except Exception:
                pass  # Non-critical — never break execution over preplan

        # --- Strategy 4: Invalidate KV-cache after execution ---
        # The executor's system prompt is different from the validator's.
        # Drop the cached prefix so the validator gets a clean encoding,
        # and the next executor retry starts fresh (not from a bad code state).
        try:
            from pipeline.kv_cache import invalidate_on_write
            invalidate_on_write(self._current_slug)
        except Exception:
            pass  # non-critical

        # --- Post-run stray file rescue ---
        # The LLM frequently writes files to wrong locations. We rescue them
        # into the correct workspace BEFORE reporting results to the validator.
        import shutil as _shutil
        _rescued_total = 0

        def _rescue_dir(src_dir: pathlib.Path, dest_base: pathlib.Path, label: str) -> int:
            """Move files from src_dir into dest_base, preserving relative paths."""
            if not src_dir.exists() or not src_dir.is_dir():
                return 0
            moved = 0
            for f in list(src_dir.rglob("*")):
                if f.is_file() and not f.name.startswith("."):
                    rel = f.relative_to(src_dir)
                    dst = dest_base / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if not dst.exists():
                        _shutil.copy2(str(f), str(dst))
                        moved += 1
                    elif f.stat().st_mtime > dst.stat().st_mtime:
                        _shutil.copy2(str(f), str(dst))
                        moved += 1
            if moved:
                try:
                    _shutil.rmtree(str(src_dir))
                except OSError:
                    pass
                import logging as _log
                _log.getLogger(__name__).warning(
                    "[executor] Rescued %d file(s) from %s", moved, label
                )
            return moved

        # Pattern 1: workspace/workspace/ double-nesting
        _rescued_total += _rescue_dir(workspace / "workspace", workspace, "workspace/workspace/")

        # Pattern 2: src/ and tests/ at project root (very common LLM mistake)
        _project_root = self._run_dir
        for _stray_name in ("src", "tests", "test"):
            _stray_dir = _project_root / _stray_name
            if _stray_dir.exists() and _stray_dir.is_dir():
                # Only rescue if files appeared DURING this run (check mtime)
                _recent = any(
                    f.stat().st_mtime > (result.started_at if hasattr(result, 'started_at') else 0)
                    for f in _stray_dir.rglob("*") if f.is_file()
                ) if hasattr(result, 'started_at') else True
                if _recent:
                    _rescued_total += _rescue_dir(_stray_dir, workspace / _stray_name, f"root {_stray_name}/")

        # Pattern 3: slug-named directory at project root
        _slug_at_root = _project_root / idea_slug
        if _slug_at_root.exists() and _slug_at_root.is_dir():
            _rescued_total += _rescue_dir(_slug_at_root, workspace, f"root {idea_slug}/")

        # Pattern 4: loose .py files at project root (not part of pipeline infra)
        _infra_files = {
            "agent.py", "extract.py", "fix_indent.py", "fix_missing_plans.py",
            "fix_stuck_tasks.py", "governance.py", "setup.py",
        }
        for _f in _project_root.glob("*.py"):
            if _f.name not in _infra_files and _f.name not in before_files:
                _dst = workspace / _f.name
                if not _dst.exists():
                    _dst.parent.mkdir(parents=True, exist_ok=True)
                    _shutil.copy2(str(_f), str(_dst))
                    _rescued_total += 1
                    import logging as _log
                    _log.getLogger(__name__).warning(
                        "[executor] Rescued loose file %s from project root", _f.name
                    )

        # Pattern 5: /workspace/workspace/<slug>/ (cloud double-nesting)
        _cloud_stray = pathlib.Path("/workspace/workspace") / idea_slug
        if _cloud_stray.exists() and _cloud_stray.is_dir():
            _rescued_total += _rescue_dir(_cloud_stray, workspace, f"/workspace/workspace/{idea_slug}/")

        # Only report files created/changed during THIS call
        after_files = (
            {p for p in workspace.rglob("*") if p.is_file()}
            if workspace.exists() else set()
        )
        new_files = after_files - before_files
        files_to_report = new_files if new_files else after_files
        files_written = [
            str(p.relative_to(workspace))
            for p in files_to_report
            if not p.name.startswith(".")
        ]

        # --- Auto-mark tasks done based on files written ---
        # The executor often forgets to update checkboxes after a long run.
        # Deterministically mark any unchecked task as [x] if the workspace
        # has files that suggest it was completed (any .py files exist at all).
        # This is conservative: only marks if workspace has substantive output.
        try:
            if tasks_full_path.exists() and len(after_files) >= 3:
                raw = tasks_full_path.read_text(encoding="utf-8")
                # Find unchecked tasks in the current phase section only
                scoped = self._extract_phase_tasks(raw, phase_num)
                unchecked = re.findall(r'^\s*- \[ \].*', scoped, re.MULTILINE)
                # Trigger if: new files written (fresh run) OR workspace has >= 3 files
                # (fix run: modifies existing files, new_files may be empty)
                has_output = bool(new_files) or len(after_files) >= 3
                if unchecked and has_output:
                    # Mark all unchecked phase tasks as done
                    # Replace only within the phase section to avoid touching other phases
                    import re as _re
                    phase_pattern = rf'^(#{1,4})\s+(?:.*?)?Phase\s+{phase_num}\b.*$'
                    m = _re.search(phase_pattern, raw, _re.MULTILINE | _re.IGNORECASE)
                    if m:
                        next_phase = _re.search(
                            rf'^#{1,4}\s+(?:.*?)?Phase\s+{phase_num + 1}\b',
                            raw[m.end():], _re.MULTILINE | _re.IGNORECASE
                        )
                        sec_end = m.end() + next_phase.start() if next_phase else len(raw)
                        section = raw[m.start():sec_end]
                        fixed = _re.sub(r'^- \[ \]', '- [x]', section, flags=_re.MULTILINE)
                        new_raw = raw[:m.start()] + fixed + raw[sec_end:]
                        tasks_full_path.write_text(new_raw, encoding="utf-8")
                        marked = len(_re.findall(r'^- \[ \]', section, _re.MULTILINE))
                        if marked:
                            import logging as _log
                            _log.getLogger(__name__).info(
                                "[executor] Auto-marked %d task(s) as done (files written: %d)",
                                marked, len(new_files)
                            )
        except Exception:
            pass  # Non-critical — validator will catch real failures

        # --- Sync task counts back to current_idea.json immediately ---
        # The auto-mark above wrote [x] to disk but current_idea.json still has
        # tasks_done=0 from the start-of-execution snapshot.  Update it now so
        # the runner's next status tick shows the real count (e.g. 6/6 not 0/6)
        # and the stall-kill guard sees fresh data.
        self._update_idea_status(f"phase_{phase_num}_executing", phase_num=phase_num)

        # Route: reviewer on first execution + even retries, validator on odd retries
        # This gives structural review coverage every other pass:
        #   1st execution → reviewer → validator
        #   retry 1 → validator (fast, no review overhead)
        #   retry 2 → reviewer → validator
        #   retry 3 → validator (fast)
        retry_count = msg.payload.get("retry_count", 0)
        use_reviewer = not fix_required or (retry_count % 2 == 0)
        next_agent = "reviewer" if use_reviewer else "validator"

        out_msg = Message.create(
            from_agent=self.role,
            to_agent=next_agent,
            type="task",
            payload={
                "phase": phase_num,
                "tasks_path": tasks_path,
                "workspace_path": str(workspace),
                "files_written": files_written,
                "validation_report_path": f"phases/phase_{phase_num}/validation_report.md",
                "idea_slug": idea_slug,
                "retry_count": retry_count,
            },
        )

        return AgentOutput(
            success=result.completed,
            answer=result.answer,
            outgoing=[out_msg],
            files_written=files_written,
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )


def main():
    """Entry point for subprocess execution."""
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default=__import__("os").environ.get("PIPELINE_MODEL", "qwen3.5:35b"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [executor] %(message)s")

    agent = ExecutorAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
