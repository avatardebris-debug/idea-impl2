"""
pipeline/agents/validator.py
Validator/Tester agent — runs tests, lint, and acceptance checks.

Receives: workspace path + file list after Executor finishes
Produces: validation_report.md, sends result to Reviewer (on PASS) or back to Executor (on FAIL)
"""

from __future__ import annotations

import ast
import logging
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.message_bus import Message

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Import-name → pip-package-name mapping
# Add entries here whenever a new package is encountered.
# ---------------------------------------------------------------------------
_IMPORT_TO_PIP: dict[str, str | None] = {
    # Web scraping / HTTP
    "bs4": "beautifulsoup4",
    "requests": "requests",
    "httpx": "httpx",
    "aiohttp": "aiohttp",
    "lxml": "lxml",
    "selenium": "selenium",
    "playwright": "playwright",
    # Data / science
    "numpy": "numpy",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "scipy": "scipy",
    "sklearn": "scikit-learn",
    "statsmodels": "statsmodels",
    # Image / media
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "imageio": "imageio",
    # Config / serialization
    "yaml": "pyyaml",
    "toml": "toml",
    "dotenv": "python-dotenv",
    # PDF / Office
    "fitz": "pymupdf",
    "pypdf": "pypdf",
    "PyPDF2": "PyPDF2",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "openpyxl": "openpyxl",
    # AI / ML
    "openai": "openai",
    "anthropic": "anthropic",
    "tiktoken": "tiktoken",
    "transformers": "transformers",
    "torch": "torch",
    "whisper": "openai-whisper",
    "faster_whisper": "faster-whisper",
    # Video / audio
    "yt_dlp": "yt-dlp",
    "pytube": "pytube",
    "pydub": "pydub",
    "moviepy": "moviepy",
    # Web frameworks
    "flask": "flask",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "django": "django",
    "starlette": "starlette",
    # Databases
    "sqlalchemy": "sqlalchemy",
    "pymongo": "pymongo",
    "redis": "redis",
    "psycopg2": "psycopg2-binary",
    # CLI / output
    "click": "click",
    "rich": "rich",
    "typer": "typer",
    "tqdm": "tqdm",
    # Crypto / auth
    "jwt": "PyJWT",
    "Crypto": "pycryptodome",
    # Misc
    "chardet": "chardet",
    "dateutil": "python-dateutil",
    "pydantic": "pydantic",
    "attr": "attrs",
    "loguru": "loguru",
    "paramiko": "paramiko",
    "serial": "pyserial",
    # stdlib aliases (no install needed)
    "tomllib": None,   # stdlib in Python 3.11+
    "typing_extensions": "typing_extensions",
}

# Modules we know are stdlib — supplement sys.stdlib_module_names for older Pythons
_KNOWN_STDLIB = {
    "abc", "argparse", "ast", "asyncio", "base64", "collections", "contextlib",
    "copy", "csv", "dataclasses", "datetime", "decimal", "email", "enum",
    "functools", "glob", "hashlib", "http", "importlib", "inspect", "io",
    "itertools", "json", "logging", "math", "multiprocessing", "operator",
    "os", "pathlib", "pickle", "platform", "pprint", "queue", "random",
    "re", "shutil", "signal", "socket", "sqlite3", "string", "struct",
    "subprocess", "sys", "tempfile", "textwrap", "threading", "time",
    "traceback", "typing", "unicodedata", "unittest", "urllib", "uuid",
    "warnings", "weakref", "xml", "xmlrpc", "zipfile", "zlib",
    "__future__", "_thread", "builtins",
}


def _stdlib_modules() -> set[str]:
    if hasattr(sys, "stdlib_module_names"):          # Python 3.10+
        return sys.stdlib_module_names | _KNOWN_STDLIB   # type: ignore[operator]
    return _KNOWN_STDLIB


def _collect_imports(workspace: pathlib.Path) -> set[str]:
    """AST-parse all .py files and return top-level module names imported."""
    names: set[str] = set()
    for py in workspace.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names.add(node.module.split(".")[0])
    return names


