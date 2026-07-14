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
from pipeline.paths import get_pipeline_dir, project_dir, state_dir

logger = logging.getLogger(__name__)


class ManagerAgent(AgentProcess):
    role = "manager"
    model_tier = "light"
    num_ctx = 4096
    max_steps = 25
    temperature = 0.3   # coordination decisions should be consistent
    think = False       # routing logic is deterministic — CoT not needed

    def handle(self, msg: Message) -> AgentOutput:
        source = msg.payload.get("source", msg.from_agent)
        outgoing = []

        if msg.type == "dropbox_user":
            answer = self._handle_dropbox_user(msg)
            self._log_decision(msg, [], note=f"dropbox {msg.payload.get('msg_id', '?')}")
            return AgentOutput(success=True, answer=answer, outgoing=[])

        if source == "ideator" or msg.from_agent == "ideator":
            outgoing = self._handle_ideator_result(msg)
        elif msg.payload.get("signal") == "FIX_ANALYSIS_NEEDED":
            # Validator sends this as type="task" when retry count >= 3
            outgoing = self._handle_pipeline_signal(msg)
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
            f"Categorize each idea into EXACTLY one of these 5 categories:\n"
            f"1. **ADD_TO_PLAN** — extends or improves what is currently being built\n"
            f"2. **REUSABLE_TOOL** — generic utility/library that could work across projects\n"
            f"3. **ADD_TO_BACKLOG** — a distinct new project idea for the future\n"
            f"4. **CAPABILITY_GAP** — no existing verified tool covers this; pipeline should build it\n"
            f"5. **ARCHIVE** — interesting but not actionable right now\n\n"
            f"Then write EACH category to its own file (append, don't overwrite).\n"
            f"Use these absolute paths (pipeline output dir — not a hardcoded .pipeline):\n\n"
            f"- **ADD_TO_PLAN** → `{get_pipeline_dir() / 'state' / 'plan_amendments.md'}`\n"
            f"  Format: `- [ ] <title>: <what to add and why>`\n\n"
            f"- **REUSABLE_TOOL** → `{get_pipeline_dir() / 'state' / 'reusable_tools.md'}`\n"
            f"  Format: `- <tool name>: <what it does>`\n\n"
            f"- **ADD_TO_BACKLOG** → `master_ideas.md` (repo root or configured ideas path)\n"
            f"  Format: `- [ ] **<title>** — <one line description>`\n\n"
            f"- **CAPABILITY_GAP** → `{get_pipeline_dir() / 'state' / 'capability_gaps.md'}`\n"
            f"  Format: `- [ ] **<title>** — <what tool is missing and why>`\n\n"
            f"- **ARCHIVE** → `{get_pipeline_dir() / 'state' / 'archived_ideas.md'}`\n"
            f"  Format: `- <title>: <reason archived>`\n\n"
            f"Write ALL five files even if a category is empty (just skip writing that one).\n"
            f"Before categorizing, call suggest_capabilities mentally: prefer REUSABLE_TOOL or "
            f"ADD_TO_BACKLOG with requires: slugs when a verified capability already fits.\n"
            f"Say DONE when finished.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)

        # No outgoing messages needed — the LLM call writes to files directly
        return []

    def _handle_dropbox_user(self, msg: Message) -> str:
        """Triage a user dropbox.md message; steer projects and reply in dropbox."""
        from pipeline.dropbox import append_manager_reply, apply_project_steer

        msg_id = msg.payload.get("msg_id", "")
        body = msg.payload.get("body", "")
        target = msg.payload.get("target_slug", "") or msg.payload.get("active_slug", "")
        ideas_path = msg.payload.get("ideas_path", "master_ideas.md")

        mi = self._read_master_ideas()[:2500]
        pipe = get_pipeline_dir()
        steer_path = ""
        if target:
            sp = project_dir(target) / "state" / "user_steer.md"
            if sp.exists():
                steer_path = sp.read_text(encoding="utf-8")[-1500:]
                steer_path_display = str(sp)
            else:
                steer_path_display = str(sp)
        else:
            steer_path_display = str(project_dir("slug") / "state" / "user_steer.md")

        task_prompt = (
            f"You are the Manager handling a USER dropbox message while the pipeline runs.\n\n"
            f"## User message (id={msg_id})\n{body}\n\n"
            f"## Target project slug\n{target or '(none — general pipeline)'}\n\n"
            f"## Prior steering for this project\n{steer_path or '(none)'}\n\n"
            f"## Master ideas (excerpt)\n{mi}\n\n"
            f"## Your job\n"
            f"1. Decide action(s): STEER_PROJECT | PLAN_AMENDMENT | BACKLOG_IDEA | "
            f"CAPABILITY_GAP | REPLY_ONLY | NEEDS_INFO\n"
            f"2. If steering a project, write concise bullet instructions agents should follow.\n"
            f"3. If NEEDS_INFO, ask specific clarifying questions.\n"
            f"4. Append files using write_file:\n"
            f"   - Project steer: `{steer_path_display}` (append)\n"
            f"   - Plan tweak: `{pipe / 'state' / 'plan_amendments.md'}` (append `- [ ] ...`)\n"
            f"   - New idea: `{ideas_path}` (append `- [ ] **Title** — desc` only if user asked)\n"
            f"   - Gap: `{pipe / 'state' / 'capability_gaps.md'}` (append if tooling missing)\n"
            f"5. End your answer with a block:\n"
            f"   DROPBOX_REPLY:\n"
            f"   status: ok | needs_info\n"
            f"   (user-facing reply, 2-6 sentences)\n"
            f"Say DONE when files are updated.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)
        answer = result.answer or ""

        reply_body = answer
        status = "ok"
        if "DROPBOX_REPLY:" in answer:
            parts = answer.split("DROPBOX_REPLY:", 1)[1].strip()
            if "status: needs_info" in parts.lower():
                status = "needs_info"
            reply_body = re.sub(r"status:\s*\w+\s*", "", parts, flags=re.I).strip()

        if target and body and status == "ok":
            try:
                apply_project_steer(target, body, source_msg_id=msg_id)
            except Exception as e:
                logger.warning("[manager] dropbox steer file failed: %s", e)

        append_manager_reply(msg_id, reply_body[:2000], status=status)
        return f"dropbox {msg_id} -> {status}"

    # --- Signal handling ---

    def _handle_pipeline_signal(self, msg: Message) -> list[Message]:
        sig = msg.payload.get("signal", "")
        if sig == "FIX_ANALYSIS_NEEDED":
            return self._handle_fix_analysis(msg)
        elif sig == "PHASE_STUCK":
            phase = msg.payload.get("phase", 0)
            idea_slug = msg.payload.get("idea_slug", "")
            reason = msg.payload.get("reason", "unknown")

            self._log_decision(msg, [], note=f"PHASE_STUCK phase={phase}: {reason} — force-advancing now")

            if idea_slug:
                from pipeline.force_advance import force_advance_phase

                ok = force_advance_phase(
                    idea_slug,
                    int(phase or 0),
                    f"Force-advanced by manager (PHASE_STUCK): {reason}",
                    retry_count=3,
                )
                if ok:
                    logger.info("[manager] Force-advanced '%s' past phase %d (PHASE_STUCK)", idea_slug, phase)
                else:
                    logger.error("[manager] Failed to force-advance '%s'", idea_slug)

        elif sig == "PHASE_COMPLETE":
            phase = msg.payload.get("phase", 0)
            self._log_decision(msg, [], note=f"PHASE_COMPLETE phase={phase} — runner handles advancement")
        return []

    def _handle_fix_analysis(self, msg: Message) -> list[Message]:
        """Manager LLM analyzes persistent failures and decides path forward.

        Called on retry 3+ when the executor has failed to fix issues twice.
        The manager reads the full fix_report.md, diagnoses the root cause,
        and decides: retry with a specific strategy, or force-advance.
        """
        phase_num = msg.payload.get("phase", 1)
        idea_slug = msg.payload.get("idea_slug", "")
        fix_report_path = msg.payload.get("fix_report_path", "")
        retry_count = msg.payload.get("retry_count", 3)
        current_failures = msg.payload.get("current_failures", 0)
        made_progress = msg.payload.get("made_progress", False)
        workspace_path = msg.payload.get("workspace_path", "")
        tasks_path = msg.payload.get("tasks_path", "")

        # Read the full fix report
        fix_report_content = ""
        if fix_report_path and idea_slug:
            proj_dir = project_dir(idea_slug)
            fr_full = proj_dir / fix_report_path
            if fr_full.exists():
                fix_report_content = fr_full.read_text(encoding="utf-8")

        # Ask manager LLM to analyze
        task_prompt = (
            f"You are the Manager analyzing a STUCK project.\n\n"
            f"## Situation\n"
            f"Project '{idea_slug}' phase {phase_num} has FAILED validation {retry_count} times.\n"
            f"Current failures: {current_failures}\n"
            f"Making progress: {'yes' if made_progress else 'NO — same failures each attempt'}\n\n"
            f"## Fix Report (full history of all attempts)\n"
            f"{fix_report_content[:8000]}\n\n"
            f"## Your Job\n"
            f"1. Read the fix report carefully.\n"
            f"2. Identify the ROOT CAUSE pattern — why do fixes keep failing?\n"
            f"   Common patterns:\n"
            f"   - File path issues (files in wrong directory)\n"
            f"   - Missing dependencies (imports that can't resolve)\n"
            f"   - Test environment issues (tests assume something unavailable)\n"
            f"   - Fundamental design mistake (wrong approach entirely)\n"
            f"3. Write your analysis to `{state_dir() / 'manager_decisions.md'}`.\n"
            f"4. Make ONE of these decisions:\n\n"
            f"   **DECISION A — RETRY WITH STRATEGY**: If you can identify a specific,\n"
            f"   different approach that hasn't been tried. Write a clear strategy the\n"
            f"   executor should follow.\n\n"
            f"   **DECISION B — FORCE ADVANCE**: If the failures are unfixable within\n"
            f"   the current phase scope (e.g., test environment issues, external\n"
            f"   dependencies). Skip remaining test failures and move to next phase.\n\n"
            f"5. Say DONE and clearly state: 'DECISION: A' or 'DECISION: B'\n"
            f"   If DECISION A, also state the specific strategy in one paragraph.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)

        # Parse the LLM's decision
        answer = result.answer if result.answer else ""
        decision_a = "DECISION: A" in answer.upper() or "DECISION A" in answer.upper()

        if decision_a and current_failures < 10:
            # Retry with manager's strategy
            strategy = ""
            # Extract strategy text after "DECISION: A" or "strategy:" keyword
            for marker in ["DECISION: A", "DECISION A", "strategy:"]:
                idx = answer.upper().find(marker.upper())
                if idx >= 0:
                    strategy = answer[idx + len(marker):].strip()[:2000]
                    break
            if not strategy:
                strategy = answer[-1000:]  # fallback: use end of response

            self._log_decision(msg, [], note=(
                f"FIX_ANALYSIS phase={phase_num} retry={retry_count}: "
                f"RETRY with manager strategy — {strategy[:200]}"
            ))

            return [Message.create(
                from_agent=self.role,
                to_agent="executor",
                type="task",
                payload={
                    "phase": phase_num,
                    "tasks_path": tasks_path,
                    "workspace_path": workspace_path,
                    "fix_required": True,
                    "fix_report_path": fix_report_path,
                    "fix_instructions": (
                        f"MANAGER ANALYSIS (retry {retry_count}): {strategy[:3000]}\n\n"
                        f"The previous {retry_count - 1} fix attempts all failed. "
                        f"The manager has analyzed the pattern and recommends the "
                        f"strategy above. Try this SPECIFIC approach — do NOT repeat "
                        f"previous fixes."
                    ),
                    "idea_slug": idea_slug,
                    "retry_count": retry_count,
                },
            )]
        else:
            # Force-advance past this phase
            self._log_decision(msg, [], note=(
                f"FIX_ANALYSIS phase={phase_num} retry={retry_count}: "
                f"FORCE ADVANCE — {current_failures} failures deemed unfixable"
            ))

            if idea_slug:
                from pipeline.force_advance import force_advance_phase

                ok = force_advance_phase(
                    idea_slug,
                    int(phase_num or 0),
                    (
                        f"Manager force-advanced: {current_failures} failures "
                        f"after {retry_count} attempts. {answer[:500]}"
                    ),
                    tasks_path=tasks_path or None,
                    workspace_path=workspace_path or None,
                    retry_count=max(int(retry_count or 0), 3),
                )
                if ok:
                    logger.info(
                        "[manager] Force-advanced '%s' past phase %d after %d retries",
                        idea_slug, phase_num, retry_count,
                    )
                else:
                    logger.error("[manager] Failed to force-advance '%s'", idea_slug)

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

        decisions_path = state_dir() / "manager_decisions.md"
        decisions_path.parent.mkdir(parents=True, exist_ok=True)
        with open(decisions_path, "a", encoding="utf-8") as f:
            f.write(entry)


def main():
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    from pipeline.pipeline_config import DEFAULT_PIPELINE_MODEL
    parser.add_argument("--model", default=DEFAULT_PIPELINE_MODEL)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [manager] %(message)s")

    agent = ManagerAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
