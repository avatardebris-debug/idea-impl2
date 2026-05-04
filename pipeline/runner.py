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


# Maximum wall-clock time per project before force-completing (minutes).
# 90 min = enough for 3 phases × ~25 min each.  Prevents any single project
# from monopolizing an unattended pipeline run.
PROJECT_TIME_BUDGET = 90   # minutes per project — SCALES with total_phases (see budget enforcement)

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

    # 3. Warm up: trigger a tiny inference to load model into VRAM
    print(f"  Model:    {model} (warming up...)", end="", flush=True)
    try:
        req = urllib.request.Request(
            f"{base_url}/api/generate",
            data=json.dumps({
                "model": model,
                "prompt": "/no_think say OK",
                "stream": False,
                "keep_alive": -1,           # pin model in VRAM after warmup
                "options": {"num_predict": 5},
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=300)  # 5 min — large models take time
        result = json.loads(resp.read())
        # Check if response came back
        if result.get("response", "").strip():
            print(" ✅")
        else:
            print(" ⚠️  (empty response)")
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
    TERMINAL = {"complete", "budget_exceeded"}
    projects_dir = pipeline_dir / "projects"
    candidates: list[pathlib.Path] = []

    if projects_dir.exists():
        candidates = list(projects_dir.glob("*/state/current_idea.json"))

    if candidates:
        # Prefer in-progress projects sorted by most recently modified
        def sort_key(p: pathlib.Path):
            try:
                state = json.loads(p.read_text(encoding="utf-8"))
                is_terminal = state.get("status", "") in TERMINAL
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
# Seed the pipeline with the first idea
# ---------------------------------------------------------------------------

_seeded_this_session: set[str] = set()  # titles seeded in this runner invocation


def seed_idea(bus: MessageBus, title: str, description: str, deps: list | None = None) -> None:
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


def seed_from_master_list(bus: MessageBus) -> bool:
    """Find the first unchecked, unblocked idea in master_ideas.md and seed it.

    Dependency syntax (append to description):
        requires: slug_one, slug_two

    Example master_ideas.md line:
        - [ ] **[Movie idea generator]** — [generate movie ideas. requires: ai_movie_generation_suite]

    Blocked ideas (deps not yet complete) are skipped with a status message.
    They unblock automatically once their dependencies reach 'complete'.
    """
    mi_path = PROJECT_ROOT.resolve() / "master_ideas.md"
    if not mi_path.exists():
        print("  ✗ master_ideas.md not found")
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
                    _seeded_this_session.add(title)
                    continue
                else:
                    print(f"  ⏭  Skipping '{title}' — already in progress ({status}), resuming from queue")
                    _seeded_this_session.add(title)
                    continue
            except Exception:
                pass  # Can't read state — seed it fresh

        description_raw = match.group(2).strip()
        # Strip outer brackets from description if present: [text] -> text
        if description_raw.startswith("[") and description_raw.endswith("]"):
            description_raw = description_raw[1:-1].strip()

        # --- Parse 'requires: slug1, slug2' dependency declarations ---
        # Handles trailing ] from markdown format e.g. [desc. requires: slug]
        dep_match = re.search(r'\brequires:\s*([\w,\s_-]+?)[\]\s.]*$', description_raw, re.IGNORECASE)
        deps: list = []
        description = description_raw
        if dep_match:
            raw_deps = dep_match.group(1)
            deps = [d.strip() for d in re.split(r'[,;]+', raw_deps) if d.strip()]
            description = description_raw[:dep_match.start()].strip().rstrip('.')

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

        seed_idea(bus, title, description, deps=deps or None)
        return True

    if blocked_count > 0:
        print(f"  [BLOCKED] {blocked_count} idea(s) blocked on dependencies -- will retry next tick")
    else:
        print("  ✗ No unchecked ideas found in master_ideas.md")
    return False


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

def _rebuild_queues_from_state(bus: MessageBus) -> int:
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

        if status in ("", "complete", "budget_exceeded"):
            continue

        # --- Budget enforcement: reset started_at to NOW ---
        # Budget measures per-SESSION time, not total project lifetime.
        # On a cold restart, every project's old started_at would be hours
        # old, causing everything to get budget_exceeded immediately.
        # Reset the clock so budget enforcement works correctly during THIS
        # session's health-check loop.
        state["started_at"] = datetime.now(timezone.utc).isoformat()
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        # Skip projects whose validator has already hit the stall limit —
        # these should have been force-advanced by the manager, but if the
        # manager message was lost, don't loop forever on the same project.
        retries_file = project_dir / "state" / "phase_retries.json"
        if retries_file.exists():
            try:
                retries = json.loads(retries_file.read_text(encoding="utf-8"))
                # Check for any no_progress streak >= 2 (our stall limit)
                for k, v in retries.items():
                    if "no_progress" in k and isinstance(v, int) and v >= 2:
                        # Force-mark as complete so it never comes back
                        state["status"] = "complete"
                        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
                        print(f"  ⏭  Force-completed stalled project '{title}' (stuck {v} cycles)")
                        break
                else:
                    retries = None  # didn't break — not stalled
                if state.get("status") == "complete":
                    continue
            except Exception:
                pass

        # Detect which phase and step we were on
        phase_match = re.match(r"phase_(\d+)_(\w+)", status)
        if phase_match:
            phase_num  = int(phase_match.group(1))
            phase_step = phase_match.group(2)

            # --- Retroactive task guardrail ---
            # Trim oversized task files for projects created before the guardrail.
            MAX_TASKS = 8
            tasks_file = project_dir / f"phases/phase_{phase_num}/tasks.md"
            if tasks_file.exists():
                try:
                    from pipeline.agent_process import AgentProcess
                    AgentProcess.normalize_tasks_file(tasks_file)  # ## Task N: -> - [ ] Task N:
                    raw = tasks_file.read_text(encoding="utf-8")
                    scoped = AgentProcess._extract_phase_tasks(raw, phase_num)
                    lines = scoped.split("\n")
                    task_indices = [i for i, l in enumerate(lines) if l.strip().startswith("- [ ]") or l.strip().startswith("- [x]")]
                    if len(task_indices) > MAX_TASKS:
                        cut_at = task_indices[MAX_TASKS]
                        trimmed = "\n".join(lines[:cut_at])
                        trimmed += f"\n\n<!-- {len(task_indices) - MAX_TASKS} tasks removed by retroactive guardrail -->\n"
                        tasks_file.write_text(trimmed, encoding="utf-8")
                        print(f"  ✂️  Trimmed '{title}' phase {phase_num}: {len(task_indices)} → {MAX_TASKS} tasks")
                except Exception:
                    pass

        # Always refresh started_at when re-queuing — budget is per-session,
        # not total project lifetime. Without this, a manually-reset project
        # or one from a previous session fires budget_exceeded immediately.
        state["started_at"] = datetime.now(timezone.utc).isoformat()
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

    if is_emergency:
        # EMERGENCY REWORK — re-plan the phase
        review_full = str(project_dir / review_path) if review_path else ""
        bus.send(Message.create(
            from_agent="runner",
            to_agent="phase_planner",
            type="task",
            payload={
                "phase": phase_num,
                "phase_spec": f"REWORK REQUIRED — see review at {review_full}",
                "is_rework": True,
                "idea_slug": slug,
            },
            priority=0,
        ))
        # Update status
        _write_state(project_dir, state, f"phase_{phase_num}_planning")
        print(f"  🚨 Emergency rework for '{title}' phase {phase_num}")
        return True

    elif blocking_bugs > 0:
        # Increment retry counter
        retries = _increment_retries(project_dir, phase_num)

        if retries >= MAX_PHASE_RETRIES:
            # Too many retries — force-advance
            print(f"  ⚠️  Force-advancing '{title}' phase {phase_num} after {retries} retries ({blocking_bugs} bugs remain)")
            _reset_retries(project_dir, phase_num)
            advanced = _advance_phase(bus, project_dir, state, phase_num, slug)
            if not advanced:
                _mark_complete(project_dir, state, title)
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
    """Advance to next phase if one exists. Returns True if advanced."""
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

    # --- Fallback: trust total_phases field in state ---
    total_phases = state.get("total_phases", 0)
    if not phase_found_in_plan and total_phases > 0 and next_phase <= total_phases:
        phase_found_in_plan = True  # plan says more phases exist

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


def _mark_complete(project_dir: pathlib.Path, state: dict, title: str) -> None:
    """Mark a project as complete in both state file and master_ideas.md."""
    state["status"] = "complete"
    state.pop("review_result", None)
    _write_state_dict(project_dir, state)

    # Mark in master_ideas.md
    mi_path = PROJECT_ROOT / "master_ideas.md"
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


def run_pipeline(
    idea: str | None = None,
    from_list: bool = False,
    resume: bool = False,
    provider: str = "ollama",
    model: str = os.environ.get("PIPELINE_MODEL", "qwen3.5:35b"),
    time_limit_minutes: float = 0,
) -> None:
    """Main pipeline orchestrator."""
    init_pipeline_dirs()
    bus = MessageBus()

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

    # Determine what to work on
    has_work = False

    # Reset abandoned 'processing' messages from previous run.
    # After a graceful shutdown, agents leave in-flight messages as 'processing'
    # in queue files.  Without resetting, has_active_work() returns True and
    # _rebuild_queues_from_state bails, preventing any work from being re-queued.
    stale = bus.reset_stale_processing()
    if stale:
        print(f"  🔄 Reset {stale} stale message(s) from previous run")

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
        # First try to rebuild any in-progress projects from saved state
        rebuilt = _rebuild_queues_from_state(bus)
        if rebuilt:
            print(f"  🔄 Rebuilt queues for {rebuilt} project(s) from saved state")
            has_work = True
        else:
            has_work = seed_from_master_list(bus)

    # Final safety net: if queues have pending messages (from stale-reset or
    # a previous run), there IS work — just start the agents and let them process.
    if not has_work and bus.has_active_work():
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

        print(f"\n  🚀 Pipeline running. Press Ctrl+C to stop.\n")

        start_time = time.time()
        health_check_interval = 60  # seconds — agents take minutes per call
        last_health_check = time.time()
        last_orphan_requeue = 0.0   # rate-limit orphan re-queues to once per 5 min
        ORPHAN_REQUEUE_COOLDOWN = 660  # 11 min — must exceed workspace recency guard (10 min)
        _status_count = 0  # for throttling non-interactive log output
        ideation_in_progress = False  # True while waiting for Ideator to generate new ideas

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

                # Check if all queues are empty AND all ideas done
                all_empty = bus.all_queues_empty()
                # Find the most recently updated project's current_idea.json
                idea_state = _get_active_idea_state(PIPELINE_DIR)

                # --- Per-session budget enforcement ---
                # If the active project has been running longer than
                # PROJECT_TIME_BUDGET, force-complete it so we move on.
                _active_slug = idea_state.get("_slug", "")
                _active_started = idea_state.get("started_at", "")
                if _active_slug and _active_started and idea_state.get("status", "") not in ("", "complete", "budget_exceeded"):
                    try:
                        _start = datetime.fromisoformat(_active_started)
                        _elapsed = (datetime.now(timezone.utc) - _start).total_seconds() / 60

                        # Budget scales with complexity: 30 min per phase, min 90 min
                        _total_phases = idea_state.get("total_phases", 3)
                        _phase_budget = max(PROJECT_TIME_BUDGET, int(_total_phases) * 30)

                        # Grace: don't kill a project on its FINAL phase — let it finish
                        _current_phase = idea_state.get("phase", 1)
                        _on_final_phase = (isinstance(_current_phase, int) and
                                           isinstance(_total_phases, int) and
                                           _current_phase >= _total_phases)
                        # Allow 50% extra time if on final phase
                        if _on_final_phase:
                            _phase_budget = int(_phase_budget * 1.5)

                        if _elapsed > _phase_budget:
                            _proj_file = PIPELINE_DIR / "projects" / _active_slug / "state" / "current_idea.json"
                            idea_state["status"] = "budget_exceeded"
                            idea_state["budget_note"] = f"Force-completed after {_elapsed:.0f} min (budget: {_phase_budget} min for {_total_phases}-phase project)"
                            _proj_file.write_text(json.dumps(idea_state, indent=2), encoding="utf-8")
                            print(f"  Budget exceeded for '{idea_state.get('title', _active_slug)}' ({_elapsed:.0f}m > {_phase_budget}m [{_total_phases} phases]) -- skipping")
                            cleared = 0
                            for _role in AGENT_ROLES:
                                cleared += bus.clear_queue(_role)
                            if cleared:
                                print(f"  Cleared {cleared} queued message(s) for budget-exceeded project")
                    except Exception:
                        pass

                # If active project is budget_exceeded, advance to next project.
                # Check has_active_work() not all_empty — all_empty only counts
                # If active project is budget_exceeded, advance to next project.
                # NOTE: Do NOT gate this on has_active_work() — other projects may
                # be running in parallel and would keep this permanently stuck.
                if idea_state.get("status") == "budget_exceeded":
                    slug = idea_state.get("_slug", "")
                    orphaned = _rebuild_queues_from_state(bus)
                    if orphaned:
                        print(f"  ▶️  Advancing past '{slug}' → {orphaned} project(s) queued")
                    elif from_list and not bus.has_active_work():
                        # Only seed/ideate when the bus is truly idle (no other projects)
                        seeded = seed_from_master_list(bus)
                        if seeded:
                            ideation_in_progress = False
                        elif not ideation_in_progress:
                            _request_ideation(bus)
                            ideation_in_progress = True

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

                # Ollama GPU heartbeat (checks every 5 min, cached otherwise)
                gpu_str = ""
                if provider == "ollama":
                    gpu_status = _check_ollama_heartbeat(model)
                    if gpu_status:
                        if "IDLE" in gpu_status or "ERR" in gpu_status:
                            gpu_str = f" ⚠️ {gpu_status} — model evicted from VRAM!"
                        else:
                            gpu_str = f" {gpu_status}"

                status_line = _clean(
                    f"  [{elapsed_m:.0f}m] agents={running_agents}/{len(AGENT_ROLES)} "
                    f"pending={pending_total} phase={phase}{task_str}{gpu_str}{title_str}"
                )
                # Always print on a new line — ’\r’ tricks break on cloud/Windows terminals.
                # Throttle to every 4 checks (~4 min) to keep output readable.
                if _status_count % 4 == 0:
                    print(status_line, flush=True)
                _status_count += 1


                if all_empty and not from_list:
                    # Single idea mode — might be done
                    # Wait a bit longer to make sure nothing new arrives
                    time.sleep(10)
                    if bus.all_queues_empty():
                        print(f"\n  ✓ All queues empty — pipeline complete.")
                        break
                elif all_empty and from_list:
                    if not bus.has_active_work():
                        now = time.time()
                        if now - last_orphan_requeue >= ORPHAN_REQUEUE_COOLDOWN:
                            orphaned = _rebuild_queues_from_state(bus)
                            if orphaned:
                                last_orphan_requeue = now
                                print(f"  🔁 Re-queued {orphaned} orphaned project(s) — not seeding new ideas yet")
                            else:
                                seeded = seed_from_master_list(bus)
                                if seeded:
                                    ideation_in_progress = False
                                elif not ideation_in_progress:
                                    _request_ideation(bus)
                                    ideation_in_progress = True

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

    args = parser.parse_args()

    if not args.idea and not args.from_list and not args.resume:
        parser.print_help()
        print("\nProvide an idea, use --from-list, or --resume.")
        sys.exit(1)

    run_pipeline(
        idea=args.idea,
        from_list=args.from_list,
        resume=args.resume,
        provider=args.provider,
        model=args.model,
        time_limit_minutes=args.time_limit,
    )


if __name__ == "__main__":
    main()