def auto_install_workspace_deps(workspace: pathlib.Path) -> list[str]:
    """
    Deterministically install every missing dependency for code in `workspace`.

    Steps:
      1. pip install -r requirements.txt  (if present)
      2. pip install -e .  (editable install of the workspace package itself — critical
         for local imports like `from sop_engine import X` inside tests)
      3. pip install from pyproject.toml deps  (if present and parseable)
      4. AST-scan all .py files → collect imports → try to import each →
         pip install anything that fails.
      5. Fallback conftest.py — if no pyproject.toml, inject sys.path so pytest
         can always find local modules regardless of install state.

    Returns a list of packages that were actually installed.
    """
    installed: list[str] = []
    stdlib = _stdlib_modules()

    # --- Baseline: always install pytest-timeout so hung tests don't freeze the validator ---
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pytest-timeout", "-q"],
        capture_output=True, text=True,
    )

    # --- Step 1: requirements.txt ---
    req = workspace / "requirements.txt"
    if req.exists():
        logger.info("[validator] Installing from requirements.txt")
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req), "-q"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            installed.append("(requirements.txt)")
            logger.info("[validator] requirements.txt installed OK")
        else:
            logger.warning("[validator] requirements.txt install failed: %s", r.stderr[:400])

    # --- Step 2: pip install -e . (editable install of local package) ---
    # This is the PRIMARY fix for ModuleNotFoundError in tests.
    # Without this, `from sop_engine import X` fails even though the file exists.
    pyproject = workspace / "pyproject.toml"
    setup_py  = workspace / "setup.py"
    if pyproject.exists() or setup_py.exists():
        logger.info("[validator] Installing workspace package in editable mode: %s", workspace)
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(workspace), "-q",
             "--no-build-isolation"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            installed.append("(editable workspace)")
            logger.info("[validator] Editable install OK")
        else:
            logger.warning("[validator] Editable install failed: %s", r.stderr[:400])

    # --- Step 3: pyproject.toml explicit deps ---

        try:
            content = pyproject.read_text(encoding="utf-8")
            # Try stdlib tomllib first (Python 3.11+), fall back to toml package
            try:
                import tomllib  # type: ignore
                data = tomllib.loads(content)
            except ImportError:
                try:
                    import toml  # type: ignore
                    data = toml.loads(content)
                except ImportError:
                    data = {}
            deps = (
                data.get("project", {}).get("dependencies", [])
                or data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            )
            if isinstance(deps, dict):
                pkgs = [k for k in deps if k.lower() != "python"]
            else:
                pkgs = [str(d).split(">")[0].split("<")[0].split("=")[0].split("!")[0].strip()
                        for d in deps]
            if pkgs:
                logger.info("[validator] Installing from pyproject.toml: %s", pkgs)
                r = subprocess.run(
                    [sys.executable, "-m", "pip", "install", *pkgs, "-q"],
                    capture_output=True, text=True,
                )
                if r.returncode == 0:
                    installed.extend(pkgs)
        except Exception as e:
            logger.warning("[validator] pyproject.toml parse failed: %s", e)

    # --- Step 3: AST import scan ---
    third_party = _collect_imports(workspace) - stdlib
    for mod in sorted(third_party):
        # Skip if already importable
        try:
            __import__(mod)
            continue
        except ImportError:
            pass
        except Exception:
            continue  # e.g. ModuleNotFoundError with extras

        pip_pkg = _IMPORT_TO_PIP.get(mod, mod)   # default: same name
        if pip_pkg is None:
            continue  # explicitly stdlib alias

        logger.info("[validator] Auto-installing '%s' (import '%s')", pip_pkg, mod)
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_pkg, "-q"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            installed.append(pip_pkg)
        else:
            logger.warning("[validator] Failed to install %s: %s", pip_pkg, r.stderr[:300])
    # --- Step 5: conftest.py sys.path fallback ---
    # Ensures `import local_module` always works in pytest even without install.
    conftest = workspace / "conftest.py"
    conftest_injection = (
        "import sys, pathlib\n"
        "# Injected by pipeline validator — ensures local imports work in pytest\n"
        "_ws = pathlib.Path(__file__).parent\n"
        "if str(_ws) not in sys.path:\n"
        "    sys.path.insert(0, str(_ws))\n"
    )
    if not conftest.exists():
        conftest.write_text(conftest_injection, encoding="utf-8")
        logger.info("[validator] Created conftest.py with sys.path injection")
    elif "sys.path" not in conftest.read_text(encoding="utf-8"):
        existing = conftest.read_text(encoding="utf-8")
        conftest.write_text(conftest_injection + "\n" + existing, encoding="utf-8")
        logger.info("[validator] Prepended sys.path injection to existing conftest.py")

    if installed:
        logger.info("[validator] Deps installed: %s", installed)
    return installed



# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class ValidatorAgent(AgentProcess):
    role = "validator"
    max_steps = 25  # list_tree + read N files + pytest + ruff + write_file = easily 15+
    temperature = 0.2   # deterministic test running
    think = False       # mechanical validation — no CoT needed

    def handle(self, msg: Message) -> AgentOutput:
        phase_num = msg.payload.get("phase", 1)
        idea_slug = msg.payload.get("idea_slug", self._current_slug)
        workspace_path = msg.payload.get("workspace_path", str(self.get_workspace_path()))
        files_written = msg.payload.get("files_written", [])
        tasks_path = msg.payload.get("tasks_path", f"phases/phase_{phase_num}/tasks.md")
        report_path = msg.payload.get(
            "validation_report_path",
            f"phases/phase_{phase_num}/validation_report.md",
        )
        report_full_path = pathlib.Path(self._project_path(report_path))

        self._update_idea_status(f"phase_{phase_num}_validating", phase_num=phase_num)

        # ------------------------------------------------------------------
        # PRE-VALIDATION: deterministic dependency installation
        # This runs BEFORE the LLM so tests can't fail from missing modules.
        # ------------------------------------------------------------------
        ws = pathlib.Path(workspace_path)
        if ws.exists():
            try:
                auto_install_workspace_deps(ws)
            except Exception as e:
                logger.warning("[validator] auto_install_workspace_deps error: %s", e)

        # Read task list for acceptance criteria — ONLY for the current phase.
        # Some tasks.md files contain all phases; we must scope to the active one.
        raw_tasks = self.read_state_file(tasks_path)
        tasks_content = self._extract_phase_tasks(raw_tasks, phase_num)

        task_prompt = (
            f"You are validating Phase {phase_num} code output.\n"
            f"IMPORTANT: You are ONLY validating Phase {phase_num}. "
            f"Ignore any tasks or acceptance criteria from other phases.\n\n"
            f"## Workspace\n"
            f"All code is in: {workspace_path}\n"
            f"Files written: {', '.join(files_written) if files_written else '(check workspace)'}\n\n"
            f"## Phase {phase_num} Task List (for acceptance criteria)\n{tasks_content}\n\n"
            f"## Your Job — BE EFFICIENT (you have limited steps)\n"
            f"NOTE: Dependencies and a conftest.py (sys.path fix) have already been set up.\n\n"
            f"STEP 1: Run tests FIRST (most important):\n"
            f"   `cd {workspace_path} && python -m pytest -v --tb=short --timeout=120 -p no:timeout 2>&1 || true`\n"
            f"   The --timeout=120 flag kills any single test that hangs beyond 2 minutes.\n"
            f"   If pytest-timeout is not installed: `pip install pytest-timeout -q` first, then run.\n"
            f"   If no test files exist, note 'No tests found'.\n\n"
            f"STEP 2: Check files with: `find {workspace_path} -name '*.py' | sort`\n"
            f"   A file is PRESENT if it appears ANYWHERE under the workspace (including subdirs).\n"
            f"   Do NOT claim a file is missing just because it is not at the workspace root.\n"
            f"   Only read individual files if tests FAIL and you need to diagnose why.\n\n"
            f"STEP 3: Write your validation report to `{report_full_path}`.\n"
            f"   Use this exact format:\n"
            f"   ```\n"
            f"   # Validation Report — Phase {phase_num}\n"
            f"   ## Summary\n"
            f"   - Tests: X passed, Y failed\n"
            f"   ## Verdict: PASS\n"
            f"   ```\n"
            f"   PASS if tests pass or no tests exist AND core files are present.\n"
            f"   FAIL only if tests error/fail OR required files are missing.\n\n"
            f"STEP 4: Say DONE and state your verdict.\n"
            f"\nCRITICAL: You MUST call write_file to save the report to `{report_full_path}`. "
            f"Do not just print it — actually write it to the file.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)

        # Determine verdict from the structured report
        report_content = self.read_state_file(report_path)

        # --- Fallback: synthesize report from LLM answer if model forgot write_file ---
        if not report_content and result.answer:
            answer_upper = result.answer.upper()
            if "VERDICT: PASS" in answer_upper or "**VERDICT: PASS**" in answer_upper:
                synth_verdict = "Verdict: PASS"
            elif "VERDICT: FAIL" in answer_upper or "**VERDICT: FAIL**" in answer_upper:
                synth_verdict = "Verdict: FAIL"
            elif "NO TESTS FOUND" in answer_upper or "NO TEST FILES" in answer_upper:
                synth_verdict = "Verdict: PASS"  # No tests = pass by convention
            else:
                synth_verdict = "Verdict: FAIL"  # Unknown — assume fail, let executor retry
            report_content = (
                f"# Validation Report — Phase {phase_num}\n\n"
                f"## Summary\n(Synthesized from agent response — model did not write file)\n\n"
                f"## Agent Response\n{result.answer[:3000]}\n\n"
                f"## {synth_verdict}\n"
            )
            report_full_path.parent.mkdir(parents=True, exist_ok=True)
            report_full_path.write_text(report_content, encoding="utf-8")
            logger.info("[validator] Synthesized report from agent answer (verdict: %s)", synth_verdict)

        is_pass = bool(report_content) and "Verdict: PASS" in report_content

        if is_pass:
            # Clear validator retry counter for this phase on success
            try:
                retry_data = self.read_json_state("state/phase_retries.json")
                retry_data.pop(f"validator_phase_{phase_num}", None)
                self.write_json_state("state/phase_retries.json", retry_data)
            except Exception:
                pass
            out_msg = Message.create(
                from_agent=self.role,
                to_agent="reviewer",
                type="task",
                payload={
                    "phase": phase_num,
                    "workspace_path": workspace_path,
                    "files_written": files_written,
                    "tasks_path": tasks_path,
                    "validation_report_path": report_path,
                    "review_path": f"phases/phase_{phase_num}/review.md",
                    "idea_slug": idea_slug,
                },
            )
        else:
            # Progress-aware retry: keep going as long as failures are decreasing.
            # Only escalate when N consecutive cycles make zero improvement.
            NO_PROGRESS_LIMIT = 3  # consecutive stale cycles before force-advancing

            retry_key      = f"validator_phase_{phase_num}"
            prev_fail_key  = f"validator_phase_{phase_num}_prev_failures"
            streak_key     = f"validator_phase_{phase_num}_no_progress"

            try:
                retry_data = self.read_json_state("state/phase_retries.json")
            except Exception:
                retry_data = {}

            # Count failures in this report (pytest FAILED/ERROR lines + import errors)
            import re as _re
            fail_patterns = [
                r'\bFAILED\b', r'\bERROR\b', r'ImportError', r'ModuleNotFoundError',
                r'AssertionError', r'SyntaxError', r'Traceback',
            ]
            current_failures = sum(
                len(_re.findall(p, report_content))
                for p in fail_patterns
            )

            # If report was empty (model didn't write it), treat as MAX failures
            # so it never looks like 'progress' and no_progress counter increments.
            if not report_content:
                current_failures = 999

            prev_failures  = retry_data.get(prev_fail_key, current_failures + 1)
            no_progress    = retry_data.get(streak_key, 0)
            retry_count    = retry_data.get(retry_key, 0) + 1
            MAX_VALIDATOR_ATTEMPTS = 4  # absolute cap — ~80 min max per phase at 20min/cycle
            made_progress  = current_failures < prev_failures

            if made_progress:
                no_progress = 0  # reset streak — it's fixing things
                logger.info(
                    "[validator] Phase %d attempt %d: failures %d→%d (progress ✓)",
                    phase_num, retry_count, prev_failures, current_failures,
                )
            else:
                no_progress += 1
                logger.info(
                    "[validator] Phase %d attempt %d: failures %d→%d (no progress %d/%d)",
                    phase_num, retry_count, prev_failures, current_failures,
                    no_progress, NO_PROGRESS_LIMIT,
                )

            retry_data[retry_key]     = retry_count
            retry_data[prev_fail_key] = current_failures
            retry_data[streak_key]    = no_progress
            self.write_json_state("state/phase_retries.json", retry_data)

            if retry_count >= MAX_VALIDATOR_ATTEMPTS:
                # Absolute cap hit — escalate regardless of progress
                logger.warning(
                    "[validator] Phase %d hit absolute retry cap (%d) — force-escalating",
                    phase_num, MAX_VALIDATOR_ATTEMPTS,
                )
                no_progress = NO_PROGRESS_LIMIT  # trigger escalation path

            if no_progress >= NO_PROGRESS_LIMIT:
                # Truly stuck — same failures N cycles in a row, escalate
                for k in (retry_key, prev_fail_key, streak_key):
                    retry_data.pop(k, None)
                self.write_json_state("state/phase_retries.json", retry_data)
                out_msg = Message.create(
                    from_agent=self.role,
                    to_agent="manager",
                    type="signal",
                    payload={
                        "signal": "PHASE_STUCK",
                        "phase": phase_num,
                        "reason": (
                            f"No progress after {no_progress} consecutive fix attempts "
                            f"({current_failures} failures unchanged). Force-advancing."
                        ),
                        "validation_report": report_content[:2000],
                        "idea_slug": idea_slug,
                    },
                )
            else:
                progress_note = "↓ improving" if made_progress else "→ stalled"
                out_msg = Message.create(
                    from_agent=self.role,
                    to_agent="executor",
                    type="task",
                    payload={
                        "phase": phase_num,
                        "tasks_path": tasks_path,
                        "workspace_path": workspace_path,
                        "fix_required": True,
                        "validation_report": report_content[:3000],
                        "error_summary": (
                            f"Validation FAILED — attempt {retry_count}, "
                            f"{current_failures} failures remaining ({progress_note}). "
                            f"Fix the specific errors listed above."
                        ),
                        "idea_slug": idea_slug,
                    },
                )


        return AgentOutput(
            success=is_pass,
            answer=result.answer,
            outgoing=[out_msg],
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default=__import__("os").environ.get("PIPELINE_MODEL", "qwen3.5:35b"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [validator] %(message)s")

    agent = ValidatorAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
