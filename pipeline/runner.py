"""
pipeline/runner.py
Main entry point — subprocess orchestrator for the multi-agent pipeline.

Starts each agent as a subprocess, monitors health, handles shutdown.

Usage:
    python pipeline/runner.py "Build a web scraper for Hacker News"
    python pipeline/runner.py --from-list
    python pipeline/runner.py --resume
    python pipeline/runner.py --from-list --provider ollama --model qwen3.5:35b --time-limit 480
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone

_ANSI_ESCAPE = re.compile(r'(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~]|\x1B\][^\x07\x1B]*(?:\x07|\x1B\\))')

# Suppress Jupyter/cloud terminal escape sequences (^[]11;rgb:... etc.)
# These are OSC color query responses that pollute output in web terminals.
if not sys.stdout.isatty():
    os.environ.setdefault("TERM", "dumb")

def _clean(text: str) -> str:
    """Strip ANSI/OSC escape sequences from a string."""
    return _ANSI_ESCAPE.sub('', text)

# Ensure project root is on path
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.message_bus import MessageBus, Message
from pipeline.metrics import RunMetrics
from pipeline.context_aggregator import (
    refresh_all_projects,
    start_background_refresh,
    stop_background_refresh,
    refresh_project,
)

# Anchor PIPELINE_DIR to where this script lives (project root), not cwd.
# This prevents /workspace/.pipeline vs /.pipeline splits when the user
# starts the runner from different directories.
PIPELINE_DIR = PROJECT_ROOT.resolve() / ".pipeline"
AGENTS_DIR = pathlib.Path(__file__).parent / "agents"

# All agent roles and their module paths
AGENT_ROLES = [
    "idea_planner",
    "phase_planner",
    "executor",
    "validator",
    "reviewer",
    "manager",
    "ideator",
]


# Default budget values (can be overridden via CLI --base-budget / --phase-budget)
DEFAULT_BASE_BUDGET = 90    # minimum minutes per project (floor)
DEFAULT_PHASE_BUDGET = 30   # minutes per phase (scales with total_phases)
# Actual budget = max(base_budget, total_phases * phase_budget)
# Override via CLI for different GPU sizes:
#   --base-budget 60 --phase-budget 20   (smaller GPU, faster timeouts)
#   --base-budget 180 --phase-budget 45  (big GPU, more time per phase)

# ---------------------------------------------------------------------------
# Ollama health checks
# ---------------------------------------------------------------------------

def _check_ollama_model(model: str) -> None:
    """Pre-flight check: verify Ollama is reachable and the model is available.

    Catches common misconfigurations (wrong model name, Ollama not running,
    model not on GPU) BEFORE starting agents, preventing silent hour-long
    failures.
    """
    import urllib.request
    import urllib.error
    base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    # Normalize: add http:// if missing, replace bind address with localhost
    if not base_url.startswith("http"):
        base_url = f"http://{base_url}"
    base_url = base_url.replace("://0.0.0.0", "://localhost")

    # 1. Check Ollama is running
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/tags", timeout=5)
        data = json.loads(resp.read())
    except Exception as e:
        print(f"\n  ❌ Ollama not reachable at {base_url}: {e}")
        print(f"     Start Ollama first: ollama serve &")
        sys.exit(1)
    # 2. Check model exists — resolve the EXACT canonical name from the API.
    # Ollama may normalize case (q4_K_M → q4_k_m) internally.
    # IMPORTANT: We do NOT do loose partial matching — "qwen3.6" must not
    # accidentally match "qwen3.5". Match must include both base AND tag.
    available = [m.get("name", "") for m in data.get("models", [])]

    # Try exact match first (case-insensitive)
    canonical = next((m for m in available if m.lower() == model.lower()), None)
    if canonical is None:
        # Case-insensitive match on full name including tag
        model_lower = model.lower()
        canonical = next(
            (m for m in available if m.lower() == model_lower),
            None,
        )

    if canonical is None:
        print(f"\n  ❌ Model '{model}' not found in Ollama.")
        print(f"     Available: {', '.join(available) or '(none)'}")
        print(f"     Pull it:   ollama pull {model}")
        sys.exit(1)

    if canonical != model:
        print(f"  Model name resolved: '{model}' -> '{canonical}' (using API canonical name)")
        model = canonical  # Use the exact name the API knows about

    # Prevent Ollama from auto-pulling models during the pipeline run.
    # Without this, if any agent accidentally uses a wrong model name,
    # Ollama silently downloads it (23GB+) instead of erroring.
    os.environ.setdefault("OLLAMA_NO_PULL", "1")

    # 3. Warm up: trigger a tiny inference to load model into VRAM.
    # Use /api/chat with think:false — /api/generate with num_predict:5 returns
    # empty for thinking models because all tokens go to the <think> block.
    print(f"  Model:    {model} (warming up...)", end="", flush=True)
    try:
        req = urllib.request.Request(
            f"{base_url}/api/chat",
            data=json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": "/no_think say OK"}],
                "stream": False,
                "think": False,             # disable chain-of-thought for warmup
                "keep_alive": -1,           # pin model in VRAM after warmup
                "options": {"num_predict": 30},
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=300)  # 5 min — large models take time
        result = json.loads(resp.read())
        # Accept response from either message.content or thinking field
        content = (
            result.get("message", {}).get("content", "")
            or result.get("message", {}).get("thinking", "")
            or result.get("response", "")
        )
        if content.strip():
            print(" ✅")
        else:
            print(" ⚠️  (empty response — model may need restart)")
    except Exception as e:
        print(f" ⚠️  warmup failed: {e}")

    # 4. Check GPU allocation
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/ps", timeout=5)
        ps_data = json.loads(resp.read())
        models_loaded = ps_data.get("models", [])
        if models_loaded:
            for m in models_loaded:
                vram_gb = m.get("size_vram", 0) / 1e9
                total_gb = m.get("size", 0) / 1e9
                name = m.get("name", "?")
                if vram_gb > 0.5:
                    print(f"  GPU:      {name} — {vram_gb:.1f}GB VRAM ✅")
                elif total_gb > 0:
                    print(f"  ⚠️  GPU:   {name} — {vram_gb:.1f}GB VRAM / {total_gb:.1f}GB total — RUNNING ON CPU!")
                    print(f"             Pipeline will be ~10-20x slower than GPU.")
        else:
            print(f"  ⚠️  GPU:   No models loaded after warmup — check Ollama GPU config")
    except Exception:
        pass  # Non-critical

    # Evict any other models installed on this instance.
    # Vast.ai and RunPod templates often pre-load qwen3.5 or other models.
    # Removing them frees VRAM and prevents background processes from
    # accidentally triggering a load (which shows as "modified" in ollama list).
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/tags", timeout=5)
        tags = json.loads(resp.read()).get("models", [])
        model_base = model.split(":")[0].lower()
        for m in tags:
            name = m.get("name", "")
            if name.lower() != model.lower() and name.split(":")[0].lower() != model_base:
                print(f"  Removing unintended model: {name}")
                import subprocess
                subprocess.run(["ollama", "rm", name], capture_output=True)
    except Exception:
        pass  # Non-critical — best effort cleanup

    return model  # Return canonical model name for caller to use


def _check_ollama_heartbeat(model: str, _last_ok: list = [0.0]) -> str:
    """Quick Ollama liveness check + keepalive ping. Returns status string.

    Only pings once every 5 minutes (tracked via _last_ok mutable default).
    If the model is IDLE (evicted from VRAM), sends a keepalive request to
    reload it so agents don't run on CPU.
    """
    now = time.time()
    if now - _last_ok[0] < 300:  # Only check every 5 min
        return ""
    _last_ok[0] = now

    import urllib.request
    base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    if not base_url.startswith("http"):
        base_url = f"http://{base_url}"
    base_url = base_url.replace("://0.0.0.0", "://localhost")
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/ps", timeout=5)
        ps_data = json.loads(resp.read())
        models = ps_data.get("models", [])
        if models:
            vram = models[0].get("size_vram", 0) / 1e9
            return f"gpu={vram:.0f}GB"
        else:
            # Model was evicted — send a keepalive ping to reload into VRAM
            try:
                import json as _json
                payload = _json.dumps({
                    "model": model,
                    "prompt": "",
                    "keep_alive": -1,   # never auto-evict
                    "stream": False,
                }).encode()
                req = urllib.request.Request(
                    f"{base_url}/api/generate",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=180)  # 3 min for 23GB model reload
                return "gpu=RELOADING"
            except Exception:
                return "gpu=IDLE"
    except Exception:
        return "gpu=ERR"


# ---------------------------------------------------------------------------
# Pipeline state management
# ---------------------------------------------------------------------------

def init_pipeline_dirs() -> None:
    """Create all pipeline runtime directories."""
    for subdir in ["queues", "state", "projects", "logs"]:
        (PIPELINE_DIR / subdir).mkdir(parents=True, exist_ok=True)


def _slugify(title: str) -> str:
    """Convert an idea title to a filesystem-safe slug.
    'CSV Analyzer' -> 'csv_analyzer', '[Youtube studio]' -> 'youtube_studio'
    """
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_-]+', '_', slug)
    return slug.strip('_') or "unknown"


def _get_active_idea_state(pipeline_dir: pathlib.Path) -> dict:
    """Return the current_idea.json from the most recently modified IN-PROGRESS project.

    Skips projects in terminal states (complete, budget_exceeded) so that
    manually-edited state files don't permanently hijack the active slot.
    Falls back to the old global .pipeline/state/current_idea.json for
    backwards compatibility with runs that predate the per-project isolation.
    """
    INACTIVE = {"complete", "budget_exceeded", "dep_waiting"}
    projects_dir = pipeline_dir / "projects"
    candidates: list[pathlib.Path] = []

    if projects_dir.exists():
        candidates = list(projects_dir.glob("*/state/current_idea.json"))

    if candidates:
        # Prefer in-progress projects sorted by most recently modified
        def sort_key(p: pathlib.Path):
            try:
                state = json.loads(p.read_text(encoding="utf-8"))
                is_terminal = state.get("status", "") in INACTIVE
                return (1 if is_terminal else 0, -p.stat().st_mtime)
            except Exception:
                return (2, 0.0)

        candidates.sort(key=sort_key)
        for path in candidates:
            try:
                state = json.loads(path.read_text(encoding="utf-8"))
                state.setdefault("_slug", path.parent.parent.name)
                return state
            except Exception:
                continue

    # Fallback: old global location (pre-isolation runs)
    old_path = pipeline_dir / "state" / "current_idea.json"
    if old_path.exists():
        try:
            return json.loads(old_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {}


def save_pipeline_status(status: dict) -> None:
    path = PIPELINE_DIR / "state" / "pipeline_status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)


def load_pipeline_status() -> dict:
    path = PIPELINE_DIR / "state" / "pipeline_status.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Agent subprocess management
# ---------------------------------------------------------------------------

class AgentSupervisor:
    """Manages agent subprocesses."""

    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        self.processes: dict[str, subprocess.Popen] = {}
        self._stop_requested = False

    def start_agent(self, role: str) -> subprocess.Popen:
        """Start an agent as a subprocess."""
        module_path = AGENTS_DIR / f"{role}.py"
        if not module_path.exists():
            raise FileNotFoundError(f"Agent module not found: {module_path}")

        cmd = [
            sys.executable, str(module_path),
            "--provider", self.provider,
            "--model", self.model,
        ]

        # Set up environment with project root on PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONUTF8"] = "1"
        # Pass model/provider as env vars so agent_process.DEFAULT_MODEL picks
        # them up even if the argparse defaults are used instead of CLI args.
        env["PIPELINE_MODEL"] = self.model
        env["PIPELINE_PROVIDER"] = self.provider
        env["OLLAMA_NO_PULL"] = "1"   # never auto-download a model mid-pipeline

        log_path = PIPELINE_DIR / "logs" / f"{role}.out"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log_path, "a", encoding="utf-8")

        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            # On Windows, use CREATE_NEW_PROCESS_GROUP for clean shutdown
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        log_file.close()  # child inherited the handle; parent must close its copy

        self.processes[role] = proc
        return proc

    def start_all(self) -> None:
        """Start all agent subprocesses."""
        for role in AGENT_ROLES:
            self.start_agent(role)
            print(f"  ✓ Started {role} (PID {self.processes[role].pid})")
            time.sleep(0.5)  # stagger starts slightly

    def stop_all(self) -> None:
        """Gracefully stop all agent subprocesses."""
        self._stop_requested = True

        # Send shutdown signal via message bus
        bus = MessageBus()
        for role in AGENT_ROLES:
            bus.send_signal("runner", role, "SHUTDOWN")

        # Wait up to 10 seconds for graceful shutdown
        deadline = time.time() + 10
        for role, proc in self.processes.items():
            remaining = max(0, deadline - time.time())
            try:
                proc.wait(timeout=remaining)
                print(f"  ✓ {role} stopped gracefully")
            except subprocess.TimeoutExpired:
                print(f"  ⚠ {role} didn't stop, killing...")
                proc.kill()
                proc.wait(timeout=5)

    def check_health(self) -> dict[str, str]:
        """Check which agents are running."""
        status = {}
        for role, proc in self.processes.items():
            ret = proc.poll()
            if ret is None:
                status[role] = "running"
            else:
                status[role] = f"exited({ret})"
        return status

    def restart_dead(self) -> list[str]:
        """Restart any agents that have died unexpectedly."""
        restarted = []
        for role, proc in list(self.processes.items()):
            if proc.poll() is not None and not self._stop_requested:
                print(f"  ⚠ {role} died (exit={proc.returncode}), restarting...")
                self.start_agent(role)
                restarted.append(role)
                time.sleep(1)
        return restarted

    def save_registry(self) -> None:
        """Write current agent state to registry file."""
        registry = {}
        for role, proc in self.processes.items():
            registry[role] = {
                "pid": proc.pid,
                "status": "running" if proc.poll() is None else f"exited({proc.returncode})",
            }
        path = PIPELINE_DIR / "state" / "agent_registry.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)


# ---------------------------------------------------------------------------
# Dep-aware stale-reset purge
# ---------------------------------------------------------------------------

def _purge_dep_blocked_messages(bus: "MessageBus") -> int:
    """After reset_stale_processing(), drop pending messages for projects
    whose dependencies are not yet satisfied.

    Without this, a project that was already started (pending message in
    queue, dep still running) bypasses every dep check and gets picked up
    by agents immediately after restart.

    Returns the number of messages purged.
    """
    DONE_STATUSES = ("complete", "budget_exceeded")
    projects_dir = PIPELINE_DIR / "projects"
    purged = 0

    for role in AGENT_ROLES:
        msgs = bus.peek(role)
        for msg in msgs:
            slug = (msg.payload.get("idea_slug")
                    or msg.payload.get("slug")
                    or "")
            if not slug:
                continue

            state_file = projects_dir / slug / "state" / "current_idea.json"
            if not state_file.exists():
                continue

            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            deps = state.get("depends_on", [])
            if not deps:
                continue

            blocking = []
            for dep_slug in deps:
                dep_file = projects_dir / dep_slug / "state" / "current_idea.json"
                if not dep_file.exists():
                    blocking.append(f"{dep_slug} (not started)")
                    continue
                try:
                    dep_st = json.loads(dep_file.read_text(encoding="utf-8"))
                    if dep_st.get("status") not in DONE_STATUSES:
                        blocking.append(f"{dep_slug} ({dep_st.get('status', '?')})")
                except Exception:
                    blocking.append(f"{dep_slug} (unreadable)")

            if blocking:
                q_path = bus._queue_path(role)
                try:
                    lines = q_path.read_text(encoding="utf-8").splitlines()
                    kept = [l for l in lines if msg.id not in l]
                    if len(kept) < len(lines):
                        q_path.write_text("\n".join(kept) + ("\n" if kept else ""),
                                          encoding="utf-8")
                        # Mark the project as dep_waiting so _rebuild skips it
                        try:
                            st = json.loads(state_file.read_text(encoding="utf-8"))
                            if st.get("status") not in ("complete", "budget_exceeded", "dep_waiting"):
                                st["status"] = "dep_waiting"
                                state_file.write_text(json.dumps(st, indent=2), encoding="utf-8")
                        except Exception:
                            pass
                        print(f"  \U0001f6ab Purged dep-blocked queue for '{slug}' "
                              f"(waiting for: {', '.join(blocking)})")
                        purged += 1
                except Exception:
                    pass

    return purged


# ---------------------------------------------------------------------------
# Seed the pipeline with the first idea
# ---------------------------------------------------------------------------

_seeded_this_session: set[str] = set()  # titles seeded in this runner invocation


def seed_idea(bus: MessageBus, title: str, description: str,
              deps: list | None = None, locked: bool = False) -> None:
    """Send the initial idea to the Idea Planner to kick off the pipeline."""
    if title in _seeded_this_session:
        return  # already seeded this run — don't duplicate
    _seeded_this_session.add(title)

    idea_slug = _slugify(title)

    # Resolve dependency workspace paths so idea_planner can read existing interfaces
    dep_workspaces: dict = {}
    if deps:
        for dep_slug in deps:
            ws = PIPELINE_DIR / "projects" / dep_slug / "workspace"
            if ws.exists():
                dep_workspaces[dep_slug] = str(ws)

    # Write a stub current_idea.json NOW so deps survive runner restarts.
    # idea_planner will overwrite this with full state once it processes the idea.
    stub_state_file = PIPELINE_DIR / "projects" / idea_slug / "state" / "current_idea.json"
    if not stub_state_file.exists():
        stub_state_file.parent.mkdir(parents=True, exist_ok=True)
        stub_state_file.write_text(json.dumps({
            "title": title,
            "slug": idea_slug,
            "status": "phase_1_planning",
            "depends_on": deps or [],
            "budget_lock": locked,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }, indent=2), encoding="utf-8")

    msg = Message.create(
        from_agent="runner",
        to_agent="idea_planner",
        type="task",
        payload={
            "title": title,
            "idea": description,
            "idea_slug": idea_slug,
            "depends_on": deps or [],
            "dep_workspaces": dep_workspaces,
        },
    )
    bus.send(msg)
    dep_note = f" [deps: {', '.join(deps)}]" if deps else ""
    print(f"\n  Seeded idea: {title} (slug: {idea_slug}){dep_note}")


def _request_ideation(bus: MessageBus) -> None:
    """When master_ideas.md is exhausted, ask the Ideator to generate 30 new ideas.

    Scans all completed projects for context (master_plan.md + workspace file tree),
    reads reusable_tools.md, then sends a 'generate_ideas' message to the ideator.
    The runner will detect new unchecked items on its next tick and resume seeding.
    """
    pipeline_dir = PIPELINE_DIR
    projects_dir = pipeline_dir / "projects"

    # --- Gather completed/in-progress project context ---
    project_summaries: list[str] = []
    if projects_dir.exists():
        for proj_dir in sorted(projects_dir.iterdir()):
            if not proj_dir.is_dir():
                continue
            ci_path = proj_dir / "state" / "current_idea.json"
            if not ci_path.exists():
                continue
            try:
                ci = json.loads(ci_path.read_text(encoding="utf-8"))
                status = ci.get("status", "")
                title  = ci.get("title", proj_dir.name)
                slug   = ci.get("_slug", proj_dir.name)
                plan_path = proj_dir / "state" / "master_plan.md"
                plan_snippet = ""
                if plan_path.exists():
                    plan_snippet = plan_path.read_text(encoding="utf-8")[:600]
                # Workspace file tree (names only)
                ws_dir = proj_dir / "workspace"
                ws_files: list[str] = []
                if ws_dir.exists():
                    for f in sorted(ws_dir.rglob("*")):
                        if f.is_file() and "__pycache__" not in str(f):
                            ws_files.append(str(f.relative_to(ws_dir)))
                ws_tree = "\n    ".join(ws_files[:30]) or "(no workspace files yet)"
                project_summaries.append(
                    f"### {title} (slug={slug}, status={status})\n"
                    f"Workspace files:\n    {ws_tree}\n\n"
                    f"Plan:\n{plan_snippet}"
                )
            except Exception:
                continue

    # --- Existing master_ideas list (to avoid duplicates) ---
    mi_path = PROJECT_ROOT.resolve() / "master_ideas.md"
    existing_ideas = mi_path.read_text(encoding="utf-8") if mi_path.exists() else ""

    # --- Reusable tools ---
    tools_path = pipeline_dir / "state" / "reusable_tools.md"
    tools_content = tools_path.read_text(encoding="utf-8") if tools_path.exists() else "(none documented yet)"

    # --- Format spec ---
    format_spec = (
        "Each idea must be exactly one line in this format:\n"
        "  - [ ] **[Title]** — [One sentence description. requires: dep1, dep2 (only if needed)]\n"
        "The `requires:` part is optional — only add it if the idea genuinely depends on "
        "another project being completed first. Keep titles concise (3-7 words)."
    )

    projects_block = "\n\n".join(project_summaries) or "(no projects yet)"

    payload = {
        "type": "generate_ideas",
        "projects_context": projects_block[:8000],
        "existing_ideas": existing_ideas[:4000],
        "reusable_tools": tools_content[:2000],
        "format_spec": format_spec,
        "master_ideas_path": str(mi_path),
    }

    msg = Message.create(
        from_agent="runner",
        to_agent="ideator",
        type="generate_ideas",
        payload=payload,
    )
    bus.send(msg)
    print("\n  🧠 master_ideas.md exhausted — queued Ideator to generate 30 new ideas...")


# Return values for seed_from_master_list
_SEED_SEEDED  = "seeded"   # started a new project
_SEED_BLOCKED = "blocked"  # ideas exist but all deps pending — wait, don't ideate
_SEED_EMPTY   = "empty"    # list truly exhausted — safe to trigger ideation


def seed_from_master_list(
    bus: MessageBus,
    silent: bool = False,
    ideas_path: pathlib.Path | None = None,
    resume_inprogress: bool = False,
) -> str:
    """Find the first unchecked, unblocked idea in master_ideas.md and seed it.

    Dependency syntax (append to description):
        requires: slug_one, slug_two

    Example master_ideas.md line:
        - [ ] **[Movie idea generator]** — [generate movie ideas. requires: ai_movie_generation_suite]

    Blocked ideas (deps not yet complete) are skipped with a status message.
    They unblock automatically once their dependencies reach 'complete'.
    """
    mi_path = ideas_path if ideas_path else PROJECT_ROOT.resolve() / "master_ideas.md"
    if not mi_path.exists():
        print(f"  ✗ {mi_path.name} not found")
        return False

    import re
    content = mi_path.read_text(encoding="utf-8")
    blocked_count = 0

    for line in content.split("\n"):
        match = re.match(r"- \[ \]\s+\*\*(.+?)\*\*\s*[—–-]\s*(.*)", line)
        if not match:
            continue

        title = match.group(1).strip()
        if title in _seeded_this_session:
            continue

        slug = _slugify(title)
        project_state = PIPELINE_DIR / "projects" / slug / "state" / "current_idea.json"

        if project_state.exists():
            try:
                state = json.loads(project_state.read_text(encoding="utf-8"))
                status = state.get("status", "?")
                if status in ("complete", "budget_exceeded"):
                    # Locked projects with budget_exceeded get auto-reset and re-seeded
                    if status == "budget_exceeded" and state.get("budget_lock"):
                        resume_status = state.get("pre_budget_status", "phase_1_executing")
                        state["status"] = resume_status
                        state["budget_note"] = ""
                        state["session_started_at"] = ""  # reset timer
                        project_state.write_text(json.dumps(state, indent=2), encoding="utf-8")
                        print(f"  🔒 [LOCKED] '{title}' was budget_exceeded — auto-reset to {resume_status}")
                        # Fall through to dep check + re-queue below
                    else:
                        _seeded_this_session.add(title)
                        continue

                # --- Dep check for already-in-progress projects ---
                # If this project has deps that aren't done, put it in dep_waiting
                # and purge its queue messages so it doesn't run until deps finish.
                in_progress_deps = state.get("depends_on", [])
                if not in_progress_deps:
                    # Also try parsing from master_ideas line (for legacy projects
                    # seeded before stub-writing existed)
                    raw_desc = match.group(2).strip()
                    _dm = re.search(r'\brequires:\s*([\w,\s_-]+?)[\]\s.]*$', raw_desc, re.IGNORECASE)
                    if _dm:
                        in_progress_deps = [d.strip() for d in re.split(r'[,;]+', _dm.group(1)) if d.strip()]

                if in_progress_deps:
                    _blocking = []
                    DONE = ("complete", "budget_exceeded")
                    for _dep in in_progress_deps:
                        _df = PIPELINE_DIR / "projects" / _dep / "state" / "current_idea.json"
                        if not _df.exists():
                            _blocking.append(f"{_dep} (not started)")
                            continue
                        try:
                            _ds = json.loads(_df.read_text(encoding="utf-8"))
                            if _ds.get("status") not in DONE:
                                _blocking.append(f"{_dep} ({_ds.get('status','?')})")
                        except Exception:
                            _blocking.append(f"{_dep} (unreadable)")
                    if _blocking:
                        if status not in ("dep_waiting",):
                            state["pre_dep_status"] = status
                            state["status"] = "dep_waiting"
                            state["depends_on"] = in_progress_deps
                            project_state.write_text(json.dumps(state, indent=2), encoding="utf-8")
                        print(f"  ⏸  '{title}' dep_waiting — blocked by: {', '.join(_blocking)}")
                        _seeded_this_session.add(title)
                        blocked_count += 1
                        continue

                if status == "dep_waiting":
                    # Deps just became satisfied (handled above) — skip, rebuild will queue it
                    _seeded_this_session.add(title)
                    continue

                if resume_inprogress and status not in ("dep_waiting",):
                    # --fresh-list-only: queues were cleared, so re-queue this project
                    # by running a targeted rebuild for just this slug.
                    requeued = _rebuild_single_project(bus, slug, state, project_state.parent.parent)
                    if requeued:
                        print(f"  🔄 Re-queued '{title}' from list ({status})")
                        return _SEED_SEEDED
                    # If rebuild couldn't queue it (dep_waiting, etc.), fall through

                print(f"  ⏭  Skipping '{title}' — already in progress ({status}), resuming from queue")
                _seeded_this_session.add(title)
                return _SEED_SEEDED  # Work already exists — do NOT seed another project
            except Exception:
                pass  # Can't read state — seed it fresh

        description_raw = match.group(2).strip()
        # Strip outer brackets from description if present: [text] -> text
        if description_raw.startswith("[") and description_raw.endswith("]"):
            description_raw = description_raw[1:-1].strip()

        # --- Parse '[lock]' tag — prevents budget_exceeded from ever firing ---
        locked = bool(re.search(r'\[lock\]', description_raw, re.IGNORECASE))

        # --- Parse 'requires: slug1, slug2' dependency declarations ---
        # Handles trailing ] from markdown format e.g. [desc. requires: slug]
        dep_match = re.search(r'\brequires:\s*([\w,\s_-]+?)[\]\s.]*$', description_raw, re.IGNORECASE)
        deps: list = []
        description = re.sub(r'\s*\[lock\]', '', description_raw, flags=re.IGNORECASE).strip()
        if dep_match:
            raw_deps = dep_match.group(1)
            deps = [d.strip() for d in re.split(r'[,;]+', raw_deps) if d.strip()]
            description = description[:dep_match.start()].strip().rstrip('.')
            description = re.sub(r'\s*\[lock\]', '', description, flags=re.IGNORECASE).strip()

        # --- Check all dependencies are complete before seeding ---
        if deps:
            blocking: list = []
            for dep_slug in deps:
                dep_state_file = PIPELINE_DIR / "projects" / dep_slug / "state" / "current_idea.json"
                if not dep_state_file.exists():
                    blocking.append(f"{dep_slug} (not started)")
                    continue
                try:
                    dep_state = json.loads(dep_state_file.read_text(encoding="utf-8"))
                    if dep_state.get("status") not in ("complete", "budget_exceeded"):
                        blocking.append(f"{dep_slug} ({dep_state.get('status', '?')})")
                except Exception:
                    blocking.append(f"{dep_slug} (unreadable)")
            if blocking:
                blocked_count += 1
                print(f"  [blocked]  '{title}' blocked - waiting for: {', '.join(blocking)}")
                continue  # try the next idea in the list

        seed_idea(bus, title, description, deps=deps or None, locked=locked)
        return _SEED_SEEDED

    if blocked_count > 0:
        print(f"  [BLOCKED] {blocked_count} idea(s) blocked on dependencies -- will retry next tick")
        return _SEED_BLOCKED  # don't trigger ideation — deps will resolve
    elif not silent:
        print("  ✗ No unchecked ideas found in master_ideas.md")
    return _SEED_EMPTY


def check_resume(bus: MessageBus) -> bool:
    """Check if there's an active pipeline state to resume."""
    status = load_pipeline_status()
    if status.get("status") == "running":
        print(f"  🔄 Resuming pipeline (idea: {status.get('current_idea', '?')})")
        return True

    # Check if any queues have pending messages
    for role in AGENT_ROLES:
        if bus.queue_depth(role) > 0:
            print(f"  🔄 Found pending messages in {role} queue — resuming")
            return True

    return False

