"""
pipeline/agents/validator.py
Validator/Tester agent — runs tests, lint, and acceptance checks.

Receives: workspace path + file list after Executor finishes
Produces: validation_report.md, sends result to Reviewer (on PASS) or back to Executor (on FAIL)
"""

from __future__ import annotations

import ast
import logging
import os
import pathlib
import re
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
    "webvtt": "webvtt-py",
    "tree_sitter_python": "tree-sitter-python",
    "tree_sitter_javascript": "tree-sitter-javascript",
    "tree_sitter_typescript": "tree-sitter-typescript",
    "sentence_transformers": "sentence-transformers",
    "spacy": "spacy",
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
    "yaml": "pyyaml",      # governance.py and many projects use yaml
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
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
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
                pkgs = [
                    str(d).split(">")[0].split("<")[0].split("=")[0].split("!")[0].strip()
                    for d in deps
                ]
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

    # --- Step 4: AST import scan ---
    # First inject workspace into sys.path so local packages are importable
    # without needing pip install — prevents trying to PyPI-install local names.
    _local_package_names: set[str] = set()
    if str(workspace) not in sys.path:
        sys.path.insert(0, str(workspace))
    # Collect names of local packages (dirs with __init__.py or .py files at root)
    for item in workspace.iterdir():
        if item.is_dir() and (item / "__init__.py").exists():
            _local_package_names.add(item.name)
        elif item.is_file() and item.suffix == ".py" and item.stem != "conftest":
            _local_package_names.add(item.stem)

    third_party = _collect_imports(workspace) - stdlib
    for mod in sorted(third_party):
        # Skip local packages — they exist on disk, not on PyPI
        if mod in _local_package_names:
            continue
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
# Deterministic pytest runner (no LLM)
# ---------------------------------------------------------------------------

def _count_py_files(workspace: pathlib.Path) -> int:
    return sum(1 for p in workspace.rglob("*.py") if p.is_file())


def _pytest_timeout_available() -> bool:
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return "--timeout" in (r.stdout or "")
    except Exception:
        return False


