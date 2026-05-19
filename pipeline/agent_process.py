"""
pipeline/agent_process.py
Base class for all pipeline agents.

Each agent runs as a subprocess, polling its queue and processing messages.
The base class handles:
  - Queue polling
  - System prompt construction (from prompts/ markdown files)
  - Calling the core ReAct loop (agent.py::run_agent)
  - Sending results downstream
  - Logging
  - Graceful shutdown
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from agent import AgentResult  # noqa: F401 — type-checker only

# Ensure project root is on path
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.message_bus import MessageBus, Message

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Strategy 1: Pipeline role ordering — used by async double-buffering
# Maps each agent to the role most likely to receive its output next.
# Preloading context for that role while current LLM generates = zero wait.
# ---------------------------------------------------------------------------
_NEXT_ROLE_MAP: dict[str, str] = {
    "idea_planner":  "phase_planner",
    "phase_planner": "executor",
    "executor":      "reviewer",
    "reviewer":      "validator",
    "validator":     "executor",   # retries go back to executor
    "manager":       "phase_planner",
    "documenter":    "manager",
}

# Single source of truth for the default model.
# The runner sets PIPELINE_MODEL env var before spawning agents so all
# subprocesses automatically use the same model without hardcoding.
# Override: PIPELINE_MODEL=qwen3.6:35b-a3b-q4_K_M python pipeline/runner.py ...
DEFAULT_MODEL = os.environ.get("PIPELINE_MODEL", "qwen3.5:35b")
DEFAULT_PROVIDER = os.environ.get("PIPELINE_PROVIDER", "ollama")

# Always anchor .pipeline/ to the project root (this file's grandparent),
# not the cwd — prevents /workspace/.pipeline vs /.pipeline splits.
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
PIPELINE_DIR = _PROJECT_ROOT / ".pipeline"
PROJECTS_DIR = PIPELINE_DIR / "projects"   # per-idea isolation root
PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"
LOGS_DIR = PIPELINE_DIR / "logs"


# ---------------------------------------------------------------------------
# Agent result from a single handle() call
# ---------------------------------------------------------------------------

@dataclass
class AgentOutput:
    """Structured output from one agent processing cycle."""
    success: bool = True
    answer: str = ""
    outgoing: list[Message] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    error: str = ""
    tokens_used: int = 0
    steps_used: int = 0


# ---------------------------------------------------------------------------
# Base agent process
# ---------------------------------------------------------------------------

class AgentProcess:
    """
    Base class for all pipeline agents.

    Subclasses must implement:
      - role (class attribute): str — the agent's role name
      - handle(msg: Message) -> AgentOutput — process one message

    Optionally override:
      - build_context(msg) — add extra context to the system prompt
      - max_steps — how many ReAct steps this agent gets
    """

    role: str = "base"
    max_steps: int = 20
    phase_timeout: int = 2700   # 45 min wall-clock per handle() call — override per agent
    poll_interval: float = 2.0   # seconds between queue checks

    # Per-role LLM tuning — subclasses override to match cognitive load of the task.
    temperature: float = 0.4     # moderate determinism by default
    num_ctx: int = 16384         # 16k context prevents code truncation (Ollama default is ~4k)
    think: bool | None = None    # None=model default; False=disable Qwen3 chain-of-thought


    def __init__(
        self,
        provider: str = DEFAULT_PROVIDER,
        model: str = DEFAULT_MODEL,
        bus: MessageBus | None = None,
    ):
        self.provider = provider
        self.model = model
        self.bus = bus or MessageBus()
        self._stop_requested = False
        self._current_slug = "unknown"   # set from message payload before each handle()
        # Anchor to project root so all path resolution is consistent,
        # regardless of which directory the runner was invoked from.
        self._run_dir = _PROJECT_ROOT
        self._setup_logging()
        self._setup_signal_handlers()

    # --- Lifecycle ---

    def run_loop(self) -> None:
        """Main loop: poll queue → handle → send results. Runs until stopped."""
        # Recover any messages stuck in 'processing' state from a previous crash
        self._recover_processing_messages()

        logger.info("[%s] Starting agent loop (provider=%s, model=%s)",
                    self.role, self.provider, self.model)

        # Adaptive poll back-off: immediately re-poll after work, ramp to max on idle.
        _POLL_MIN  = 0.1   # seconds — retry immediately after a hit
        _POLL_MAX  = 2.0   # seconds — cap on idle sleep
        _POLL_STEP = 0.25  # seconds — additive back-off increment per miss
        _poll_wait = _POLL_MIN

        while not self._stop_requested:
            msg = self.bus.read_next(self.role)

            if msg is None:
                time.sleep(_poll_wait)
                # Ramp up sleep on consecutive misses, cap at max
                _poll_wait = min(_poll_wait + _POLL_STEP, _POLL_MAX)
                continue

            # Got a message — reset back-off so next check is immediate
            _poll_wait = _POLL_MIN

            # Handle signals specially
            if msg.type == "signal":
                self._handle_signal(msg)
                self.bus.ack(msg)
                continue

            logger.info("[%s] Processing message %s from %s (type=%s)",
                        self.role, msg.msg_id, msg.from_agent, msg.type)

            try:
                # Bind the current idea slug so all path helpers use the right project dir
                if msg.type != "signal":
                    self._current_slug = msg.payload.get("idea_slug", self._current_slug)

                # Measure queue wait time (time from message creation to now)
                try:
                    from datetime import datetime, timezone
                    _created = datetime.fromisoformat(msg.created_at)
                    _queue_wait_s = (datetime.now(timezone.utc) - _created).total_seconds()
                except Exception:
                    _queue_wait_s = 0.0
                _handle_start = time.time()

                # Run handle() in a thread so we can enforce a wall-clock timeout
                _result: list[Any] = [None]
                _exc: list[Optional[Exception]] = [None]

                def _run_handle() -> None:
                    try:
                        _result[0] = self.handle(msg)
                    except Exception as e:
                        _exc[0] = e

                t = threading.Thread(target=_run_handle, daemon=True)
                t.start()
                t.join(timeout=self.phase_timeout)

                if t.is_alive():
                    # Agent timed out — escalate to manager
                    timeout_min = self.phase_timeout // 60
                    logger.warning(
                        "[%s] Timed out after %d min on message %s",
                        self.role, timeout_min, msg.msg_id
                    )
                    timeout_msg = Message.create(
                        from_agent=self.role,
                        to_agent="manager",
                        type="signal",
                        payload={
                            "signal": "PHASE_STUCK",
                            "reason": f"{self.role} timed out after {timeout_min} minutes",
                            "phase": msg.payload.get("phase", "?"),
                            "idea_slug": self._current_slug,
                        },
                    )
                    self.bus.send(timeout_msg)
                    self.bus.fail(msg)   # Don't retry a timed-out message
                    continue

                if _exc[0] is not None:
                    raise _exc[0]

                output = _result[0]

                # Send outgoing messages
                for out_msg in output.outgoing:
                    self.bus.send(out_msg)
                    logger.info("[%s] Sent %s to %s",
                                self.role, out_msg.type, out_msg.to_agent)

                self.bus.ack(msg)

                # Record timing metrics
                try:
                    _handle_s = time.time() - _handle_start
                    from pipeline.agent_metrics import record as _record_metric
                    _record_metric(
                        role=self.role,
                        slug=self._current_slug,
                        queue_wait_s=_queue_wait_s,
                        handle_s=_handle_s,
                        tokens=output.tokens_used,
                        files_written=len(output.files_written),
                    )
                except Exception:
                    pass  # Never crash over metrics

                logger.info("[%s] Completed message %s (success=%s, tokens=%d, steps=%d)",
                            self.role, msg.msg_id, output.success,
                            output.tokens_used, output.steps_used)

            except Exception as e:
                logger.error("[%s] Failed processing message %s: %s",
                             self.role, msg.msg_id, e, exc_info=True)
                self.bus.nack(msg)
                time.sleep(5)  # back off on failure

        logger.info("[%s] Shutting down", self.role)

    def stop(self) -> None:
        """Request graceful shutdown."""
        self._stop_requested = True

    # --- Core: subclasses implement these ---

    def handle(self, msg: Message) -> AgentOutput:
        """Process a single message. Must be overridden by subclasses."""
        raise NotImplementedError(f"{self.role} must implement handle()")

    def build_context(self, msg: Message) -> str:
        """Optional extra context injected into the system prompt.

        Override to add phase-specific state, file listings, etc.
        """
        return ""

    # --- Per-idea project directory ---

    @property
    def _project_dir(self) -> pathlib.Path:
        """Absolute path to this idea's isolated project directory.

        Uses the cwd captured at agent startup so all paths are anchored
        to the correct location regardless of LLM tool resolution.
        """
        d = self._run_dir / ".pipeline" / "projects" / self._current_slug
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _project_path(self, relative: str) -> str:
        """Return the ABSOLUTE path string for use in LLM prompts.

        Absolute paths prevent the LLM from mis-resolving relative paths
        against a different working directory.
        Example: '/workspace/idea impl/.pipeline/projects/csv_analyzer/state/master_plan.md'
        """
        return str(self._project_dir / relative)

    def _update_idea_status(self, status: str, phase_num: int | None = None) -> None:
        """Write a quick status update to current_idea.json for the runner's display.

        Also reads task checkbox counts from the phase tasks.md so the status
        line can show '3/8 tasks' alongside the phase name.

        IMPORTANT: Never overwrites 'complete' or 'stalled' — those are terminal
        states set by the runner/manager.  In-flight agents may finish after a
        force-complete; their status writes must be silently ignored.
        """
        try:
            existing = self.read_json_state("state/current_idea.json")

            # Guard: terminal states are sacred — never overwrite them
            if existing.get("status") in ("complete", "stalled", "budget_exceeded"):
                return

            existing["status"] = status

            # Invalidate rolling context when phase boundary is crossed
            # (new phase = fresh workspace state; prior exchanges no longer relevant)
            old_status = existing.get("status", "")
            if (
                old_status != status
                and "_planning" in status
                and "_planning" not in old_status
            ):
                try:
                    from pipeline.rolling_context import get_context_store
                    get_context_store().invalidate(self._current_slug)
                except Exception:
                    pass

            # Optionally count task progress — ONLY for the current phase
            if phase_num is not None:
                import re as _re
                tasks_content = self.read_state_file(f"phases/phase_{phase_num}/tasks.md")
                phase_tasks = self._extract_phase_tasks(tasks_content, phase_num)
                if phase_tasks:
                    total = len(_re.findall(r'^- \[[ x]\]', phase_tasks, _re.MULTILINE))
                    done  = len(_re.findall(r'^- \[x\]', phase_tasks, _re.MULTILINE | _re.IGNORECASE))
                    existing["tasks_done"] = done
                    existing["tasks_total"] = total

            self.write_json_state("state/current_idea.json", existing)
        except Exception:
            pass  # Non-critical — don't break the pipeline over a status update

    @staticmethod
    def _extract_phase_tasks(tasks_content: str, phase_num: int) -> str:
        """Extract only the current phase's task section from tasks.md.

        Some tasks.md files contain all phases in one file.  This extracts
        ONLY the section belonging to `phase_num` so that task counts and
        validation are scoped correctly.

        Heuristic: find the heading that matches 'Phase <N>' (any level),
        then capture everything until the next 'Phase <N+1>' heading or EOF.
        If no phase heading is found, return the full content (single-phase file).
        """
        import re as _re
        # Match ## Phase 1, ### Phase 1, # Phase 1: ..., etc.
        # NOTE: {{1,4}} is required — {1,4} in rf-strings becomes a set literal!
        pattern = rf'^(#{{1,4}})\s+(?:.*?)?Phase\s+{phase_num}\b.*$'
        match = _re.search(pattern, tasks_content, _re.MULTILINE | _re.IGNORECASE)
        if not match:
            return tasks_content  # No phase heading — assume whole file is this phase

        start = match.start()
        # Find the NEXT phase heading (Phase N+1, N+2, etc.)
        next_pattern = rf'^#{{1,4}}\s+(?:.*?)?Phase\s+(?:{phase_num + 1}|{phase_num + 2}|{phase_num + 3})\b'
        next_match = _re.search(next_pattern, tasks_content[match.end():], _re.MULTILINE | _re.IGNORECASE)
        if next_match:
            end = match.end() + next_match.start()
        else:
            end = len(tasks_content)

        return tasks_content[start:end]

    @staticmethod
    def _normalize_tasks_format(content: str) -> str:
        """Normalize any LLM task format to canonical '- [ ] Task N: title'.

        Handles these common LLM deviations:
          ## Task 1: title       -> - [ ] Task 1: title
          ### Task 1: title      -> - [ ] Task 1: title
          **Task 1**: title      -> - [ ] Task 1: title
          1. Task 1: title       -> - [ ] Task 1: title (numbered lists)
          - [ x ] ...            -> - [x] ... (space inside brackets)
        """
        import re as _re
        lines = content.splitlines()
        out = []
        for line in lines:
            # ## Task N: or ### Task N: headings
            m = _re.match(r'^#+\s+(Task\s+\d+[:.]\s*.+)', line, _re.IGNORECASE)
            if m:
                out.append(f"- [ ] {m.group(1)}")
                continue
            # **Task N**: title or **Task N: title**
            m = _re.match(r'^\*\*(Task\s+\d+)[:\.]?\*\*[:\s]*(.*)', line, _re.IGNORECASE)
            if m:
                out.append(f"- [ ] {m.group(1)}: {m.group(2)}".rstrip(": "))
                continue
            # Numbered list: 1. Task N: ... or 1. title
            m = _re.match(r'^\d+\.\s+(Task\s+\d+[:.].+)', line, _re.IGNORECASE)
            if m:
                out.append(f"- [ ] {m.group(1)}")
                continue
            # Fix space inside brackets: - [ x ] or - [X ]
            line = _re.sub(r'^(\s*- \[)\s*([xX])\s*(\])', r'\1\2\3', line)
            out.append(line)
        return "\n".join(out)

    @classmethod
    def normalize_tasks_file(cls, tasks_path: "pathlib.Path") -> bool:
        """Normalize a tasks.md file in-place. Returns True if changes were made."""
        import pathlib
        p = pathlib.Path(tasks_path)
        if not p.exists():
            return False
        raw = p.read_text(encoding="utf-8")
        normalized = cls._normalize_tasks_format(raw)
        if normalized != raw:
            p.write_text(normalized, encoding="utf-8")
            return True
        return False


    # --- Prompt construction ---

    def load_system_prompt(self) -> str:
        """Load the agent's system prompt from its markdown template."""
        prompt_path = PROMPTS_DIR / f"{self.role}.md"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        logger.warning("[%s] No prompt file found at %s", self.role, prompt_path)
        return f"You are the {self.role} agent in an idea development pipeline."

    def build_full_prompt(self, msg: Message) -> str:
        """Construct the complete task prompt for the ReAct loop."""
        base_prompt = self.load_system_prompt()
        context = self.build_context(msg)

        sections = [base_prompt]

        if context:
            sections.append(f"\n## Current Context\n{context}")

        if msg.payload:
            sections.append(f"\n## Task Payload\n```json\n{json.dumps(msg.payload, indent=2)}\n```")

        return "\n\n".join(sections)

    # --- Helper: call the core ReAct agent ---

    def call_agent(
        self,
        task: str,
        system_prompt_addon: str = "",
        max_steps: int | None = None,
        verbose: bool = False,
    ) -> "AgentResult":
        """Run the core ReAct loop from agent.py with per-role LLM settings.

        Enhancements over the bare run_agent() call:
        - Injects the last 3 exchanges (rolling context) as a compact context
          block so the model has continuity without re-reading workspace files.
        - Saves the prompt+response pair after each call so future calls can
          reference them via the same rolling context window.
        - Invalidates the rolling context when the project phase changes.
        - Strategy 1: Launches a daemon thread that pre-warms the context
          aggregator cache for the NEXT likely agent while this LLM generates.
        - Strategy 5: Injects a compact prompt header (role/project/phase ref)
          so the model skips re-reading boilerplate on KV-cache hits.
        """
        from agent import run_agent

        # --- Strategy 5: Compact prompt header (reference, not repetition) ---
        # On KV-cache hits the static system prompt is already tokenised.
        # Prepend a tiny [ROLE:x][PROJECT:y][PHASE:z] header so the model
        # immediately knows its context without re-reading the full preamble.
        try:
            _state = self.read_json_state("state/current_idea.json")
            _phase_n = _state.get("phase", "?")
            _slug_ref = self._current_slug
            _hdr = f"[ROLE:{self.role}] [PROJECT:{_slug_ref}] [PHASE:{_phase_n}]\n"
            task = _hdr + task
        except Exception:
            pass

        # --- Rolling context: inject prior exchanges ---
        try:
            from pipeline.rolling_context import get_context_store
            _rc_store = get_context_store(n=3)
            prior = _rc_store.format_for_prompt(
                slug=self._current_slug,
                role=self.role,
                n=3,
            )
            if prior:
                prior_block = (
                    "\n\n## Prior Exchanges (this project, this role — most recent last)\n"
                    + prior
                    + "\n(End of prior exchanges. Continue from where you left off.)"
                )
                system_prompt_addon = (system_prompt_addon + prior_block) if system_prompt_addon else prior_block
        except Exception:
            pass  # non-critical — never break the agent for a context load failure

        # --- Strategy 1: Async double-buffering — pre-warm next agent's context ---
        # While this call_agent() runs the LLM, a daemon thread pre-loads the
        # context aggregator cache for the next role in the pipeline.  By the
        # time this agent finishes and the message arrives at the next agent,
        # its context read (tasks.md, workspace tree, validation_report) is
        # already in memory — zero extra I/O wait on the critical path.
        _preload_thread: threading.Thread | None = None
        try:
            _next_role = _NEXT_ROLE_MAP.get(self.role, "")
            if _next_role and self._current_slug:
                _slug_for_preload = self._current_slug

                def _preload_next_context() -> None:
                    """Background preload — errors silently swallowed."""
                    try:
                        from pipeline.context_aggregator import get_aggregator
                        agg = get_aggregator()
                        agg.build(slug=_slug_for_preload, force=False)
                    except Exception:
                        pass

                _preload_thread = threading.Thread(
                    target=_preload_next_context,
                    daemon=True,
                    name=f"ctx-preload-{_next_role}-{_slug_for_preload[:8]}",
                )
                _preload_thread.start()
        except Exception:
            pass

        result = run_agent(
            task=task,
            provider=self.provider,
            model=self.model,
            max_steps=max_steps or self.max_steps,
            temperature=self.temperature,
            think=self.think,
            num_ctx=self.num_ctx,
            system_prompt_addon=system_prompt_addon,
            verbose=verbose,
            pipeline_mode=True,  # skip repo file tree + shared .agent/ memory
            slug=self._current_slug,  # enables Ollama KV-cache reuse per project
        )

        # Preload thread is daemon — no need to join; it will finish naturally.
        # If it's still running when we return, the context build completes in
        # the background before the next agent polls.

        # --- Rolling context: save this exchange ---
        try:
            from pipeline.rolling_context import get_context_store
            _rc_store = get_context_store(n=3)
            _rc_store.push(
                slug=self._current_slug,
                role=self.role,
                prompt=task[:4000],          # cap to avoid bloat
                response=result.answer[:4000],
                metadata={"steps": result.steps_used, "tokens": result.tokens_used},
            )
        except Exception:
            pass  # non-critical

        return result

    # --- Helper: read/write per-idea project state files ---

    def read_state_file(self, relative_path: str) -> str:
        """Read a file from this idea's project directory."""
        path = self._project_dir / relative_path
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def write_state_file(self, relative_path: str, content: str) -> None:
        """Write a file to this idea's project directory."""
        path = self._project_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def read_json_state(self, relative_path: str) -> dict:
        """Read a JSON state file."""
        content = self.read_state_file(relative_path)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {}
        return {}

    def write_json_state(self, relative_path: str, data: dict) -> None:
        """Write a JSON state file."""
        self.write_state_file(relative_path, json.dumps(data, indent=2))

    def record_file_changes(
        self,
        changed_files: list[str],
        reason: str,
    ) -> None:
        """Append a deferred review notice when files are changed mid-phase.

        The reviewer reads state/pending_review_notes.md at review time
        and checks for regressions caused by these changes.
        This is a zero-interrupt, zero-overhead notification pattern.
        """
        if not changed_files:
            return
        try:
            from datetime import datetime, timezone
            notes_path = self._project_dir / "state" / "pending_review_notes.md"
            existing = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""
            new_entry = (
                f"\n## Change Notice — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"**Reason:** {reason}\n"
                f"**Modified files:**\n"
                + "\n".join(f"- `{f}`" for f in changed_files)
                + "\n\nVerify these changes don't introduce regressions in dependent code.\n"
            )
            notes_path.parent.mkdir(parents=True, exist_ok=True)
            notes_path.write_text(existing + new_entry, encoding="utf-8")
        except Exception:
            pass  # Non-critical

    def get_current_phase(self) -> dict:
        """Read current phase state."""
        return self.read_json_state("state/current_phase.json")

    def get_workspace_path(self) -> pathlib.Path:
        """Return the workspace path for generated code (per-idea)."""
        ws = self._project_dir / "workspace"
        ws.mkdir(parents=True, exist_ok=True)
        return ws

    # --- Signal handling ---

    def _handle_signal(self, msg: Message) -> None:
        """Process signal messages."""
        sig = msg.payload.get("signal", "")
        logger.info("[%s] Received signal: %s from %s", self.role, sig, msg.from_agent)

        if sig == "SHUTDOWN":
            self.stop()
        elif sig == "PAUSE":
            logger.info("[%s] Paused — waiting for RESUME", self.role)
            while not self._stop_requested:
                resume = self.bus.read_next(self.role)
                if resume and resume.type == "signal" and resume.payload.get("signal") == "RESUME":
                    self.bus.ack(resume)
                    logger.info("[%s] Resumed", self.role)
                    break
                if resume:
                    self.bus.nack(resume)  # put non-resume messages back
                time.sleep(1)

    def _setup_signal_handlers(self) -> None:
        """Handle OS-level signals for graceful shutdown."""
        def _handler(signum, frame):
            logger.info("[%s] Received signal %s, requesting stop", self.role, signum)
            self._stop_requested = True

        try:
            signal.signal(signal.SIGINT, _handler)
            signal.signal(signal.SIGTERM, _handler)
        except (OSError, ValueError):
            pass  # can't set signal handlers in non-main threads

    def _recover_processing_messages(self) -> None:
        """On startup, reset stuck 'processing' messages and discard stale SHUTDOWNs.

        If a subprocess crashed mid-handle(), those messages are stuck in
        'processing' and invisible to read_next(). This makes them retryable.

        Also discards any SHUTDOWN signals left in the queue from a previous
        pipeline run — these would otherwise cause agents to immediately exit
        on every restart.

        NOTE: MessageBus is SQLite-backed (Strategy 2). The old file-based
        _queue_path/_read_lines/_write_lines methods no longer exist.
        """
        from pipeline.message_bus import _get_conn

        conn = _get_conn(self.bus._db)

        # Reset any messages stuck in 'processing' for THIS agent
        cur = conn.execute(
            "UPDATE messages SET status='pending' WHERE to_agent=? AND status='processing'",
            (self.role,),
        )
        recovered = cur.rowcount
        if recovered:
            conn.commit()
            logger.warning("[%s] Recovered %d stuck processing message(s)",
                           self.role, recovered)

        # Discard stale SHUTDOWN signals left from a previous pipeline run
        cur = conn.execute(
            """UPDATE messages SET status='done'
               WHERE to_agent=? AND status='pending'
               AND type='signal'
               AND json_extract(payload, '$.signal')='SHUTDOWN'""",
            (self.role,),
        )
        discarded = cur.rowcount
        if discarded:
            conn.commit()
            logger.info("[%s] Discarded %d stale SHUTDOWN signal(s)",
                        self.role, discarded)

    def _setup_logging(self) -> None:
        """Configure per-agent log file."""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / f"{self.role}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
        ))

        agent_logger = logging.getLogger(f"pipeline.{self.role}")
        agent_logger.addHandler(file_handler)
        agent_logger.setLevel(logging.INFO)

        # Also add to the module logger
        logger.addHandler(file_handler)