def _rebuild_single_project(bus: MessageBus, slug: str, state: dict, project_dir: pathlib.Path) -> bool:
    """Re-queue one specific in-progress project. Returns True if queued."""
    status = state.get("status", "")
    title  = state.get("title", slug)

    if status in ("", "complete", "budget_exceeded", "dep_waiting"):
        return False

    # Reset session budget timer
    _now = datetime.now(timezone.utc).isoformat()
    state["session_started_at"] = _now
    state.pop("budget_note", None)
    state_file = project_dir / "state" / "current_idea.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    if status == "planning":
        bus.send(Message.create(from_agent="runner", to_agent="idea_planner", type="task",
            payload={"title": title, "idea": state.get("description", title), "idea_slug": slug}))
        return True

    if not status.startswith("phase_"):
        return False

    phase_match = re.match(r"phase_(\d+)_(\w+)", status)
    if not phase_match:
        return False
    phase_num  = int(phase_match.group(1))
    phase_step = phase_match.group(2)

    tasks_path     = f"phases/phase_{phase_num}/tasks.md"
    workspace_path = str(project_dir / "workspace")
    report_path    = f"phases/phase_{phase_num}/validation_report.md"
    review_path    = f"phases/phase_{phase_num}/review.md"

    if phase_step == "planning":
        master_plan_file = project_dir / "state" / "master_plan.md"
        phase_spec = f"Resume phase {phase_num} of {title}"
        if master_plan_file.exists():
            try:
                mp = master_plan_file.read_text(encoding="utf-8")
                m = re.search(rf"## Phase {phase_num}\b[^\n]*\n.*?(?=## Phase \d|$)", mp, re.DOTALL | re.IGNORECASE)
                if m:
                    phase_spec = m.group(0)[:3000]
            except Exception:
                pass
        bus.send(Message.create(from_agent="runner", to_agent="phase_planner", type="task",
            payload={"phase": phase_num, "phase_spec": phase_spec, "idea_slug": slug}))
    elif phase_step == "executing":
        tasks_file_path = project_dir / tasks_path
        if not tasks_file_path.exists():
            ph_spec = f"Phase {phase_num} of project {slug}"
            mp_file = project_dir / "state" / "master_plan.md"
            if mp_file.exists():
                try:
                    mp_txt = mp_file.read_text(encoding="utf-8")
                    pm = re.search(rf"## Phase {phase_num}\b.*?(?=## Phase \d|$)", mp_txt, re.DOTALL | re.IGNORECASE)
                    if pm:
                        ph_spec = pm.group(0)
                except Exception:
                    pass
            _write_state(project_dir, state, f"phase_{phase_num}_planning")
            bus.send(Message.create(from_agent="runner", to_agent="phase_planner", type="task",
                payload={"phase": phase_num, "phase_spec": ph_spec[:3000], "idea_slug": slug}))
        else:
            bus.send(Message.create(from_agent="runner", to_agent="executor", type="task",
                payload={"phase": phase_num, "tasks_path": tasks_path,
                         "workspace_path": workspace_path, "idea_slug": slug}))
    elif phase_step == "validating":
        existing_report = ""
        report_file = project_dir / report_path
        if report_file.exists():
            try:
                existing_report = report_file.read_text(encoding="utf-8")[:3000]
            except Exception:
                pass
        has_failures = existing_report and "Verdict: PASS" not in existing_report
        bus.send(Message.create(from_agent="runner", to_agent="validator", type="task",
            payload={"phase": phase_num, "tasks_path": tasks_path, "workspace_path": workspace_path,
                     "validation_report_path": report_path, "idea_slug": slug,
                     "fix_required": has_failures, "validation_report": existing_report if has_failures else "",
                     "error_summary": "Re-queued by runner — continue fixing failures." if has_failures else ""}))
    elif phase_step == "reviewing":
        bus.send(Message.create(from_agent="runner", to_agent="reviewer", type="task",
            payload={"phase": phase_num, "tasks_path": tasks_path, "workspace_path": workspace_path,
                     "validation_report_path": report_path, "review_path": review_path, "idea_slug": slug}))
    elif phase_step == "reviewed":
        return bool(_tick_project(bus, project_dir, state, phase_num, slug))
    else:
        return False

    return True