def run_pytest(workspace: pathlib.Path, timeout_per_test: int = 120) -> dict:
    """
    Run pytest in `workspace` and return structured results.

    Exit codes: 0 = pass, 5 = no tests collected (treated as pass).
    """
    tests_dir = workspace / "tests"
    target = "tests/" if tests_dir.exists() and tests_dir.is_dir() else "."

    base_cmd = [sys.executable, "-m", "pytest", target, "-v", "--tb=short", "--no-header"]
    if _pytest_timeout_available():
        cmd = base_cmd + [f"--timeout={timeout_per_test}"]
    else:
        cmd = base_cmd

    logger.info("[validator] Running pytest in %s (target=%s)", workspace, target)
    proc = subprocess.run(
        cmd,
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    # Retry without --timeout if plugin missing (exit 4 + usage error)
    if proc.returncode == 4 and "unrecognized arguments: --timeout" in combined:
        proc = subprocess.run(
            base_cmd,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
    combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    passed = len(re.findall(r"\bPASSED\b", combined))
    failed = len(re.findall(r"\bFAILED\b", combined))
    errors = len(re.findall(r"\bERROR\b", combined))

    # Summary footer is authoritative: "71 passed, 1 failed in 8.18s"
    sm_passed = re.search(r"(\d+)\s+passed", combined, re.IGNORECASE)
    sm_failed = re.search(r"(\d+)\s+failed", combined, re.IGNORECASE)
    sm_errors = re.search(r"(\d+)\s+errors?", combined, re.IGNORECASE)
    if sm_passed:
        passed = int(sm_passed.group(1))
    if sm_failed:
        failed = int(sm_failed.group(1))
    if sm_errors:
        errors = int(sm_errors.group(1))

    summary_m = re.search(
        r"=+\s*([\d\w ,]+)\s+in\s+[\d.]+s\s*=+",
        combined,
        re.IGNORECASE,
    )
    summary_line = summary_m.group(0).strip() if summary_m else ""
    no_tests = (
        proc.returncode == 5
        or "no tests ran" in combined.lower()
        or "collected 0 items" in combined.lower()
    )

    return {
        "returncode": proc.returncode,
        "stdout": combined,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "no_tests": no_tests,
        "summary_line": summary_line,
    }


def _structural_gate_enabled() -> bool:
    # Soft default: off until pipelines opt in (legacy workspaces lack tests/import hygiene)
    from pipeline.env_flags import env_bool
    return env_bool("PIPELINE_STRUCTURAL_GATE", default=False)


def _require_tests_enabled() -> bool:
    # Soft default: off — set PIPELINE_REQUIRE_TESTS=1 for strict quality runs
    from pipeline.env_flags import env_bool
    return env_bool("PIPELINE_REQUIRE_TESTS", default=False)


def _run_structural_scan(workspace: pathlib.Path) -> tuple[bool, str]:
    """Return (ok, report_section).

    When the gate is enabled, only **local** graph issues (and scan crashes) fail.
    Uninstalled third-party imports are non-blocking warnings.
    """
    if not _structural_gate_enabled() or not workspace.exists():
        return True, ""
    try:
        from pipeline.import_graph import scan_workspace

        graph = scan_workspace(workspace)
        block = graph.format_block() if hasattr(graph, "format_block") else ""
        if not graph.has_blocking_issues:
            if graph.warnings:
                warn = "\n".join(f"- {w}" for w in graph.warnings[:15])
                return True, f"\n## Structural / import issues\n- None blocking\n### Warnings\n{warn}\n"
            return True, "\n## Structural / import issues\n- None\n"
        return False, f"\n## Structural / import issues\n{block}\n"
    except Exception as exc:
        logger.warning("[validator] structural scan error (fail closed when gate on): %s", exc)
        return False, f"\n## Structural / import issues\n- FAIL (scan error): {exc}\n"


def build_validation_report(
    phase_num: int,
    pytest_result: dict,
    tasks_content: str,
    workspace: pathlib.Path,
    *,
    structural_ok: bool = True,
    structural_section: str = "",
) -> tuple[str, bool]:
    """Build validation_report.md content and return (report, is_pass)."""
    pr = pytest_result
    py_count = _count_py_files(workspace)
    has_code = py_count > 0
    require_tests = _require_tests_enabled()

    if pr["no_tests"]:
        test_line = "- Tests: no tests collected (0 run)"
        if require_tests and has_code:
            tests_ok = False
            test_line += " — FAIL (PIPELINE_REQUIRE_TESTS: code present but no tests)"
        else:
            tests_ok = True
    else:
        test_line = (
            f"- Tests: {pr['passed']} passed, {pr['failed']} failed, "
            f"{pr['errors']} errors"
        )
        tests_ok = pr["returncode"] == 0 and pr["failed"] == 0 and pr["errors"] == 0

    files_line = f"- Python files in workspace: {py_count}"
    structural_line = (
        f"- Structural gate: {'PASS' if structural_ok else 'FAIL'}"
        if _structural_gate_enabled()
        else "- Structural gate: disabled"
    )

    # Empty workspace (no code, no tests): soft PASS — scaffolding / docs phases.
    # require_tests only applies when code is present.
    if tests_ok and structural_ok and (has_code or pr["no_tests"]):
        if not has_code and pr["no_tests"]:
            files_line += " (empty workspace — soft pass)"
        verdict = "Verdict: PASS"
        is_pass = True
    elif pr["no_tests"] and not has_code:
        # Unreachable when tests_ok True; keep FAIL path if structural failed
        verdict = "Verdict: FAIL"
        is_pass = False
        files_line += " (no .py files found)"
    else:
        verdict = "Verdict: FAIL"
        is_pass = False

    details = ""
    if not is_pass and pr["stdout"]:
        # Keep tail of output — failures are usually at the end
        tail = pr["stdout"][-8000:]
        details = f"\n## Test Output\n```\n{tail}\n```\n"

    tasks_block = ""
    if tasks_content.strip():
        tasks_block = f"\n## Phase {phase_num} Tasks (acceptance scope)\n{tasks_content[:4000]}\n"

    report = (
        f"# Validation Report — Phase {phase_num}\n\n"
        f"## Summary\n"
        f"{test_line}\n"
        f"{files_line}\n"
        f"{structural_line}\n"
        f"(Deterministic pytest + structural gate — no LLM validator steps used.)\n"
        f"{tasks_block}"
        f"{structural_section}"
        f"{details}\n"
        f"## {verdict}\n"
    )
    return report, is_pass


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class ValidatorAgent(AgentProcess):
    role = "validator"
    model_tier = "light"
    num_ctx = 8192
    max_steps = 8   # LLM only when PIPELINE_VALIDATOR_USE_LLM=1 (legacy path)
    temperature = 0.2
    think = False

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

        use_llm = os.environ.get("PIPELINE_VALIDATOR_USE_LLM", "").strip().lower() in (
            "1", "true", "yes",
        )
        result_answer = ""
        tokens_used = 0
        steps_used = 0

        if ws.exists():
            try:
                pytest_result = run_pytest(ws)
            except subprocess.TimeoutExpired:
                pytest_result = {
                    "returncode": 1,
                    "stdout": "pytest timed out after 600s",
                    "passed": 0,
                    "failed": 0,
                    "errors": 1,
                    "no_tests": False,
                    "summary_line": "",
                }
            except Exception as e:
                logger.warning("[validator] pytest error: %s", e)
                pytest_result = {
                    "returncode": 1,
                    "stdout": f"pytest failed to run: {e}",
                    "passed": 0,
                    "failed": 0,
                    "errors": 1,
                    "no_tests": False,
                    "summary_line": "",
                }
        else:
            pytest_result = {
                "returncode": 1,
                "stdout": f"Workspace not found: {workspace_path}",
                "passed": 0,
                "failed": 0,
                "errors": 1,
                "no_tests": False,
                "summary_line": "",
            }

        ws_path = ws if ws.exists() else pathlib.Path(workspace_path)
        structural_ok, structural_section = _run_structural_scan(ws_path)
        report_content, is_pass = build_validation_report(
            phase_num,
            pytest_result,
            tasks_content,
            ws_path,
            structural_ok=structural_ok,
            structural_section=structural_section,
        )
        report_full_path.parent.mkdir(parents=True, exist_ok=True)
        report_full_path.write_text(report_content, encoding="utf-8")
        logger.info(
            "[validator] Deterministic verdict phase %d: %s (rc=%s structural=%s)",
            phase_num,
            "PASS" if is_pass else "FAIL",
            pytest_result.get("returncode"),
            "ok" if structural_ok else "fail",
        )
        if not is_pass:
            from pipeline.pipeline_activity import log_activity
            log_activity(
                "validator_fail",
                phase=phase_num,
                slug=idea_slug,
                structural_ok=structural_ok,
                no_tests=bool(pytest_result.get("no_tests")),
            )

        # Optional legacy LLM path for extra diagnosis on failure
        if not is_pass and use_llm:
            task_prompt = (
                f"Phase {phase_num} tests FAILED. Workspace: {workspace_path}\n\n"
                f"## Pytest output (already run)\n```\n{pytest_result['stdout'][-6000:]}\n```\n\n"
                f"## Tasks\n{tasks_content[:3000]}\n\n"
                f"Add a brief ## Diagnosis section (3-5 bullets) to `{report_full_path}` "
                f"using patch_file or write_file. Say DONE when done."
            )
            result = self.call_agent(task=task_prompt, verbose=False)
            result_answer = result.answer
            tokens_used = result.tokens_used
            steps_used = result.steps_used
            report_content = self.read_state_file(report_path) or report_content
            is_pass = "Verdict: PASS" in report_content

        if is_pass:
            # Determine retry count from fix report
            retry_count = 0
            try:
                _fix_report_str = f"phases/phase_{phase_num}/fix_report.md"
                _existing_report = self.read_state_file(_fix_report_str)
                if _existing_report:
                    import re as _re
                    _att_cnt = len(_re.findall(r"^### Attempt \d+", _existing_report, _re.MULTILINE))
                    retry_count = max(_att_cnt, 1)
            except Exception:
                pass

            # Clear validator retry counter for this phase on success
            try:
                retry_data = self.read_json_state("state/phase_retries.json")
                retry_data.pop(f"validator_phase_{phase_num}", None)
                self.write_json_state("state/phase_retries.json", retry_data)
            except Exception:
                pass

            # Phase passed — drop per-phase fix memory (stale bans no longer apply)
            try:
                from pipeline.phase_fix_memory import clear_fix_memory

                clear_fix_memory(pathlib.Path(self._project_dir), int(phase_num))
            except Exception:
                pass

            try:
                from pipeline.bug_memory import record_validator_pass
                fix_report_path_str = f"phases/phase_{phase_num}/fix_report.md"
                existing_fix_report = self.read_state_file(fix_report_path_str)
                record_validator_pass(
                    idea_slug,
                    phase_num,
                    existing_fix_report,
                    report_content,
                    retry_count,
                )
                if existing_fix_report and retry_count >= 1:
                    logger.info(
                        "[validator] Bug memory: recorded resolution for %s phase %d (%d retries)",
                        idea_slug, phase_num, retry_count,
                    )
            except Exception as _bm_err:
                logger.warning("[validator] Bug memory write failed (non-critical): %s", _bm_err)

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
                    "retry_count": retry_count,
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

            # Use structured pytest counts (stable; avoids matching ERROR in prose)
            current_failures = (
                int(pytest_result.get("failed", 0))
                + int(pytest_result.get("errors", 0))
            )
            if current_failures == 0 and not is_pass:
                current_failures = 1  # workspace missing code, etc.

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

            try:
                from pipeline.bug_memory import record_failure_observation
                record_failure_observation(
                    idea_slug, phase_num, report_content, retry_count,
                )
            except Exception:
                pass

            # Structured phase fix memory — ban repeated failure signatures
            try:
                from pipeline.phase_fix_memory import record_failed_attempt

                record_failed_attempt(
                    pathlib.Path(self._project_dir),
                    int(phase_num),
                    summary=(
                        f"Validation FAIL attempt {retry_count}: "
                        f"{current_failures} failures "
                        f"({'improving' if made_progress else 'no progress'})"
                    ),
                    source_text=report_content,
                    ban=True,
                )
            except Exception:
                pass

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
                        "retry_count": int(retry_count),
                    },
                )
            else:
                progress_note = "↓ improving" if made_progress else "→ stalled"

                mock_hint = ""
                if "AssertionError: Expected mock" in report_content or "AttributeError: <" in report_content or "does not have the attribute" in report_content:
                    mock_hint = "\n\n💡 HINT: You have mocking errors. Check if your @patch decorators are mocking the target where it is IMPORTED (e.g. `@patch('module_under_test.Dependency')`), not where it is DEFINED."

                # --- Write persistent fix_report.md with full context ---
                fix_report_path = f"phases/phase_{phase_num}/fix_report.md"
                fix_report_full = pathlib.Path(self._project_path(fix_report_path))
                fix_report_full.parent.mkdir(parents=True, exist_ok=True)

                attempt_entry = (
                    f"### Attempt {retry_count}\n"
                    f"- **Failures**: {current_failures} ({progress_note})\n"
                    f"- **Previous failures**: {prev_failures}\n\n"
                    f"#### Test Output\n```\n{report_content[:6000]}\n```\n\n"
                )

                if fix_report_full.exists():
                    existing = fix_report_full.read_text(encoding="utf-8")
                    updated = existing + "\n" + attempt_entry
                else:
                    updated = (
                        f"# Fix Report — Phase {phase_num}\n\n"
                        f"## Current Issues\n"
                        f"{report_content[:4000]}\n\n"
                        f"## Attempt History\n\n"
                        + attempt_entry
                    )
                fix_report_full.write_text(updated, encoding="utf-8")

                # Retry 3+ → manager for analysis; retries 1-2 → executor directly
                MANAGER_THRESHOLD = 3
                if retry_count >= MANAGER_THRESHOLD:
                    out_msg = Message.create(
                        from_agent=self.role,
                        to_agent="manager",
                        type="task",
                        payload={
                            "phase": phase_num,
                            "signal": "FIX_ANALYSIS_NEEDED",
                            "tasks_path": tasks_path,
                            "workspace_path": workspace_path,
                            "fix_report_path": fix_report_path,
                            "retry_count": retry_count,
                            "current_failures": current_failures,
                            "made_progress": made_progress,
                            "idea_slug": idea_slug,
                        },
                    )
                    logger.info(
                        "[validator] Phase %d retry %d → manager for analysis (%d failures)",
                        phase_num, retry_count, current_failures,
                    )
                else:
                    out_msg = Message.create(
                        from_agent=self.role,
                        to_agent="executor",
                        type="task",
                        payload={
                            "phase": phase_num,
                            "tasks_path": tasks_path,
                            "workspace_path": workspace_path,
                            "fix_required": True,
                            "fix_report_path": fix_report_path,
                            "retry_count": retry_count,
                            "error_summary": (
                                f"Validation FAILED — attempt {retry_count}, "
                                f"{current_failures} failures ({progress_note}). "
                                f"Read fix_report.md for full details + previous attempts."
                                f"{mock_hint}"
                            ),
                            "idea_slug": idea_slug,
                        },
                    )


        return AgentOutput(
            success=is_pass,
            answer=result_answer or ("PASS" if is_pass else "FAIL"),
            outgoing=[out_msg],
            tokens_used=tokens_used,
            steps_used=steps_used,
        )


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    from pipeline.pipeline_config import DEFAULT_PIPELINE_MODEL
    parser.add_argument("--model", default=DEFAULT_PIPELINE_MODEL)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [validator] %(message)s")

    agent = ValidatorAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
