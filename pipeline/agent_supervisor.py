"""
pipeline/agent_supervisor.py
Agent subprocess lifecycle management.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

from pipeline.message_bus import MessageBus
from pipeline.paths import logs_dir, state_dir
from pipeline.pipeline_config import AGENT_ROLES, AGENTS_DIR, PROJECT_ROOT

class AgentSupervisor:
    """Manages agent subprocesses."""

    def __init__(self, provider: str, model: str, num_executors: int = 1, legacy: bool = False):
        self.provider = provider
        self.model = model
        self.num_executors = max(1, num_executors)
        self.legacy = legacy
        self.processes: dict[str, subprocess.Popen] = {}
        self._stop_requested = False

    def start_agent(self, role: str, key_override: str | None = None) -> subprocess.Popen:
        """Start an agent as a subprocess.

        key_override: if set, use as the registry key instead of role.
        Used to spawn multiple executor instances (executor_0, executor_1, ...).
        """
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
        if self.legacy:
            env["PIPELINE_LEGACY"] = "1"
            env.pop("PIPELINE_CAPABILITY_TOOLS", None)
        else:
            env.pop("PIPELINE_LEGACY", None)
            env["PIPELINE_CAPABILITY_TOOLS"] = "1"

        _key = key_override or role
        log_path = logs_dir() / f"{_key}.out"
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

        self.processes[_key] = proc
        return proc

    def start_all(self) -> None:
        """Start all agent subprocesses."""
        MessageBus().discard_stale_shutdowns()
        for role in AGENT_ROLES:
            if role == "executor" and self.num_executors > 1:
                # Spawn multiple executor instances — SQLite bus competing consumers
                # handles mutual exclusion so they never double-claim the same message.
                for _ei in range(self.num_executors):
                    _key = f"executor_{_ei}"
                    proc = self.start_agent(role, key_override=_key)
                    print(f"  ✓ Started {_key} (PID {proc.pid})")
                    time.sleep(0.3)
            else:
                self.start_agent(role)
                print(f"  ✓ Started {role} (PID {self.processes[role].pid})")
                time.sleep(0.5)  # stagger starts slightly

    def stop_all(self) -> None:
        """Gracefully stop all agent subprocesses."""
        self._stop_requested = True

        # Send shutdown signal via message bus.
        # Send multiple SHUTDOWN signals to executor if multiple instances running.
        bus = MessageBus()
        for role in AGENT_ROLES:
            if role == "executor" and self.num_executors > 1:
                for _ in range(self.num_executors):
                    bus.send_signal("runner", "executor", "SHUTDOWN")
            else:
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
        for key, proc in list(self.processes.items()):
            if proc.poll() is not None and not self._stop_requested:
                print(f"  ⚠ {key} died (exit={proc.returncode}), restarting...")
                # Derive role from key: "executor_0" -> "executor", "manager" -> "manager"
                role = key.rsplit("_", 1)[0] if key[-1].isdigit() else key
                key_override = key if key != role else None
                MessageBus().discard_stale_shutdowns()
                self.start_agent(role, key_override=key_override)
                restarted.append(key)
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
        path = state_dir() / "agent_registry.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