def _rebuild_queues_from_state(bus: MessageBus, ideas_path: pathlib.Path | None = None) -> int:
    """Re-inject a queue message for ONE in-progress project that has no queued work.

    Called at startup and during the health-check loop when queues appear empty.
    Re-queues ONE project at a time (matching seed_from_master_list behaviour)
    so the pipeline works serially through incomplete projects rather than
    dumping all of them into the queue at once.

    Also enforces a wall-clock budget per project — any project that has been
    running longer than PROJECT_TIME_BUDGET minutes is force-completed.

    Returns the number of projects re-queued (0 or 1).
    """
    if bus.has_active_work():
        return 0  # Queues are already populated — nothing to rebuild

    projects_dir = PIPELINE_DIR / "projects"
    if not projects_dir.exists():
        return 0

    # ----------------------------------------------------------------
    # PRE-PASS: Unblock ALL dep_waiting projects whose deps are done.
    # This must run before the main requeue loop because the main loop
    # returns after processing ONE project — if a more-recently-touched
    # project is first, dep_waiting projects never get evaluated.
    # ----------------------------------------------------------------
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue
        state_file = project_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if state.get("status") != "dep_waiting":
            continue

        title = state.get("title", project_dir.name)
        deps = state.get("depends_on", [])

        # Re-parse deps from master_ideas.md (state may have stale deps from seed time)
        mi_path = ideas_path if ideas_path else PROJECT_ROOT / "master_ideas.md"
        if mi_path.exists():
            try:
                mi_text = mi_path.read_text(encoding="utf-8")
                _mi_title = state.get("title", "")
                if _mi_title:
                    for mi_line in mi_text.splitlines():
                        if _mi_title.strip("[]") in mi_line:
                            _dm = re.search(r'\brequires:\s*([\w,\s_-]+?)[\]\s.]*$', mi_line, re.IGNORECASE)
                            if _dm:
                                fresh_deps = [d.strip() for d in re.split(r'[,;]+', _dm.group(1)) if d.strip()]
                                if set(fresh_deps) != set(deps):
                                    print(f"  🔄 Updated deps for '{title}': {deps} → {fresh_deps}")
                                    deps = fresh_deps
                                    state["depends_on"] = deps
                            break
            except Exception:
                pass

        DONE = ("complete",)  # budget_exceeded does NOT satisfy a dep — the
        # prereq must have actually finished. If it only hit budget, the dependent
        # project stays blocked and waits for the prereq to be retried.
        still_blocked = [
            d for d in deps
            if not (projects_dir / d / "state" / "current_idea.json").exists()
            or (
                (projects_dir / d / "state" / "current_idea.json").exists()
                and json.loads((projects_dir / d / "state" / "current_idea.json")
                              .read_text(encoding="utf-8")).get("status") not in DONE
            )
        ]
        if still_blocked:
            continue  # still waiting

        # All deps done — restore last real phase status
        new_status = state.get("pre_dep_status", "phase_1_executing")
        state["status"] = new_status
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        print(f"  ✅ '{title}' deps satisfied — resuming from {new_status}")

    # ----------------------------------------------------------------
    # MAIN LOOP: Find the most-recently-active incomplete project and
    # requeue it. Only ONE project at a time.
    # ----------------------------------------------------------------
    injected = 0
    def _project_recency(d: pathlib.Path) -> float:
        sf = d / "state" / "current_idea.json"
        try:
            s = json.loads(sf.read_text(encoding="utf-8"))
            return -datetime.fromisoformat(s.get("started_at", "2000-01-01T00:00:00+00:00")).timestamp()
        except Exception:
            return 0.0
    for project_dir in sorted(projects_dir.iterdir(), key=_project_recency):
        if not project_dir.is_dir():
            continue

        state_file = project_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue

        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        status = state.get("status", "")
        title  = state.get("title", project_dir.name)
        slug   = project_dir.name

        if status in ("", "complete", "budget_exceeded", "dep_waiting"):
            continue

        # --- Budget enforcement: ALWAYS reset session_started_at on requeue ---
        # This is a NEW runner session — any stale session_started_at from a
        # previous run would cause instant budget_exceeded (e.g. 5000+ min elapsed).
        state["session_started_at"] = datetime.now(timezone.utc).isoformat()
        # Also set started_at if missing (legacy projects)
        if not state.get("started_at"):
            state["started_at"] = state["session_started_at"]
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


        # Skip projects whose validator has already hit the stall limit —
        # these should have been force-advanced by the manager, but if the
        # manager message was lost, don't loop forever on the same project.
        retries_file = project_dir / "state" / "phase_retries.json"
        if retries_file.exists():
            try:
                retries = json.loads(retries_file.read_text(encoding="utf-8"))
                # Check for any no_progress streak >= 4 (our stall limit)
                # BUT respect budget_lock: locked projects are never force-completed
                _is_locked = state.get("budget_lock", False)
                for k, v in retries.items():
                    if "no_progress" in k and isinstance(v, int) and v >= 4 and not _is_locked:
                        # Force-mark as budget_exceeded (NOT complete) so [lock] can recover it
                        state["status"] = "budget_exceeded"
                        state["budget_note"] = f"Stalled: no_progress streak {v} cycles on {k}"
                        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
                        print(f"  ⏭️  Stall-stopped project '{title}' (stuck {v} cycles) → budget_exceeded")
                        break
                else:
                    retries = None  # didn't break — not stalled
                if state.get("status") == "budget_exceeded":
                    continue
            except Exception:
                pass

        # --- Dependency check: don't re-queue if deps aren't done yet ---
        depends_on = state.get("depends_on", [])
        if depends_on:
            dep_blocked = []
            DONE_STATUSES = ("complete",)  # budget_exceeded is NOT a satisfied dep
            for dep_slug in depends_on:
                dep_file = projects_dir / dep_slug / "state" / "current_idea.json"
                if not dep_file.exists():
                    dep_blocked.append(f"{dep_slug} (not started)")
                    continue
                try:
                    dep_st = json.loads(dep_file.read_text(encoding="utf-8"))
                    if dep_st.get("status") not in DONE_STATUSES:
                        dep_blocked.append(f"{dep_slug} ({dep_st.get('status','?')})")
                except Exception:
                    dep_blocked.append(f"{dep_slug} (unreadable)")
            if dep_blocked:
                print(f"  ⏸  '{title}' dep_waiting — blocked by: {', '.join(dep_blocked)}")
                continue  # don't re-queue until deps are finished

        phase_match = re.match(r"phase_(\d+)_(\w+)", status)
        if phase_match:
            phase_num  = int(phase_match.group(1))
            phase_step = phase_match.group(2)

            # --- Retroactive format normalization ---
            # Normalize task formatting for backward compatibility (## Task N: → - [ ] Task N:)
            # NOTE: no longer trims oversized tasks — the phase_planner handles overflow
            # with the planner-chooses system (restructure/split/trim).
            tasks_file = project_dir / f"phases/phase_{phase_num}/tasks.md"
            if tasks_file.exists():
                try:
                    from pipeline.agent_process import AgentProcess
                    AgentProcess.normalize_tasks_file(tasks_file)
                except Exception:
                    pass


        # Always refresh timestamps when re-queuing — budget is per-session,
        # not total project lifetime. Without this, a manually-reset project
        # or one from a previous session fires budget_exceeded immediately.
        _now = datetime.now(timezone.utc).isoformat()
        state["started_at"] = _now
        state["session_started_at"] = _now  # MUST also reset this — budget enforcement reads it first
        state.pop("budget_note", None)
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        if status == "planning":
            # Was in initial idea planning — restart from idea_planner
            msg = Message.create(
                from_agent="runner",
                to_agent="idea_planner",
                type="task",
                payload={
                    "title": title,
                    "idea": state.get("description", title),
                    "idea_slug": slug,
                },
            )
            bus.send(msg)
            injected += 1
            print(f"  🔁 Re-queued '{title}' → idea_planner (was: planning)")
            continue
        elif not status.startswith("phase_"):
            continue  # Unknown status — skip


        tasks_path     = f"phases/phase_{phase_num}/tasks.md"
        workspace_path = str(project_dir / "workspace")
        report_path    = f"phases/phase_{phase_num}/validation_report.md"
        review_path    = f"phases/phase_{phase_num}/review.md"

        # Route to the correct agent based on phase step
        if phase_step == "planning":
            # phase_planner was building the task list — extract specific phase section
            master_plan_file = project_dir / "state" / "master_plan.md"
            phase_spec = f"Resume phase {phase_num} of {title}"
            if master_plan_file.exists():
                try:
                    mp = master_plan_file.read_text(encoding="utf-8")
                    m = re.search(rf"## Phase {phase_num}\b[^\n]*\n.*?(?=## Phase \d|$)",
                                  mp, re.DOTALL | re.IGNORECASE)
                    if m:
                        phase_spec = m.group(0)[:3000]
                except Exception:
                    pass
            agent    = "phase_planner"
            payload  = {"phase": phase_num, "phase_spec": phase_spec, "idea_slug": slug}
        elif phase_step == "executing":
            # Don't re-queue if workspace files were written in last 10 min —
            # the executor may still be mid-run (acked msg but writing files).
            workspace_dir = project_dir / "workspace"
            recently_active = False
            if workspace_dir.exists():
                cutoff = time.time() - 600  # 10 minutes
                for _root, _, _files in os.walk(str(workspace_dir)):
                    if recently_active:
                        break
                    for _fn in _files:
                        if _fn.endswith((".py", ".md", ".json", ".yaml")):
                            try:
                                if os.path.getmtime(os.path.join(_root, _fn)) > cutoff:
                                    recently_active = True
                                    break
                            except OSError:
                                pass
            if recently_active:
                print(f"  \u23f3 '{title}' executor active recently — skipping re-queue")
                continue
            # Guard: if tasks.md is missing, re-route to phase_planner
            tasks_file_path = project_dir / tasks_path
            if not tasks_file_path.exists():
                mp_file = project_dir / "state" / "master_plan.md"
                ph_spec = f"Phase {phase_num} of project {slug}"
                if mp_file.exists():
                    try:
                        mp_txt = mp_file.read_text(encoding="utf-8")
                        pm = re.search(
                            rf"## Phase {phase_num}\b.*?(?=## Phase \d|$)",
                            mp_txt, re.DOTALL | re.IGNORECASE)
                        if pm:
                            ph_spec = pm.group(0)
                    except Exception:
                        pass
                _write_state(project_dir, state, f"phase_{phase_num}_planning")
                print(f"  \U0001f4cb '{title}' missing tasks.md \u2192 re-routing to phase_planner")
                agent   = "phase_planner"
                payload = {"phase": phase_num, "phase_spec": ph_spec[:3000], "idea_slug": slug}
            else:
                agent   = "executor"
                payload = {"phase": phase_num, "tasks_path": tasks_path,
                           "workspace_path": workspace_path, "idea_slug": slug}


        elif phase_step == "validating":
            agent = "validator"
            # Check if there's an existing failed report — if so, treat this as a
            # fix_required re-queue so the validator's retry/no-progress counter
            # doesn't reset (the runner re-queue was resetting it each time).
            existing_report = ""
            report_file = project_dir / report_path
            if report_file.exists():
                try:
                    existing_report = report_file.read_text(encoding="utf-8")[:3000]
                except Exception:
                    pass
            has_failures = existing_report and "Verdict: PASS" not in existing_report
            payload = {
                "phase": phase_num,
                "tasks_path": tasks_path,
                "workspace_path": workspace_path,
                "validation_report_path": report_path,
                "idea_slug": slug,
                # Preserve retry context so validator doesn't treat this as fresh start
                "fix_required": has_failures,
                "validation_report": existing_report if has_failures else "",
                "error_summary": "Re-queued by runner after stall detection — continue fixing failures." if has_failures else "",
            }
        elif phase_step == "reviewing":
            agent   = "reviewer"
            payload = {"phase": phase_num, "tasks_path": tasks_path,
                       "workspace_path": workspace_path,
                       "validation_report_path": report_path,
                       "review_path": review_path, "idea_slug": slug}
        elif phase_step == "reviewed":
            # Reviewer finished — deterministic routing via _tick_project
            routed = _tick_project(bus, project_dir, state, phase_num, slug)
            if routed:
                return 1
            continue
        else:
            continue  # Unknown step

        bus.send(Message.create(from_agent="runner", to_agent=agent,
                                type="task", payload=payload))
        print(f"  🔁 Re-queued '{title}' → {agent} (was: {status})")
        return 1  # One at a time — next project picked up after this one completes

    # -----------------------------------------------------------------
    # RECOVERY: If we found nothing to run, check whether ALL remaining
    # blocked projects are waiting exclusively on budget_exceeded prereqs.
    # In that case, reset those prereqs so they can be retried rather than
    # generating new ideas or starting dependents without their prereq.
    # -----------------------------------------------------------------
    blocked_by_budget: dict[str, list[str]] = {}  # prereq_slug -> [waiters]
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue
        state_file = project_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if state.get("status") != "dep_waiting":
            continue
        title = state.get("title", project_dir.name)
        deps  = state.get("depends_on", [])
        for dep_slug in deps:
            dep_file = projects_dir / dep_slug / "state" / "current_idea.json"
            if not dep_file.exists():
                continue
            try:
                dep_state = json.loads(dep_file.read_text(encoding="utf-8"))
                if dep_state.get("status") == "budget_exceeded":
                    blocked_by_budget.setdefault(dep_slug, []).append(title)
            except Exception:
                pass

    if blocked_by_budget:
        now = datetime.now(timezone.utc).isoformat()
        for dep_slug, waiters in blocked_by_budget.items():
            dep_file = projects_dir / dep_slug / "state" / "current_idea.json"
            try:
                dep_state = json.loads(dep_file.read_text(encoding="utf-8"))
                # Restore where the project was before it hit budget
                pre_status = dep_state.get("pre_budget_status", "phase_1_executing")
                dep_state["status"]            = pre_status
                dep_state["session_started_at"] = now
                dep_state["started_at"]         = now
                dep_state.pop("budget_note", None)
                dep_file.write_text(json.dumps(dep_state, indent=2), encoding="utf-8")
                print(
                    f"  🔄 Resetting budget_exceeded prereq '{dep_slug}' → {pre_status} "
                    f"(required by: {', '.join(waiters)})"
                )
            except Exception:
                pass
        # Re-run one more time so the now-unblocked prereq gets queued
        return _rebuild_queues_from_state(bus, ideas_path)

    return 0  # No incomplete projects found


