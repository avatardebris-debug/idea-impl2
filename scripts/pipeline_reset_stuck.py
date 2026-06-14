#!/usr/bin/env python3
"""
Reset a wedged Ollama + stuck message-bus state before rerunning the pipeline.

  export PIPELINE_CLOUD=1
  python scripts/pipeline_reset_stuck.py
  python pipeline/runner.py "Smoke test: ..." --provider ollama --parallel-seeds 1 --executors 1
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("PIPELINE_CLOUD", "1")


def _run(cmd: list[str]) -> None:
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=False)


def _ollama_alive(timeout: float = 5.0) -> bool:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def main() -> int:
    print("=== Pipeline reset (Ollama + queue) ===\n")

    print("[1/4] Stopping agent subprocesses...")
    _run(["pkill", "-f", "pipeline/agents"])
    _run(["pkill", "-f", "pipeline/runner.py"])
    time.sleep(1)

    print("\n[2/4] Restarting Ollama...")
    _run(["pkill", "-f", "ollama serve"])
    time.sleep(2)
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=open("/tmp/ollama.log", "a", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    for _ in range(15):
        if _ollama_alive():
            print("  ✓ Ollama responding on :11434")
            break
        time.sleep(1)
    else:
        print("  ✗ Ollama not responding — check /tmp/ollama.log")
        return 1

    print("\n[3/4] Clearing message-bus stuck state...")
    from pipeline.message_bus import MessageBus

    bus = MessageBus()
    shutdowns = bus.discard_stale_shutdowns()
    reset = bus.reset_stale_processing()
    deduped = bus.dedupe_pending_tasks("idea_planner", ("idea_slug",))
    print(f"  discarded SHUTDOWN={shutdowns}, reset processing={reset}, deduped={deduped}")

    lock = ROOT / ".pipeline" / "state" / "ollama.lock"
    if lock.exists():
        try:
            lock.unlink()
            print("  removed stale ollama.lock")
        except Exception as exc:
            print(f"  could not remove ollama.lock: {exc}")

    print("\n[4/4] Quick chat probe (10s timeout)...")
    import json

    payload = json.dumps(
        {
            "model": os.environ.get("PIPELINE_MODEL", "qwen3.6:35b-a3b-q4_K_M"),
            "messages": [{"role": "user", "content": "Reply OK"}],
            "stream": False,
            "think": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        snippet = (body.get("message", {}).get("content") or "")[:80]
        print(f"  ✓ Ollama chat OK: {snippet!r}")
    except Exception as exc:
        print(f"  ✗ Ollama chat failed in 10s: {exc}")
        print("    Model may need reloading: ollama run qwen3.6:35b-a3b-q4_K_M")
        return 1

    print("\nDone. Rerun the pipeline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
