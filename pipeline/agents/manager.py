"""
pipeline/agents/manager.py
Manager agent — handles ideator triage and pipeline signals.

Review routing was migrated to the runner's _tick_project() function.
The manager now only handles:
  1. Ideator output triage (categorize ideas into files)
  2. PHASE_STUCK signals (log and let runner handle advancement)
"""

from __future__ import annotations

import json
import logging
import pathlib
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.message_bus import Message

logger = logging.getLogger(__name__)


class ManagerAgent(AgentProcess):
    role = "manager"
    max_steps = 25
    temperature = 0.3   # coordination decisions should be consistent
    think = False       # routing logic is deterministic — CoT not needed

    def handle(self, msg: Message) -> AgentOutput:
        source = msg.payload.get("source", msg.from_agent)
        outgoing = []

        if source == "ideator" or msg.from_agent == "ideator":
            outgoing = self._handle_ideator_result(msg)
        elif msg.from_agent == "reviewer":
            # Review routing is now handled deterministically by the runner's
            # _tick_project() function.  Log and drop.
            self._log_decision(msg, [], note="Review routing now handled by runner — ignored")
        elif msg.type == "signal":
            outgoing = self._handle_pipeline_signal(msg)
        else:
            outgoing = self._handle_generic(msg)

        # Log the decision
        self._log_decision(msg, outgoing)

        return AgentOutput(
            success=True,
            answer=f"Processed {msg.type} from {msg.from_agent}, sent {len(outgoing)} messages",
            outgoing=outgoing,
        )

    # --- Ideator result handling ---

    def _handle_ideator_result(self, msg: Message) -> list[Message]:
        ideator_content = msg.payload.get("ideator_content_preview", "")

        # Use LLM to triage the ideas into separate destinations
        task_prompt = (
            f"You are the Manager triaging Ideator output into separate files.\n\n"
            f"## Ideator Output\n{ideator_content[:3000]}\n\n"
            f"## Current Master Ideas List\n"
            f"{self._read_master_ideas()[:2000]}\n\n"
            f"## Your Job\n"
            f"Categorize each idea into EXACTLY one of these 4 categories:\n"
            f"1. **ADD_TO_PLAN** — extends or improves what is currently being built\n"
            f"2. **REUSABLE_TOOL** — generic utility/library that could work across projects\n"
            f"3. **ADD_TO_BACKLOG** — a distinct new project idea for the future\n"
            f"4. **ARCHIVE** — interesting but not actionable right now\n\n"
            f"Then write EACH category to its own file (append, don't overwrite):\n\n"
            f"- **ADD_TO_PLAN** items → append to `.pipeline/state/plan_amendments.md`\n"
            f"  Format each as: `- [ ] <title>: <what to add and why>`\n\n"
            f"- **REUSABLE_TOOL** items → append to `.pipeline/state/reusable_tools.md`\n"
            f"  Format each as: `- <tool name>: <what it does, which agents/files it lives near>`\n\n"
            f"- **ADD_TO_BACKLOG** items → append to `master_ideas.md`\n"
            f"  Format each as: `- [ ] **<title>** — <one line description>`\n\n"
            f"- **ARCHIVE** items → append to `.pipeline/state/archived_ideas.md`\n"
            f"  Format each as: `- <title>: <reason archived>`\n\n"
            f"Write ALL four files even if a category is empty (just skip writing that one).\n"
            f"Say DONE when finished.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)

        # No outgoing messages needed — the LLM call writes to files directly
        return []

    # --- Signal handling ---

    def _handle_pipeline_signal(self, msg: Message) -> list[Message]:
        sig = msg.payload.get("signal", "")
        if sig == "PHASE_STUCK":
            phase      = msg.payload.get("phase", 0)
            idea_slug  = msg.payload.get("idea_slug", "")
            reason     = msg.payload.get("reason", "unknown")

            self._log_decision(msg, [], note=f"PHASE_STUCK phase={phase}: {reason} — force-advancing now")

            # Force-advance: write 'phase_N_reviewed' with 0 blocking bugs so
            # the runner's next _tick_project() call will advance to phase N+1.
            # The runner checks for 'reviewed' state and routes via _tick_project().
            if idea_slug:
                proj_dir   = pathlib.Path(".pipeline") / "projects" / idea_slug
                state_file = proj_dir / "state" / "current_idea.json"
                retry_file = proj_dir / "state" / "phase_retries.json"
                try:
                    state = json.loads(state_file.read_text(encoding="utf-8"))
                    state["status"] = f"phase_{phase}_reviewed"
                    state["review_result"] = {
                        "blocking_bugs": 0,
                        "non_blocking_notes": f"Force-advanced by manager: {reason}",
                        "tasks_path": f"phases/phase_{phase}/tasks.md",
                        "workspace_path": str(proj_dir / "workspace"),
                        "review_path": f"phases/phase_{phase}/review.md",
                    }
                    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
                    # Clear retry counters for this phase so next phase starts fresh
                    if retry_file.exists():
                        retries = json.loads(retry_file.read_text(encoding="utf-8"))
                        for key in list(retries.keys()):
                            if f"phase_{phase}" in key:
                                retries.pop(key)
                        retry_file.write_text(json.dumps(retries, indent=2), encoding="utf-8")
                    logger.info("[manager] Force-advanced '%s' past phase %d (PHASE_STUCK)", idea_slug, phase)
                except Exception as e:
                    logger.error("[manager] Failed to force-advance '%s': %s", idea_slug, e)

        elif sig == "PHASE_COMPLETE":
            phase = msg.payload.get("phase", 0)
            self._log_decision(msg, [], note=f"PHASE_COMPLETE phase={phase} — runner handles advancement")
        return []

    def _handle_generic(self, msg: Message) -> list[Message]:
        """Fallback handler for unexpected message types."""
        self._log_decision(msg, [], note="Unhandled message type — logged only")
        return []

    # --- Helpers ---

    def _read_master_ideas(self) -> str:
        mi_path = pathlib.Path("master_ideas.md")
        if mi_path.exists():
            return mi_path.read_text(encoding="utf-8")
        return "(no master ideas list)"

    def _log_decision(
        self,
        msg: Message,
        outgoing: list[Message],
        note: str = "",
    ) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        destinations = [f"{m.to_agent}({m.type})" for m in outgoing]
        entry = (
            f"\n## {ts}\n"
            f"- **Input**: {msg.type} from {msg.from_agent} "
            f"(phase={msg.payload.get('phase', '?')})\n"
            f"- **Routed to**: {', '.join(destinations) if destinations else 'none'}\n"
        )
        if note:
            entry += f"- **Note**: {note}\n"

        decisions_path = pathlib.Path(".pipeline/state/manager_decisions.md")
        decisions_path.parent.mkdir(parents=True, exist_ok=True)
        with open(decisions_path, "a", encoding="utf-8") as f:
            f.write(entry)


def main():
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default=__import__("os").environ.get("PIPELINE_MODEL", "qwen3.5:35b"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [manager] %(message)s")

    agent = ManagerAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