# Maximum reviewer->executor round-trips per phase before force-advancing
# 5 attempts = ~25-35 min max per stuck phase (saves 40+ min vs old limit of 12)
MAX_PHASE_RETRIES = 5


def _tick_project(
    bus: MessageBus,
    project_dir: pathlib.Path,
    state: dict,
    phase_num: int,
    slug: str,
) -> bool:
    """Deterministic state machine tick for a reviewed project.

    Reads the reviewer's verdict from current_idea.json and routes:
    - 0 blocking bugs → advance to next phase (or complete)
    - Blocking bugs → send back to executor (up to MAX_PHASE_RETRIES)
    - Emergency (architectural issues) → re-plan the phase

    Returns True if a message was sent, False if nothing to do.
    """
    review = state.get("review_result", {})
    blocking_bugs = review.get("blocking_bugs", 0)
    review_content = review.get("review_content_preview", "")
    non_blocking_notes = review.get("non_blocking_notes", "")
    tasks_path = review.get("tasks_path", f"phases/phase_{phase_num}/tasks.md")
    workspace_path = review.get("workspace_path", str(project_dir / "workspace"))
    review_path = review.get("review_path", f"phases/phase_{phase_num}/review.md")
    title = state.get("title", slug)

    # Check for emergency rework indicators
    rework_indicators = sum(1 for word in ["fundamental", "architectural",
                                            "completely wrong", "redesign",
                                            "start over", "rewrite"]
                            if word in review_content.lower())
    is_emergency = rework_indicators >= 3 or blocking_bugs > 5

    # Cap emergency reworks — after 2, fall through to normal fix path
    MAX_EMERGENCY_REWORKS = 2
    emergency_count = 0
    retries_file = project_dir / "state" / "phase_retries.json"
    if retries_file.exists():
        try:
            _rd = json.loads(retries_file.read_text(encoding="utf-8"))
            emergency_count = _rd.get(f"phase_{phase_num}_emergency", 0)
        except Exception:
            pass

    if is_emergency and emergency_count < MAX_EMERGENCY_REWORKS:
        # EMERGENCY REWORK — re-plan the phase with actual review content
        review_full_path = project_dir / review_path if review_path else None
        review_text = ""
        if review_full_path and review_full_path.exists():
            try:
                review_text = review_full_path.read_text(encoding="utf-8")[:4000]
            except Exception:
                pass

        # Read master plan section for this phase
        master_plan_section = ""
        mp_file = project_dir / "state" / "master_plan.md"
        if mp_file.exists():
            try:
                mp = mp_file.read_text(encoding="utf-8")
                m = re.search(rf"## Phase {phase_num}\b[^\n]*\n.*?(?=## Phase \d|$)",
                              mp, re.DOTALL | re.IGNORECASE)
                if m:
                    master_plan_section = m.group(0)[:2000]
            except Exception:
                pass

        bus.send(Message.create(
            from_agent="runner",
            to_agent="phase_planner",
            type="task",
            payload={
                "phase": phase_num,
                "phase_spec": (
                    f"REWORK REQUIRED for phase {phase_num} (attempt {emergency_count + 1}/{MAX_EMERGENCY_REWORKS}).\n\n"
                    f"## Original Phase Goal\n{master_plan_section}\n\n"
                    f"## Reviewer Feedback (fix these issues):\n{review_text}\n"
                ),
                "is_rework": True,
                "idea_slug": slug,
            },
            priority=0,
        ))
        # Track emergency count
        _rd = {}
        if retries_file.exists():
            try:
                _rd = json.loads(retries_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        _rd[f"phase_{phase_num}_emergency"] = emergency_count + 1
        retries_file.parent.mkdir(parents=True, exist_ok=True)
        retries_file.write_text(json.dumps(_rd, indent=2), encoding="utf-8")

        # Update status
        _write_state(project_dir, state, f"phase_{phase_num}_planning")
        print(f"  🚨 Emergency rework for '{title}' phase {phase_num} (attempt {emergency_count + 1}/{MAX_EMERGENCY_REWORKS})")
        return True

    elif is_emergency and emergency_count >= MAX_EMERGENCY_REWORKS:
        # Emergency cap hit — demote to normal fix path (blocking_bugs > 0 branch below)
        print(f"  ⚠️  Emergency cap hit for '{title}' phase {phase_num} — switching to incremental fix path")
        blocking_bugs = max(blocking_bugs, 1)  # ensure we enter the fix path

    if blocking_bugs > 0:
        # Increment retry counter
        retries = _increment_retries(project_dir, phase_num)

        if retries >= MAX_PHASE_RETRIES:
            # Too many retries — force-advance
            print(f"  ⚠️  Force-advancing '{title}' phase {phase_num} after {retries} retries ({blocking_bugs} bugs remain)")
            _reset_retries(project_dir, phase_num)
            advanced = _advance_phase(bus, project_dir, state, phase_num, slug)
            if not advanced:
                _mark_complete(project_dir, state, title)
                print(f"  ✅ '{title}' completed all phases (force-advanced past last phase)!")
            return True
        else:
            # Send back to executor with fix instructions
            review_full = str(project_dir / review_path) if review_path else ""
            bus.send(Message.create(
                from_agent="runner",
                to_agent="executor",
                type="task",
                payload={
                    "phase": phase_num,
                    "tasks_path": tasks_path,
                    "workspace_path": workspace_path,
                    "fix_required": True,
                    "review_path": review_path,
                    "blocking_bugs": blocking_bugs,
                    "fix_instructions": (
                        f"Fix {blocking_bugs} blocking bugs from review (attempt {retries}/{MAX_PHASE_RETRIES}). "
                        f"Read `{review_full}` for details."
                    ),
                    "idea_slug": slug,
                },
            ))
            _write_state(project_dir, state, f"phase_{phase_num}_executing")
            print(f"  🔧 '{title}' phase {phase_num}: {blocking_bugs} bugs → executor (retry {retries}/{MAX_PHASE_RETRIES})")
            return True
    else:
        # Clean pass — save non-blocking notes, advance or complete
        if non_blocking_notes:
            _append_polish(project_dir, phase_num, non_blocking_notes)

        # --- Extract reusable components from review (no LLM needed) ---
        _extract_shared_libs(project_dir, review_path, workspace_path, title)

        _reset_retries(project_dir, phase_num)

        advanced = _advance_phase(bus, project_dir, state, phase_num, slug)
        if not advanced:
            _mark_complete(project_dir, state, title)
            print(f"  ✅ '{title}' completed all phases!")
        else:
            print(f"  ➡️  '{title}' phase {phase_num} passed → advancing to phase {phase_num + 1}")

        return True



def _extract_shared_libs(
    project_dir: pathlib.Path,
    review_path: str,
    workspace_path: str,
    title: str,
) -> None:
    """Post-hook: parse ## Reusable Components from review.md and copy files
    to .pipeline/shared_libs/ + append to reusable_tools.md.

    Runs after every clean reviewer pass — no LLM budget needed.
    The reviewer LLM only needs to LIST components; we handle file copying.
    """
    import re as _re
    import shutil as _shutil

    run_dir   = project_dir.parent.parent.parent  # .pipeline/projects/slug -> idea impl/
    shared    = run_dir / ".pipeline" / "shared_libs"
    tools_log = run_dir / ".pipeline" / "state" / "reusable_tools.md"
    review_full = project_dir / review_path

    if not review_full.exists():
        return
    try:
        review_text = review_full.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return

    # Extract the ## Reusable Components section (handles bold: **Reusable Components**)
    m = _re.search(
        r"(?:##\s*\*{0,2}Reusable Components\*{0,2})(.*?)(?=\n##\s|\Z)",
        review_text, _re.DOTALL | _re.IGNORECASE,
    )
    if not m:
        return
    section = m.group(1).strip()
    if not section or _re.search(r"\b(none|n/a|nothing)\b", section, _re.IGNORECASE):
        return

    ws_path = pathlib.Path(workspace_path) if workspace_path else project_dir / "workspace"
    extracted: list[str] = []

    for line in section.splitlines():
        line = line.strip()
        # Strip bullet markers: "- ", "* ", "1. ", "2. " etc.
        line = _re.sub(r"^[-*\d]+[.)]\s*", "", line).strip()
        if not line or len(line) < 8:
            continue

        # Strip leading backticks/code spans for the name
        clean = _re.sub(r"`([^`]+)`", r"\1", line)

        # Derive a safe component name from the first word/phrase before : or —
        first_part = _re.split(r"[:\s—–]", clean)[0].strip().lower()
        component_name = _re.sub(r"[^a-z0-9_]", "_", first_part).strip("_")[:40]
        if not component_name or len(component_name) < 2:
            continue

        # Find any .py file references in the bullet line
        file_refs = _re.findall(r"`([^`]+\.py)`|([\w./]+\.py)", line)
        dest_dir = shared / component_name
        copied = 0

        for ref_tuple in file_refs:
            ref = (ref_tuple[0] or ref_tuple[1]).lstrip("/")
            candidates = [
                ws_path / ref,
                ws_path / pathlib.Path(ref).name,
                *list(ws_path.rglob(pathlib.Path(ref).name)),
            ]
            for candidate in candidates:
                if candidate.exists() and candidate.is_file():
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    _shutil.copy2(candidate, dest_dir / candidate.name)
                    copied += 1
                    break

        # Log entry whether or not we found the file — metadata is still useful
        desc = line[:120]
        log_entry = f"- {component_name}: {desc} (source: {title})\n"
        tools_log.parent.mkdir(parents=True, exist_ok=True)
        existing = tools_log.read_text(encoding="utf-8") if tools_log.exists() else ""
        if component_name not in existing:
            with tools_log.open("a", encoding="utf-8") as f:
                f.write(log_entry)
            extracted.append(component_name)

    if extracted:
        print(f"  [shared_libs] {len(extracted)} component(s) from '{title}': {', '.join(extracted)}")


def _advance_phase(
    bus: MessageBus,
    project_dir: pathlib.Path,
    state: dict,
    completed_phase: int,
    slug: str,
) -> bool:
    """Advance to next phase if one exists. Returns True if advanced.

    Checks for overflow tasks first — if phase N had >8 tasks split into
    batches, the overflow runs before advancing to phase N+1.
    """
    # --- Overflow check: run batch 2 before advancing ---
    overflow_tasks_path = project_dir / f"phases/phase_{completed_phase}_overflow/tasks.md"
    overflow_done_marker = project_dir / f"phases/phase_{completed_phase}_overflow/.completed"
    if overflow_tasks_path.exists() and not overflow_done_marker.exists():
        # Overflow tasks exist and haven't been completed yet — queue them
        workspace = project_dir / "workspace"
        state["status"] = f"phase_{completed_phase}_executing"
        state.pop("review_result", None)
        _write_state_dict(project_dir, state)

        # Mark that we're in overflow mode so we don't loop
        overflow_done_marker.parent.mkdir(parents=True, exist_ok=True)

        bus.send(Message.create(
            from_agent="runner",
            to_agent="executor",
            type="task",
            payload={
                "phase": completed_phase,
                "tasks_path": f"phases/phase_{completed_phase}_overflow/tasks.md",
                "workspace_path": str(workspace),
                "idea_slug": slug,
                "is_overflow": True,
            },
        ))
        title = state.get("title", slug)
        print(f"  📦 '{title}' phase {completed_phase} overflow: queuing batch 2 tasks")
        return True

    # If overflow was just completed, mark it and continue to next phase
    if overflow_done_marker.exists():
        # Mark overflow as done for this phase
        try:
            overflow_done_marker.write_text("completed", encoding="utf-8")
        except Exception:
            pass

    next_phase = completed_phase + 1

    # --- Primary check: master_plan.md has a ## Phase N heading ---
    phase_found_in_plan = False
    phase_spec = f"Phase {next_phase} of project {slug}"
    master_plan_file = project_dir / "state" / "master_plan.md"
    if master_plan_file.exists():
        try:
            master_plan = master_plan_file.read_text(encoding="utf-8")
            pattern = rf"## Phase {next_phase}\b"
            if re.search(pattern, master_plan, re.IGNORECASE):
                phase_found_in_plan = True
                phase_pattern = rf"(## Phase {next_phase}\b[^\n]*\n)(.*?)(?=## Phase \d|$)"
                match = re.search(phase_pattern, master_plan, re.DOTALL | re.IGNORECASE)
                if match:
                    phase_spec = match.group(0)
        except Exception:
            pass

    # --- REMOVED: total_phases fallback ---
    # Previously we trusted state["total_phases"] as a fallback when the master
    # plan didn't have a ## Phase N heading. This caused phantom phases (7-9)
    # with generic boilerplate tasks when total_phases > actual plan headings.
    # Now only master_plan.md headings determine available phases.

    if not phase_found_in_plan:
        return False  # No more phases

    # Update state
    state["status"] = f"phase_{next_phase}_planning"
    state["phase"] = next_phase
    state.pop("review_result", None)  # Clear stale review data
    _write_state_dict(project_dir, state)

    # Write spec.md so the agent always has full context on disk
    spec_dir = project_dir / f"phases/phase_{next_phase}"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_file = spec_dir / "spec.md"
    if phase_spec and not spec_file.exists():
        try:
            spec_file.write_text(phase_spec, encoding="utf-8")
        except Exception:
            pass

    # Send to phase planner
    bus.send(Message.create(
        from_agent="runner",
        to_agent="phase_planner",
        type="task",
        payload={
            "phase": next_phase,
            "phase_spec": phase_spec[:3000],
            "idea_slug": slug,
        },
    ))
    return True


def _mark_complete(project_dir: pathlib.Path, state: dict, title: str, ideas_path: pathlib.Path | None = None) -> None:
    """Mark a project as complete in both state file and master_ideas.md."""
    state["status"] = "complete"
    state.pop("review_result", None)
    _write_state_dict(project_dir, state)
    print(f"  ✅ '{title}' completed all phases!")

    # Mark in master_ideas.md
    mi_path = ideas_path if ideas_path else PROJECT_ROOT / "master_ideas.md"
    if mi_path.exists() and title:
        content = mi_path.read_text(encoding="utf-8")
        # Handle both [title] and title formats
        clean_title = title.strip("[]")
        updated = content.replace(f"- [ ] **{title}**", f"- [x] **{title}**")
        if updated == content:
            updated = content.replace(f"- [ ] **[{clean_title}]**", f"- [x] **[{clean_title}]**")
        if updated != content:
            mi_path.write_text(updated, encoding="utf-8")


def _write_state(project_dir: pathlib.Path, state: dict, new_status: str) -> None:
    """Update status in current_idea.json."""
    state["status"] = new_status
    state.pop("review_result", None)
    _write_state_dict(project_dir, state)


def _write_state_dict(project_dir: pathlib.Path, state: dict) -> None:
    """Write state dict to disk."""
    state_file = project_dir / "state" / "current_idea.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _increment_retries(project_dir: pathlib.Path, phase_num: int) -> int:
    """Increment and return the retry count for a phase."""
    retries_file = project_dir / "state" / "phase_retries.json"
    try:
        data = json.loads(retries_file.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    key = f"phase_{phase_num}"
    data[key] = data.get(key, 0) + 1
    retries_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data[key]


def _reset_retries(project_dir: pathlib.Path, phase_num: int) -> None:
    """Reset retry counter for a phase."""
    retries_file = project_dir / "state" / "phase_retries.json"
    try:
        data = json.loads(retries_file.read_text(encoding="utf-8"))
        data.pop(f"phase_{phase_num}", None)
        retries_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _append_polish(project_dir: pathlib.Path, phase_num: int, notes: str) -> None:
    """Save non-blocking review notes as deferred polish tasks."""
    path = PIPELINE_DIR / "state" / "plan_amendments.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    bullets = re.findall(r'^[-*]\s+(.+)$', notes, re.MULTILINE)
    if not bullets:
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n### Phase {phase_num} Polish Items\n")
        for b in bullets:
            f.write(f"- [ ] (polish) {b}\n")


def _run_polish_mode(
    bus: "MessageBus",
    ideas_path: pathlib.Path | None = None,
) -> int:
    """Process polish_queue.md — resume complete projects that have missing phases.

    Reads polish_queue.md (same `- [ ] **[Title]** — notes` format).
    For each unchecked entry whose slug is 'complete', resets its state to
    the next unfinished phase so the normal run_pipeline loop can continue it.

    Returns the number of projects re-queued.
    """
    import re
    polish_path = ideas_path or (PROJECT_ROOT.resolve() / "polish_queue.md")
    if not polish_path.exists():
        print(f"  [polish] {polish_path.name} not found — creating template...")
        _write_polish_queue_template(polish_path)
        print(f"  [polish] Wrote template to {polish_path}")
        print(f"  [polish] Edit polish_queue.md then re-run with --polish")
        return 0

    content = polish_path.read_text(encoding="utf-8")
    queued = 0
    projects_dir = PIPELINE_DIR / "projects"

    for line in content.splitlines():
        match = re.match(r"- \[ \]\s+\*\*(.+?)\*\*\s*[—–-]\s*(.*)", line)
        if not match:
            continue
        raw_title = match.group(1).strip().strip("[]")
        notes = match.group(2).strip()
        slug = _slugify(raw_title)

        state_file = projects_dir / slug / "state" / "current_idea.json"
        if not state_file.exists():
            print(f"  [polish] SKIP '{raw_title}' — no project state found (slug: {slug})")
            continue

        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [polish] SKIP '{raw_title}' — unreadable state: {e}")
            continue

        current_status = state.get("status", "")
        current_phase  = state.get("phase", 1)
        total_phases   = state.get("total_phases", 1)

        if current_status not in ("complete", "budget_exceeded"):
            print(f"  [polish] SKIP '{raw_title}' — status is '{current_status}' (not complete/budget_exceeded)")
            continue

        # Determine which phase to resume from
        next_phase = int(current_phase) + 1 if current_status == "complete" else int(current_phase)
        if next_phase > int(total_phases):
            print(f"  [polish] SKIP '{raw_title}' — already at max phase ({current_phase}/{total_phases})")
            continue

        # Reset state to target phase
        resume_status = f"phase_{next_phase}_planning"
        state["status"] = resume_status
        state["session_started_at"] = datetime.now(timezone.utc).isoformat()
        state.pop("budget_note", None)
        state.pop("pre_budget_status", None)
        if notes:
            state["polish_notes"] = notes
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        # Queue to phase_planner
        master_plan_file = projects_dir / slug / "state" / "master_plan.md"
        phase_spec = f"Polish resume: phase {next_phase} of {raw_title}. {notes}"
        if master_plan_file.exists():
            try:
                mp = master_plan_file.read_text(encoding="utf-8")
                m = re.search(rf"## Phase {next_phase}\b[^\n]*\n.*?(?=## Phase \d|$)",
                              mp, re.DOTALL | re.IGNORECASE)
                if m:
                    phase_spec = m.group(0)[:3000]
            except Exception:
                pass

        msg = Message.create(
            from_agent="runner",
            to_agent="phase_planner",
            type="task",
            payload={"phase": next_phase, "phase_spec": phase_spec, "idea_slug": slug},
        )
        bus.send(msg)
        print(f"  [polish] Queued '{raw_title}' → phase_{next_phase}_planning (was {current_status} p{current_phase}/{total_phases})")
        _seeded_this_session.add(raw_title)
        queued += 1

    if queued == 0:
        print("  [polish] Nothing to polish — all entries already done or missing.")
    return queued


def _write_polish_queue_template(path: pathlib.Path) -> None:
    """Write a starter polish_queue.md with projects that have missing phases."""
    projects_dir = PIPELINE_DIR / "projects"
    lines = [
        "# Polish Queue",
        "",
        "Projects marked complete but with missing phases.",
        "The --polish flag resumes them from their last completed phase.",
        "Format: `- [ ] **[project-slug]** — notes about what to add`",
        "",
    ]
    if projects_dir.exists():
        for proj_dir in sorted(projects_dir.iterdir()):
            if not proj_dir.is_dir():
                continue
            sf = proj_dir / "state" / "current_idea.json"
            if not sf.exists():
                continue
            try:
                s = json.loads(sf.read_text(encoding="utf-8"))
                status = s.get("status", "")
                phase  = s.get("phase", 1)
                total  = s.get("total_phases", 1)
                title  = s.get("title", proj_dir.name)
                if status in ("complete", "budget_exceeded") and int(phase) < int(total):
                    lines.append(
                        f"- [ ] **[{proj_dir.name}]** — "
                        f"p{phase}/{total} {status}. Continue phases {int(phase)+1}-{total}. Original title: {title[:50]}"
                    )
            except Exception:
                continue
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pipeline(
    idea: str | None = None,
    from_list: bool = False,
    resume: bool = False,
    provider: str = "ollama",
    model: str = os.environ.get("PIPELINE_MODEL", "qwen3.5:35b"),
    time_limit_minutes: float = 0,
    base_budget: int = DEFAULT_BASE_BUDGET,
    phase_budget: int = DEFAULT_PHASE_BUDGET,
    ideas_file: str | None = None,
    fresh_list_only: bool = False,
    polish: bool = False,
    parallel_seeds: int = 1,
    auto_tune: bool = False,
    max_seeds: int = 4,
) -> None:
    """Main pipeline orchestrator."""
    # Override master ideas path if --ideas-file was given
    global PROJECT_ROOT
    _ideas_path = pathlib.Path(ideas_file).resolve() if ideas_file else PROJECT_ROOT.resolve() / "master_ideas.md"
    if ideas_file:
        print(f"  Ideas:    {_ideas_path}")
    init_pipeline_dirs()
    bus = MessageBus()

    # One-shot migration: import any legacy JSONL queue files into SQLite.
    # Safe to call every startup — INSERT OR IGNORE skips already-imported msgs.
    try:
        _migrated = bus.migrate_from_jsonl()
        if _migrated:
            print(f"  🗄️  Migrated {_migrated} legacy queue message(s) to SQLite bus")
    except Exception:
        pass

    print("=" * 60)
    print("  🏭 Idea Development Pipeline")
    print("=" * 60)
    print(f"  Provider: {provider}")
    print(f"  Model:    {model}")
    if time_limit_minutes > 0:
        print(f"  Time:     {time_limit_minutes:.0f} minutes")
    else:
        print(f"  Time:     unlimited")
    print(f"  Agents:   {len(AGENT_ROLES)}")
    print(f"  Budget:   {base_budget}min base, {phase_budget}min/phase")
    if fresh_list_only:
        print(f"  Mode:     FRESH LIST ONLY — skipping all stray/in-progress projects")
    if polish:
        print(f"  Mode:     POLISH - resuming complete projects with missing phases")
    if auto_tune:
        print(f"  Seeds:    auto-tune ON (start={parallel_seeds}, max={max_seeds})")
    elif parallel_seeds > 1:
        print(f"  Seeds:    {parallel_seeds} parallel project slots (Strategy 6)")

    # Polish mode: reset complete-but-incomplete projects and queue them, then
    # fall through to normal pipeline startup so agents actually process them.
    if polish:
        _polish_path = pathlib.Path(ideas_file).resolve() if ideas_file else PROJECT_ROOT.resolve() / "polish_queue.md"
        bus = MessageBus()
        init_pipeline_dirs()
        n = _run_polish_mode(bus, ideas_path=_polish_path)
        if n == 0:
            return
        # Fall through — treat queued polish items as normal has_work
        has_work = True
        from_list = True  # keep seeding next polish item when current finishes
        bus = MessageBus()  # re-use same bus instance in the logic below

    # Determine what to work on
    has_work = False

    # Reset abandoned 'processing' messages from previous run.
    # After a graceful shutdown, agents leave in-flight messages as 'processing'
    # in queue files.  Without resetting, has_active_work() returns True and
    # _rebuild_queues_from_state bails, preventing any work from being re-queued.
    stale = bus.reset_stale_processing()
    if stale:
        print(f"  🔄 Reset {stale} stale message(s) from previous run")
    # Always purge dep-blocked messages — catches both stale-reset AND
    # pre-existing pending messages from previous runs.
    purged = _purge_dep_blocked_messages(bus)
    if purged:
        print(f"  🚫 Purged {purged} dep-blocked queue(s) — will resume when deps complete")

    if fresh_list_only:
        # Clear ALL existing queues — don't resume stray projects
        cleared_total = 0
        for _role in AGENT_ROLES:
            cleared_total += bus.clear_queue(_role)
        if cleared_total:
            print(f"  🧹 Cleared {cleared_total} stale queue message(s) (fresh-list-only mode)")

    if resume:
        # Resume always acts like --from-list: keep running until ALL projects
        # are done, not just the first queue drain.  This prevents the runner
        # from exiting when a message is in 'processing' state and the pending
        # queue looks empty to the health check.
        from_list = True
        has_work = check_resume(bus)
        if not has_work:
            # Queues empty but project state may exist — try rebuilding from state
            rebuilt = _rebuild_queues_from_state(bus)
            if rebuilt:
                print(f"  🔄 Rebuilt queues for {rebuilt} project(s) from saved state")
                has_work = True
            else:
                print("  No active pipeline to resume.")

    if not has_work and idea:
        seed_idea(bus, idea.split(".")[0][:50], idea)
        has_work = True

    if not has_work and from_list:
        # --fresh-list-only: never rebuild stray projects, go straight to ideas file
        if not fresh_list_only:
            rebuilt = _rebuild_queues_from_state(bus, ideas_path=_ideas_path)
            if rebuilt:
                print(f"  🔄 Rebuilt queues for {rebuilt} project(s) from saved state")
                has_work = True
        if not has_work:
            seed_result = seed_from_master_list(bus, ideas_path=_ideas_path,
                                                resume_inprogress=fresh_list_only)
            has_work = seed_result in (_SEED_SEEDED, _SEED_BLOCKED)

    # Final safety net: if queues have pending messages (from stale-reset or
    # a previous run), there IS work — just start the agents and let them process.
    if not has_work and not fresh_list_only and bus.has_active_work():
        pending_total = sum(bus.queue_depth(r) for r in AGENT_ROLES)
        print(f"  🔄 Found {pending_total} pending queue message(s) — starting agents")
        has_work = True

    if not has_work:
        print("\n  ✗ Nothing to do. Provide an idea, use --from-list, or --resume.")
        print("    python pipeline/runner.py \"Your idea here\"")
        print("    python pipeline/runner.py --from-list")
        return

    # Save initial status
    save_pipeline_status({
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "current_idea": idea or "(from list)",
    })

    # Start metrics collection
    run_metrics = RunMetrics.start(provider=provider, model=model)
    print(f"  Prompts:  {run_metrics.prompt_version}")

    # --- Ollama pre-flight check ---
    if provider == "ollama":
        model = _check_ollama_model(model)  # Returns canonical API name (may differ in case)

    # Start all agents
    print(f"\n  Starting agents...")
    supervisor = AgentSupervisor(provider, model)

    # Handle Ctrl+C
    stop_requested = False
    original_sigint = signal.getsignal(signal.SIGINT)

    def _handle_interrupt(signum, frame):
        nonlocal stop_requested
        if stop_requested:
            print("\n  Force stopping...")
            supervisor.stop_all()
            sys.exit(1)
        print("\n\n  [Pipeline] Graceful stop requested. Finishing current work...")
        print("  [Pipeline] Press Ctrl+C again to force stop.")
        stop_requested = True

    signal.signal(signal.SIGINT, _handle_interrupt)

    try:
        supervisor.start_all()
        supervisor.save_registry()

        # --- Warm context caches for all existing projects ---
        _ctx_refreshed = refresh_all_projects(PIPELINE_DIR)
        if _ctx_refreshed:
            print(f"  📦 Context cache: warmed {_ctx_refreshed} project(s)")
        start_background_refresh(PIPELINE_DIR, interval_seconds=120)

        print(f"\n  🚀 Pipeline running. Press Ctrl+C to stop.\n")

        start_time = time.time()
        health_check_interval = 60  # seconds — agents take minutes per call
        last_health_check = time.time()
        last_orphan_requeue = 0.0   # rate-limit orphan re-queues to once per 5 min
        ORPHAN_REQUEUE_COOLDOWN = 660  # 11 min — must exceed workspace recency guard (10 min)
        IDEATION_TIMEOUT = 35 * 60    # 35 min — retry if ideator hasn't written ideas yet
        ZERO_TASK_PHASE_KILL = 15 * 60  # 15 min in _executing with 0 tasks = stuck, skip it
        ZERO_TASK_WARN       = 10 * 60  # 10 min — warn before killing
        _status_count = 0  # for throttling non-interactive log output
        _last_tps_print = 0.0  # timestamp of last tok/s status print
        _TPS_PRINT_INTERVAL = 15 * 60  # print throughput every 15 minutes
        ideation_in_progress = False  # True while waiting for Ideator to generate new ideas
        ideation_requested_at = 0.0   # timestamp of last _request_ideation() call
        _zero_progress_since: dict[str, float] = {}  # (slug:phase) -> timestamp first seen 0 tasks
        _zero_task_warned: set[str] = set()  # keys that have had the 10-min warning printed

        # --- Dynamic Parallelizer (auto-tune) ---
        _tuner = None
        _tuner_log_path = PIPELINE_DIR / "state" / "tuner_log.jsonl"
        if auto_tune:
            try:
                from pipeline.dynamic_parallelizer import DynamicParallelizer
                _tuner = DynamicParallelizer(
                    min_seeds=1,
                    max_seeds=max_seeds,
                )
            except Exception as _te:
                print(f"  [tuner] Failed to init DynamicParallelizer: {_te}")

        # --- Strategy 6: Parallel seed slot tracking ---
        # Count how many distinct non-terminal projects are currently active.
        # When active_count < parallel_seeds, we can seed another project.
        def _count_active_projects() -> int:
            """Count projects that are in-flight (not complete/budget_exceeded)."""
            pd = PIPELINE_DIR / "projects"
            if not pd.exists():
                return 0
            active = 0
            for p in pd.iterdir():
                if not p.is_dir():
                    continue
                sf = p / "state" / "current_idea.json"
                if not sf.exists():
                    continue
                try:
                    s = json.loads(sf.read_text(encoding="utf-8"))
                    if s.get("status", "") not in ("complete", "budget_exceeded", ""):
                        active += 1
                except Exception:
                    pass
            return active

        # --- Strategy 7: Environment pooling — pre-warm context caches ---
        # Mirrors PufferLib's environment pool: spin up N environments before
        # any training starts.  Here we pre-build context_cache.json for the
        # next N unstarted ideas so agents start with a warm cache instead of
        # doing 5-10 file reads on their first turn.
        def _warm_upcoming_projects(n: int = 3) -> None:
            """Background thread: pre-build context caches for next N ideas."""
            try:
                from pipeline.context_aggregator import get_aggregator
                agg = get_aggregator()
                ideas_path = _ideas_path  # closure over outer scope
                if not ideas_path.exists():
                    return
                text = ideas_path.read_text(encoding="utf-8")
                # Extract unchecked items (same logic as seed_from_master_list)
                import re as _re
                unchecked = _re.findall(
                    r'^-\s*\[\s*\]\s+(.+?)\s*$', text, _re.MULTILINE
                )
                warmed = 0
                for raw_title in unchecked[:n]:
                    slug = _slugify(raw_title.split(".")[0][:50])
                    agg.build(slug=slug, force=False)  # no-op if cache exists
                    warmed += 1
                if warmed:
                    pass  # silent — background activity
            except Exception:
                pass

        # Kick off initial context pre-warming for next batch of ideas
        if from_list and parallel_seeds > 1:
            threading.Thread(
                target=_warm_upcoming_projects,
                args=(parallel_seeds + 2,),
                daemon=True,
                name="env-pool-warmup",
            ).start()

        while not stop_requested:
            # Time limit check
            if time_limit_minutes > 0:
                elapsed = (time.time() - start_time) / 60
                if elapsed >= time_limit_minutes:
                    print(f"\n  ⏰ Time limit reached ({time_limit_minutes:.0f} min)")
                    break

            # Periodic health check
            if time.time() - last_health_check >= health_check_interval:
                health = supervisor.check_health()
                restarted = supervisor.restart_dead()
                if restarted:
                    supervisor.save_registry()

                # Compact queues periodically (every ~30 health checks ≈ 30 min)
                if _status_count > 0 and _status_count % 10 == 0:
                    compacted = bus.compact_all()
                    if compacted > 0:
                        print(f"  🧹 Compacted {compacted} stale messages from queues")

                # --- Deterministic self-healing checks (every 5th cycle ≈ 5 min) ---
                # Pure Python, no LLM calls. Catches and auto-fixes:
                #   - stray files (src/, tests/ at root)
                #   - missing __init__.py
                #   - state inconsistencies
                #   - import issues
                if _status_count > 0 and _status_count % 5 == 0:
                    try:
                        from pipeline.health_checks import run_all_checks, write_health_report
                        _active_for_health = _get_active_idea_state(PIPELINE_DIR)
                        _health_slug = _active_for_health.get("_slug", "")
                        hc_results = run_all_checks(
                            PROJECT_ROOT, PIPELINE_DIR, _health_slug,
                        )
                        if hc_results:
                            fixes = sum(1 for r in hc_results if r.auto_fixed)
                            issues = len(hc_results) - fixes
                            if fixes:
                                print(f"  🩺 Health check: {fixes} auto-fixed, {issues} reported")
                            write_health_report(hc_results, PIPELINE_DIR)
                    except Exception as _hc_err:
                        print(f"  [health] Check failed: {_hc_err}")

                # Check if all queues are empty AND all ideas done
                all_empty = bus.all_queues_empty()
                # Find the most recently updated project's current_idea.json
                idea_state = _get_active_idea_state(PIPELINE_DIR)

                # --- Per-session budget enforcement ---
                # If the active project has been running longer than
                # PROJECT_TIME_BUDGET, force-complete it so we move on.
                _active_slug = idea_state.get("_slug", "")
                _active_started = idea_state.get("session_started_at",
                                                  idea_state.get("started_at", ""))
                if _active_slug and _active_started and idea_state.get("status", "") not in ("", "complete", "budget_exceeded"):
                    _is_locked = idea_state.get("budget_lock", False)
                    try:
                        _start = datetime.fromisoformat(_active_started)
                        _elapsed = (datetime.now(timezone.utc) - _start).total_seconds() / 60

                        # Budget scales with complexity: phase_budget min per phase, min base_budget
                        _total_phases = idea_state.get("total_phases", 3)
                        _phase_budget = max(base_budget, int(_total_phases) * phase_budget)

                        # Grace: don't kill a project on its FINAL phase — let it finish
                        _current_phase = idea_state.get("phase", 1)
                        _on_final_phase = (isinstance(_current_phase, int) and
                                           isinstance(_total_phases, int) and
                                           _current_phase >= _total_phases)
                        # Allow 50% extra time if on final phase
                        if _on_final_phase:
                            _phase_budget = int(_phase_budget * 1.5)

                        if _elapsed > _phase_budget and not _is_locked:
                            _proj_file = PIPELINE_DIR / "projects" / _active_slug / "state" / "current_idea.json"
                            idea_state["pre_budget_status"] = idea_state.get("status", "phase_1_executing")
                            idea_state["status"] = "budget_exceeded"
                            idea_state["budget_note"] = f"Force-completed after {_elapsed:.0f} min (budget: {_phase_budget} min for {_total_phases}-phase project)"
                            _proj_file.write_text(json.dumps(idea_state, indent=2), encoding="utf-8")
                            print(f"  Budget exceeded for '{idea_state.get('title', _active_slug)}' ({_elapsed:.0f}m > {_phase_budget}m [{_total_phases} phases]) -- skipping")
                            cleared = 0
                            for _role in AGENT_ROLES:
                                cleared += bus.clear_queue(_role)
                            if cleared:
                                print(f"  Cleared {cleared} queued message(s) for budget-exceeded project")
                        elif _elapsed > _phase_budget and _is_locked:
                            if int(_elapsed) % 30 < 2:  # warn once every 30 min
                                print(f"  🔒 [LOCKED] '{idea_state.get('title', _active_slug)}' over budget ({_elapsed:.0f}m) but lock prevents skip")
                    except Exception:
                        pass

                # --- Immediate _reviewed advancement ---
                # If the active project is at phase_X_reviewed and queues are
                # empty, advance it NOW. Don't wait for _rebuild_queues_from_state
                # (which has an 11-min cooldown and multiple preconditions).
                _active_status = idea_state.get("status", "")
                if _active_status.endswith("_reviewed") and all_empty and _active_slug:
                    _rv_match = re.match(r"phase_(\d+)_reviewed", _active_status)
                    if _rv_match:
                        _rv_phase = int(_rv_match.group(1))
                        _rv_proj = PIPELINE_DIR / "projects" / _active_slug
                        _rv_state_file = _rv_proj / "state" / "current_idea.json"
                        if _rv_state_file.exists():
                            try:
                                _rv_state = json.loads(_rv_state_file.read_text(encoding="utf-8"))
                                routed = _tick_project(bus, _rv_proj, _rv_state, _rv_phase, _active_slug)
                                if routed:
                                    # Re-read idea_state since _tick_project may have changed it
                                    idea_state = _get_active_idea_state(PIPELINE_DIR)
                            except Exception as _rv_err:
                                print(f"  [reviewed] Failed to advance {_active_slug}: {_rv_err}")

                # If active project is budget_exceeded, advance to next project.
                if idea_state.get("status") == "budget_exceeded":
                    slug = idea_state.get("_slug", "")
                    orphaned = _rebuild_queues_from_state(bus)
                    if orphaned:
                        print(f"  ▶️  Advancing past '{slug}' → {orphaned} project(s) queued")
                    if from_list and not bus.has_active_work():
                        # --- Strategy 6: Parallel seeding ---
                        # Try to fill all open slots up to parallel_seeds.
                        active_now = _count_active_projects()
                        slots_free = max(1, parallel_seeds - active_now)
                        for _seed_i in range(slots_free):
                            seeded = seed_from_master_list(bus, silent=ideation_in_progress,
                                                            ideas_path=_ideas_path, resume_inprogress=fresh_list_only)
                            if seeded == _SEED_SEEDED:
                                ideation_in_progress = False
                                ideation_requested_at = 0.0
                                # After seeding, pre-warm next batch (Strategy 7)
                                if parallel_seeds > 1:
                                    threading.Thread(
                                        target=_warm_upcoming_projects,
                                        args=(parallel_seeds,),
                                        daemon=True,
                                        name="env-pool-refill",
                                    ).start()
                            elif seeded == _SEED_EMPTY and not ideation_in_progress:
                                _request_ideation(bus)
                                ideation_in_progress = True
                                ideation_requested_at = time.time()
                                break
                            elif seeded == _SEED_EMPTY and time.time() - ideation_requested_at > IDEATION_TIMEOUT:
                                print("  ⏰ Ideation timed out — retrying...")
                                ideation_in_progress = False
                                ideation_requested_at = 0.0
                                break
                            else:
                                break  # _SEED_BLOCKED or no more ideas
                    elif from_list and not orphaned:
                        seed_from_master_list(bus, silent=True, ideas_path=_ideas_path,
                                              resume_inprogress=fresh_list_only)

                running_agents = sum(1 for s in health.values() if s == "running")

                # Print status line
                pending_total = sum(bus.queue_depth(r) for r in AGENT_ROLES)
                elapsed_m = (time.time() - start_time) / 60
                phase = idea_state.get("status", "?")
                title = idea_state.get("title", "")
                title_str = f" | [{title[:28]}]" if title else ""

                # --- Live task progress from tasks.md (not stale JSON) ---
                # The executor only writes tasks_done/tasks_total once at start.
                # We re-read the actual file every tick for live progress.
                tasks_done, tasks_total = 0, 0
                try:
                    slug = idea_state.get("_slug", "")
                    phase_num = idea_state.get("phase", 1)
                    if slug:
                        tasks_file = PIPELINE_DIR / "projects" / slug / f"phases/phase_{phase_num}/tasks.md"
                        if tasks_file.exists():
                            from pipeline.agent_process import AgentProcess
                            AgentProcess.normalize_tasks_file(tasks_file)  # fix heading format
                            raw = tasks_file.read_text(encoding="utf-8")
                            scoped = AgentProcess._extract_phase_tasks(raw, phase_num)
                            tasks_total = len(re.findall(r'^\s*- \[[ xX]\]', scoped, re.MULTILINE))
                            tasks_done  = len(re.findall(r'^\s*- \[[xX]\]', scoped, re.MULTILINE))
                            # Fallback: count numbered task lines if no checkbox format found
                            if tasks_total == 0:
                                numbered = re.findall(r'^\d+\.\s+\S', scoped, re.MULTILINE)
                                tasks_total = len(numbered)
                except Exception:
                    pass
                task_str = f" {tasks_done}/{tasks_total}✓" if tasks_total else ""

                # --- Workspace activity signal (used by stall-kill guard below) ---
                # Measures file-write activity independently of checkbox state.
                # The executor often writes files for 10-15 min before marking any [x].
                _ws_file_count = 0
                _ws_last_mtime = 0.0
                try:
                    if _active_slug:
                        _ws_dir = PIPELINE_DIR / "projects" / _active_slug / "workspace"
                        if _ws_dir.exists():
                            for _wf in _ws_dir.rglob("*"):
                                if _wf.is_file() and not _wf.name.startswith("."):
                                    _ws_file_count += 1
                                    _mt = _wf.stat().st_mtime
                                    if _mt > _ws_last_mtime:
                                        _ws_last_mtime = _mt
                except Exception:
                    pass

                # Improve display: when 0 checkboxes but files exist, show file count
                if tasks_total and tasks_done == 0 and _ws_file_count > 0:
                    task_str = f" 0/{tasks_total}✓ ({_ws_file_count} files)"

                # Ollama GPU heartbeat (checks every 5 min, cached otherwise)
                gpu_str = ""
                _gpu_idle = False
                if provider == "ollama":
                    gpu_status = _check_ollama_heartbeat(model)
                    if gpu_status:
                        if "IDLE" in gpu_status or "ERR" in gpu_status:
                            gpu_str = f" ⚠️ {gpu_status} — model evicted from VRAM!"
                            _gpu_idle = True
                        else:
                            gpu_str = f" {gpu_status}"

                # --- Dynamic Parallelizer: observe & adjust ---
                _tuner_str = ""
                if _tuner is not None:
                    try:
                        _tp_path = PIPELINE_DIR / "state" / "throughput.json"
                        _decision = _tuner.observe(
                            throughput_path=_tp_path,
                            current_seeds=parallel_seeds,
                            gpu_idle=_gpu_idle,
                        )
                        if _decision.changed:
                            parallel_seeds = _decision.new_seeds
                            print(f"  {_decision.reason} [conf={_decision.confidence:.0%}]")
                            try:
                                with open(_tuner_log_path, "a", encoding="utf-8") as _tlf:
                                    _tlf.write(json.dumps({
                                        "ts": time.time(),
                                        "old_seeds": _decision.old_seeds,
                                        "new_seeds": _decision.new_seeds,
                                        "reason": _decision.reason,
                                        "confidence": round(_decision.confidence, 3),
                                    }) + "\n")
                            except Exception:
                                pass
                        if _status_count % 4 == 0:
                            _tuner_str = f"  {_tuner.status_line(parallel_seeds)}"
                    except Exception:
                        pass  # Never crash the loop on tuner errors

                status_line = _clean(
                    f"  [{elapsed_m:.0f}m] agents={running_agents}/{len(AGENT_ROLES)} "
                    f"pending={pending_total} phase={phase}{task_str}{gpu_str}{title_str}"
                )
                # Always print on a new line — ’\r’ tricks break on cloud/Windows terminals.
                # Throttle to every 4 checks (~4 min) to keep output readable.
                if _status_count % 4 == 0:
                    print(status_line, flush=True)
                    if _tuner_str:
                        print(_tuner_str, flush=True)
                _status_count += 1

                # Print full throughput breakdown every 15 minutes
                _now = time.time()
                if provider == "ollama" and (_now - _last_tps_print) >= _TPS_PRINT_INTERVAL:
                    _tp_path = PIPELINE_DIR / "state" / "throughput.json"
                    if _tp_path.exists():
                        try:
                            _tp = json.loads(_tp_path.read_text(encoding="utf-8"))
                            _age_s      = _now - _tp.get("updated_at", _now)
                            _cum_tok    = _tp.get("cumulative_tokens", 0)
                            _cum_inf_s  = _tp.get("cumulative_inference_s", 0.0)
                            _cum_wall_s = _tp.get("cumulative_wall_s", 0.0) or 1
                            _cum_tool_s = _tp.get("cumulative_tool_s", 0.0)
                            _calls      = _tp.get("call_count", 0)
                            _tool_calls = _tp.get("tool_call_count", 0)
                            _tps_inf    = _tp.get("tps", 0)  # last-call GPU tok/s
                            # Pipeline tok/s = total tokens / total elapsed time
                            _tps_pipe   = _cum_tok / _cum_wall_s if _cum_tok else 0
                            # Average inference tok/s over the whole session
                            _tps_inf_avg = _cum_tok / _cum_inf_s if _cum_inf_s > 0 else 0
                            # Time allocation percentages
                            _gpu_pct    = (_cum_inf_s  / _cum_wall_s) * 100
                            _tool_pct   = (_cum_tool_s / _cum_wall_s) * 100
                            _overhead_pct = max(0, 100 - _gpu_pct - _tool_pct)
                            # Human-readable wall time
                            _wall_h     = int(_cum_wall_s // 3600)
                            _wall_m     = int((_cum_wall_s % 3600) // 60)
                            _wall_str   = (f"{_wall_h}h{_wall_m:02d}m" if _wall_h
                                           else f"{_wall_m}m")
                            _age_str    = (f"{int(_age_s // 60)}m ago"
                                           if _age_s > 90 else "recent")
                            if _cum_tok > 0 and _age_s < 3600:
                                print(
                                    f"  \U0001f4ca Throughput [{_wall_str} wall-clock, "
                                    f"{_calls} LLM calls, {_tool_calls} tool calls]\n"
                                    f"     Inference:  {_tps_inf:.1f} tok/s (last call)  "
                                    f"/ {_tps_inf_avg:.1f} tok/s avg\n"
                                    f"     Pipeline:   {_tps_pipe:.1f} tok/s  "
                                    f"(tokens / total wall-clock)\n"
                                    f"     Time split: GPU {_gpu_pct:.0f}%  "
                                    f"| Tools {_tool_pct:.0f}%  "
                                    f"| Overhead {_overhead_pct:.0f}%  "
                                    f"(queue/switch/init)\n"
                                    f"     Tokens:     {_cum_tok:,} generated  "
                                    f"/ {_cum_tok//_calls if _calls else 0} avg/call  "
                                    f"(last: {_age_str})",
                                    flush=True,
                                )
                        except Exception:
                            pass
                    _last_tps_print = _now

                # --- Zero-task-progress phase kill ---
                # If the executor has been in *_executing phase for ZERO_TASK_PHASE_KILL
                # with 0/N tasks done, the project is genuinely stuck (e.g. external API
                # unavailable, impossible task). Mark budget_exceeded and move on.
                _zpk = f"{_active_slug}:{idea_state.get('phase', 1)}"
                _is_locked = idea_state.get("budget_lock", False)
                if (tasks_total > 0 and tasks_done == 0
                        and "executing" in idea_state.get("status", "")
                        and _active_slug
                        and not _is_locked
                        and idea_state.get("status", "") not in ("complete", "budget_exceeded")):
                    # Guard: if workspace files were written recently the executor IS
                    # making progress — it just hasn't ticked checkboxes yet (0→N pattern).
                    # Reset the stall timer so we don't kill a productive executor.
                    _ACTIVITY_WINDOW = 8 * 60  # 8 min — executor marks boxes at end
                    _ws_active = (
                        _ws_last_mtime > 0
                        and (time.time() - _ws_last_mtime) < _ACTIVITY_WINDOW
                    )
                    if _ws_active:
                        # Files modified recently → reset stall clock silently
                        _zero_progress_since.pop(_zpk, None)
                        _zero_task_warned.discard(_zpk)
                    elif _zpk not in _zero_progress_since:
                        _zero_progress_since[_zpk] = time.time()
                    else:
                        _stall_secs = time.time() - _zero_progress_since[_zpk]
                        # 10-min warning
                        if _stall_secs > ZERO_TASK_WARN and _zpk not in _zero_task_warned:
                            _zero_task_warned.add(_zpk)
                            print(
                                f"  ⚠️  Zero-task stall: '{idea_state.get('title', _active_slug)}' "
                                f"phase {idea_state.get('phase',1)} — "
                                f"0/{tasks_total} tasks for {int(_stall_secs//60)}m, "
                                f"{_ws_file_count} workspace file(s), "
                                f"last write {int((time.time()-_ws_last_mtime)//60) if _ws_last_mtime else '?'}m ago "
                                f"(kill in {(ZERO_TASK_PHASE_KILL - _stall_secs)//60:.0f}m)"
                            )
                        # 15-min kill — only fires if no recent file activity either
                        if _stall_secs > ZERO_TASK_PHASE_KILL:
                            _proj_file = (PIPELINE_DIR / "projects" / _active_slug
                                          / "state" / "current_idea.json")
                            try:
                                _st = json.loads(_proj_file.read_text(encoding="utf-8"))
                                if _st.get("status", "") not in ("complete", "budget_exceeded"):
                                    _st["status"] = "budget_exceeded"
                                    _st["budget_note"] = (
                                        f"Phase {idea_state.get('phase',1)} stuck: "
                                        f"0/{tasks_total} tasks after {ZERO_TASK_PHASE_KILL//60}m"
                                    )
                                    _proj_file.write_text(json.dumps(_st, indent=2), encoding="utf-8")
                                    print(
                                        f"  ⏰ Zero-task timeout: '{idea_state.get('title', _active_slug)}' "
                                        f"phase {idea_state.get('phase',1)} — "
                                        f"0/{tasks_total} tasks in {ZERO_TASK_PHASE_KILL//60}m → budget_exceeded"
                                    )
                                    for _role in AGENT_ROLES:
                                        bus.clear_queue(_role)
                            except Exception:
                                pass
                            _zero_progress_since.pop(_zpk, None)
                            _zero_task_warned.discard(_zpk)
                else:
                    _zero_progress_since.pop(_zpk, None)  # reset when tasks progress or phase changes
                    _zero_task_warned.discard(_zpk)

                if all_empty and not from_list:
                    # Single idea mode — might be done
                    # Wait a bit longer to make sure nothing new arrives
                    time.sleep(10)
                    if bus.all_queues_empty():
                        print(f"\n  ✓ All queues empty — pipeline complete.")
                        break
                elif all_empty and from_list:
                    # --- Guard: don't seed a new project if any project is
                    # actively being worked on.  The queue looks empty because
                    # the agent acked the message, but the agent is still
                    # processing it.  Check if ANY project has a working-state
                    # status that was recently modified (< 15 min ago). ---
                    _any_working = False
                    _working_states = ("_executing", "_validating", "_reviewing", "_planning")
                    _recency_cutoff = time.time() - 900  # 15 min
                    _projects_dir = PIPELINE_DIR / "projects"
                    if _projects_dir.exists():
                        for _pd in _projects_dir.iterdir():
                            _sf = _pd / "state" / "current_idea.json"
                            if not _sf.exists():
                                continue
                            try:
                                if os.path.getmtime(str(_sf)) < _recency_cutoff:
                                    continue
                                _st = json.loads(_sf.read_text(encoding="utf-8"))
                                _ss = _st.get("status", "")
                                if any(_ss.endswith(ws) for ws in _working_states):
                                    _any_working = True
                                    break
                            except Exception:
                                pass

                    if _any_working:
                        pass  # agent is mid-task — wait for it to finish
                    elif not bus.has_active_work():
                        now = time.time()
                        if now - last_orphan_requeue >= ORPHAN_REQUEUE_COOLDOWN:
                            orphaned = 0 if fresh_list_only else _rebuild_queues_from_state(bus)
                            if orphaned:
                                last_orphan_requeue = now
                                print(f"  🔁 Re-queued {orphaned} orphaned project(s) — not seeding new ideas yet")
                            else:
                                seeded = seed_from_master_list(bus, silent=ideation_in_progress,
                                                                ideas_path=_ideas_path, resume_inprogress=fresh_list_only)
                                if seeded == _SEED_SEEDED:
                                    ideation_in_progress = False
                                    ideation_requested_at = 0.0
                                elif seeded == _SEED_EMPTY and not ideation_in_progress:
                                    _request_ideation(bus)
                                    ideation_in_progress = True
                                    ideation_requested_at = time.time()
                                elif seeded == _SEED_EMPTY and time.time() - ideation_requested_at > IDEATION_TIMEOUT:
                                    print("  ⏰ Ideation timed out — retrying...")
                                    ideation_in_progress = False
                                    ideation_requested_at = 0.0
                                # _SEED_BLOCKED — deps pending, just wait

                # --- Collect per-project metrics from state files ---
                try:
                    projects_dir = PIPELINE_DIR / "projects"
                    if projects_dir.exists():
                        for proj_dir in projects_dir.iterdir():
                            if not proj_dir.is_dir():
                                continue
                            slug = proj_dir.name
                            ci_path = proj_dir / "state" / "current_idea.json"
                            if ci_path.exists():
                                ci = json.loads(ci_path.read_text(encoding="utf-8"))
                                run_metrics.record_project_start(slug)
                                st = ci.get("status", "")
                                if st == "complete":
                                    # Read retry counts from phase_retries.json
                                    retries = 0
                                    pr_path = proj_dir / "state" / "phase_retries.json"
                                    if pr_path.exists():
                                        try:
                                            pr_data = json.loads(pr_path.read_text(encoding="utf-8"))
                                            retries = sum(v for v in pr_data.values() if isinstance(v, int))
                                        except Exception:
                                            pass
                                    run_metrics.record_project_complete(
                                        slug,
                                        phases=ci.get("phase", 0),
                                        retries=retries,
                                    )
                except Exception:
                    pass  # metrics are best-effort, never crash the runner

                last_health_check = time.time()

            time.sleep(2)

    finally:
        stop_background_refresh()
        print("\n  Stopping agents...")
        supervisor.stop_all()
        supervisor.save_registry()

        save_pipeline_status({
            "status": "stopped",
            "stopped_at": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "model": model,
        })

        # Finalize and save metrics report
        try:
            metrics_path = run_metrics.finish()
            metrics_report = metrics_path.parent / "report.md"
        except Exception as e:
            metrics_report = None
            print(f"  ⚠ Metrics save failed: {e}")

        signal.signal(signal.SIGINT, original_sigint)

        print("\n" + "=" * 60)
        print("  Pipeline stopped.")
        print(f"  Logs: .pipeline/logs/")
        print(f"  Output: .pipeline/workspace/")
        print(f"  Decisions: .pipeline/state/manager_decisions.md")
        if metrics_report and metrics_report.exists():
            print(f"  Run Report: {metrics_report.relative_to(PROJECT_ROOT)}")
            print(f"  Prompt Ver: {run_metrics.prompt_version}")
        print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Multi-agent idea development pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python pipeline/runner.py "Build a CLI tool that converts CSV to JSON"
              python pipeline/runner.py --from-list
              python pipeline/runner.py --from-list --provider ollama --model qwen3.5:35b --time-limit 480
              python pipeline/runner.py --resume
        """),
    )
    parser.add_argument("idea", nargs="?", default=None,
                        help="Idea description to implement")
    parser.add_argument("--from-list", action="store_true",
                        help="Read ideas from master_ideas.md")
    parser.add_argument("--resume", action="store_true",
                        help="Resume a previously stopped pipeline")
    parser.add_argument("--provider", default="ollama",
                        choices=["openai", "claude", "gemini", "ollama", "grok"],
                        help="LLM provider (default: ollama)")
    parser.add_argument("--model", default=os.environ.get("PIPELINE_MODEL", "qwen3.5:35b"),
                        help="LLM model (default: qwen3.5:35b, or $PIPELINE_MODEL env var)")
    parser.add_argument("--time-limit", type=float, default=0,
                        help="Time limit in minutes (0 = unlimited)")
    parser.add_argument("--base-budget", type=int, default=DEFAULT_BASE_BUDGET,
                        help=f"Minimum minutes per project (default: {DEFAULT_BASE_BUDGET}). "
                             f"Lower for smaller GPUs, higher for bigger ones.")
    parser.add_argument("--phase-budget", type=int, default=DEFAULT_PHASE_BUDGET,
                        help=f"Minutes per phase (default: {DEFAULT_PHASE_BUDGET}). "
                             f"Total budget = max(base-budget, phases * phase-budget).")
    parser.add_argument("--ideas-file", default=None,
                        help="Path to a specific master ideas file (default: master_ideas.md). "
                             "Use this to run separate instances on different idea lists.")
    parser.add_argument("--fresh-list-only", action="store_true",
                        help="Skip all stray/in-progress projects. Only work from --ideas-file "
                             "(or master_ideas.md). Use for a clean second instance.")
    parser.add_argument("--polish", action="store_true",
                        help="Resume complete projects with missing phases, reading from "
                             "polish_queue.md (auto-generated if missing). "
                             "Use with --ideas-file to specify an alternate polish list.")
    parser.add_argument("--parallel-seeds", type=int, default=1, metavar="N",
                        help="Seed up to N independent projects simultaneously. "
                             "With --auto-tune this becomes the starting value (default: 1). "
                             "Example: --parallel-seeds 2")
    parser.add_argument("--auto-tune", action="store_true",
                        help="Enable the DynamicParallelizer: automatically detects diminishing "
                             "returns and adjusts parallel seeds to maximise throughput. "
                             "Starts at --parallel-seeds N and self-adjusts up to --max-seeds M. "
                             "Example: --auto-tune --parallel-seeds 1 --max-seeds 4")
    parser.add_argument("--max-seeds", type=int, default=4, metavar="M",
                        help="Upper ceiling for --auto-tune (default: 4). Ignored when "
                             "--auto-tune is not set.")

    args = parser.parse_args()

    if not args.idea and not args.from_list and not args.resume and not args.polish:
        parser.print_help()
        print("\nProvide an idea, use --from-list, --resume, or --polish.")
        sys.exit(1)

    run_pipeline(
        idea=args.idea,
        from_list=args.from_list,
        resume=args.resume,
        provider=args.provider,
        model=args.model,
        time_limit_minutes=args.time_limit,
        base_budget=args.base_budget,
        phase_budget=args.phase_budget,
        ideas_file=args.ideas_file,
        fresh_list_only=args.fresh_list_only,
        polish=args.polish,
        parallel_seeds=args.parallel_seeds,
        auto_tune=args.auto_tune,
        max_seeds=args.max_seeds,
    )


if __name__ == "__main__":
    main()
