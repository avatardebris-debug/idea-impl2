"""
pipeline/seeding.py
Seed ideas from master list, ideation, dep-aware queue purge.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pipeline.message_bus import Message, MessageBus
from pipeline.dep_policy import (
    dep_blocking_reason,
    parse_requires_from_description,
    split_requires_from_description,
)
from pipeline.paths import project_dir, project_state_file, projects_dir as pipeline_projects_dir
from pipeline.pipeline_config import AGENT_ROLES, PROJECT_ROOT, get_pipeline_dir
from pipeline.project_ops import _rebuild_single_project
from pipeline.slug_util import slugify_title as _slugify

if TYPE_CHECKING:
    from pipeline.run_context import RunContext

# Return values for seed_from_master_list
SEED_SEEDED = "seeded"
SEED_BLOCKED = "blocked"
SEED_EMPTY = "empty"
SEED_GOAL_QUEUED = "goal_queued"

# Back-compat aliases for runner imports
_SEED_SEEDED = SEED_SEEDED
_SEED_BLOCKED = SEED_BLOCKED
_SEED_EMPTY = SEED_EMPTY
_SEED_GOAL_QUEUED = SEED_GOAL_QUEUED

_seeded_this_session: set[str] = set()

def _purge_dep_blocked_messages(bus: "MessageBus") -> int:
    """After reset_stale_processing(), drop pending messages for projects
    whose dependencies are not yet satisfied.

    Without this, a project that was already started (pending message in
    queue, dep still running) bypasses every dep check and gets picked up
    by agents immediately after restart.

    Returns the number of messages purged.
    """
    projects_dir = pipeline_projects_dir()
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
                    blocking.append(dep_blocking_reason(dep_slug, None, context="purge"))
                    continue
                try:
                    dep_st = json.loads(dep_file.read_text(encoding="utf-8"))
                    reason = dep_blocking_reason(
                        dep_slug, dep_st.get("status"), context="purge",
                    )
                    if reason:
                        blocking.append(reason)
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


def seed_idea(bus: MessageBus, title: str, description: str,
              deps: list | None = None, locked: bool = False,
              priority_tier: int = 0) -> None:
    """Send the initial idea to the Idea Planner to kick off the pipeline."""
    if title in _seeded_this_session:
        return  # already seeded this run — don't duplicate
    _seeded_this_session.add(title)

    idea_slug = _slugify(title)

    # Resolve dependency workspace paths so idea_planner can read existing interfaces
    dep_workspaces: dict = {}
    if deps:
        for dep_slug in deps:
            ws = project_dir(dep_slug) / "workspace"
            if ws.exists():
                dep_workspaces[dep_slug] = str(ws)

    # Write a stub current_idea.json NOW so deps survive runner restarts.
    # idea_planner will overwrite this with full state once it processes the idea.
    stub_state_file = project_state_file(idea_slug)
    if not stub_state_file.exists():
        stub_state_file.parent.mkdir(parents=True, exist_ok=True)
        stub_state_file.write_text(json.dumps({
            "title": title,
            "slug": idea_slug,
            "status": "phase_1_planning",
            "depends_on": deps or [],
            "budget_lock": locked,
            "priority_tier": priority_tier,
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
            "priority_tier": priority_tier,
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
    pipeline_dir = get_pipeline_dir()
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
        "Groups 1–4 (pipeline harness): add `kind:harness` in the description when possible.\n"
        "Group 5 (agentic & bridge): REQUIRED `kind:connector requires: slug_a, slug_b` with exact slugs.\n"
        "Group 6 (experiments): add `kind:experiment` when applicable.\n"
        "Use exact project slugs from Existing Projects. Keep titles concise (3-7 words)."
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
_SEED_SEEDED      = "seeded"       # started a new project
_SEED_BLOCKED     = "blocked"      # ideas exist but all deps pending — wait, don't ideate
_SEED_EMPTY       = "empty"        # list truly exhausted — safe to trigger ideation
_SEED_GOAL_QUEUED = "goal_queued"  # --goal decomposed and children injected


def seed_from_master_list(
    bus: MessageBus,
    silent: bool = False,
    ideas_path: pathlib.Path | None = None,
    resume_inprogress: bool = False,
    run_ctx: "RunContext | None" = None,
) -> str:
    """Find the first unchecked, unblocked idea in master_ideas.md and seed it.

    Dependency syntax (append to description):
        requires: slug_one, slug_two

    Example master_ideas.md line:
        - [ ] **[Movie idea generator]** — [generate movie ideas. requires: ai_movie_generation_suite]

    Blocked ideas (deps not yet complete) are skipped with a status message.
    They unblock automatically once their dependencies reach 'complete'.
    """
    if run_ctx and run_ctx.mode == "polish":
        # Polish runs only use polish_queue.md via run_polish_mode / queue_pending.
        return SEED_EMPTY

    if not ideas_path or ideas_path.name == "master_ideas.md":
        try:
            from pipeline.capability_gaps import seed_next_capability_gap

            gap_result = seed_next_capability_gap(bus)
            if gap_result in (SEED_SEEDED, SEED_BLOCKED):
                return gap_result
        except Exception:
            pass

    mi_path = ideas_path if ideas_path else PROJECT_ROOT.resolve() / "master_ideas.md"
    if not mi_path.exists():
        print(f"  ✗ {mi_path.name} not found")
        return SEED_EMPTY
    # Trim completed ideas from master list only (not polish queue)
    _is_polish_list = run_ctx.is_polish_queue(mi_path) if run_ctx else False
    if not _is_polish_list:
        try:
            from pipeline.ideas_sync import prepare_master_ideas_for_seed
            n_trim = prepare_master_ideas_for_seed(mi_path, verbose=not silent)
            if n_trim and not silent:
                print(f"  [truth] {n_trim} completed idea(s) removed from queue before seed")
        except Exception:
            pass

    import re
    content = mi_path.read_text(encoding="utf-8")
    blocked_count = 0

    _LINE_PATTERNS = (
        re.compile(r"- \[ \]\s+\*\*(.+?)\*\*\s*[—–-]\s*(.*)"),
        re.compile(r"-?\s*\[ \]\s+\[(.+?)\]\s*[—–-]\s*(.*)"),
        # kind:connector metadata before em dash
        re.compile(
            r"- \[ \]\s+\*\*(.+?)\*\*\s+"
            r"(?:kind:\s*connector\b(?:\s+requires:\s*[\w,\s_-]+)?(?:\s+connector:\s*[\w_-]+)?)\s*"
            r"[—–-]\s*(.*)",
            re.IGNORECASE,
        ),
    )

    for line in content.split("\n"):
        match = None
        for pat in _LINE_PATTERNS:
            match = pat.match(line)
            if match:
                break
        if not match:
            continue

        title = match.group(1).strip()
        if title in _seeded_this_session:
            continue

        slug = _slugify(title)
        project_state = project_state_file(slug)

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
                    in_progress_deps = parse_requires_from_description(raw_desc)

                if in_progress_deps:
                    _blocking = []
                    for _dep in in_progress_deps:
                        _df = project_state_file(_dep)
                        if not _df.exists():
                            _blocking.append(dep_blocking_reason(_dep, None, context="seeding"))
                            continue
                        try:
                            _ds = json.loads(_df.read_text(encoding="utf-8"))
                            reason = dep_blocking_reason(
                                _dep, _ds.get("status"), context="seeding",
                            )
                            if reason:
                                _blocking.append(reason)
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

        # --- Detect --goal tag: decompose into subgoals instead of seeding ---
        if re.search(r'\s--goal\s*$', line, re.IGNORECASE):
            # Strip the --goal tag from description before passing to decomposer
            goal_description = re.sub(r'\s--goal\s*$', '', description_raw, flags=re.IGNORECASE).strip()
            try:
                from pipeline.goal_decomposer import process_goal_line
                injected = process_goal_line(
                    goal_title=title,
                    goal_description=goal_description,
                    mi_path=mi_path,
                )
                if injected:
                    _seeded_this_session.add(title)
                    return _SEED_SEEDED  # children are now in list; runner will pick them up next tick
                else:
                    # Decomposer returned nothing — mark as skipped to avoid infinite retry
                    print(f"  ⚠  --goal '{title}' decomposed 0 branches; skipping")
                    _seeded_this_session.add(title)
                    continue
            except Exception as _ge:
                print(f"  ✗ --goal decomposer failed for '{title}': {_ge}")
                _seeded_this_session.add(title)
                continue

        # --- Detect --hermes tag: run via Hermes Worker+Critic instead of pipeline ---
        if re.search(r'\s--hermes\s*$', line, re.IGNORECASE):
            hermes_description = re.sub(r'\s--hermes\s*$', '', description_raw, flags=re.IGNORECASE).strip()
            # Parse optional hermes_goal_check from description: [goal_check: ...]
            _hgc_match = re.search(r'goal_check:\s*([^\.\]]+)', hermes_description, re.IGNORECASE)
            hermes_goal_check = _hgc_match.group(1).strip() if _hgc_match else f"Has the task '{title}' been completed?"
            print(f"\n  🤖 Routing to Hermes: {title}")
            _seeded_this_session.add(title)
            try:
                from pipeline.hermes_runner import HermesGoalRunner
                _hr = HermesGoalRunner()
                _hr_result = _hr.run(
                    prompt=hermes_description,
                    goal_check=hermes_goal_check,
                    time_budget_min=60,
                    branch_id=_slugify(title),
                )
                print(f"  🤖 Hermes '{title}': {_hr_result['status']} ({_hr_result['attempts']} attempts)")
                try:
                    from pipeline.pipeline_mode import legacy_mode
                    if not legacy_mode():
                        from pipeline.capability_registry import register_hermes_capability

                        register_hermes_capability(
                            title,
                            purpose=hermes_description,
                            goal_check=hermes_goal_check,
                            achieved=_hr_result.get("status") == "achieved",
                            output_excerpt=(_hr_result.get("output") or "")[:500],
                        )
                except Exception:
                    pass
                # Mark the line as done in master_ideas.md
                try:
                    _mi_content = mi_path.read_text(encoding="utf-8")
                    _mi_content = _mi_content.replace(
                        f"- [ ] **[{title}]",
                        f"- [x] **[{title}]",
                        1,
                    )
                    mi_path.write_text(_mi_content, encoding="utf-8")
                except Exception:
                    pass
            except Exception as _he:
                print(f"  ✗ Hermes runner failed for '{title}': {_he}")
            return _SEED_SEEDED

        # --- kind:connector → run workflow YAML, not a 7-phase project ---
        if re.search(r"\bkind:\s*connector\b", line, re.IGNORECASE):
            _conn_m = re.search(r"\bconnector:\s*([\w_-]+)", line, re.IGNORECASE)
            wf_slug = _conn_m.group(1).strip() if _conn_m else slug
            print(f"\n  🔗 Connector '{title}' → workflow `{wf_slug}` (skipping project seed)")
            _seeded_this_session.add(title)
            try:
                from pipeline.workflow_runner import run_workflow

                _wfr = run_workflow(wf_slug, force=True)
                _ok = _wfr.startswith("OK")
                print(f"  {'✓' if _ok else '⚠'} {_wfr[:300]}")
                if _ok:
                    try:
                        _mi_content = mi_path.read_text(encoding="utf-8")
                        _mi_content = _mi_content.replace(
                            f"- [ ] **[{title}]",
                            f"- [x] **[{title}]",
                            1,
                        )
                        mi_path.write_text(_mi_content, encoding="utf-8")
                    except Exception:
                        pass
            except Exception as _ce:
                print(f"  ✗ Connector workflow failed for '{title}': {_ce}")
            continue

        # --- Parse 'priority: N' or 'priority_tier: N' ---
        priority_match = re.search(r'\b(?:priority|priority_tier):\s*(\d+)', description_raw, re.IGNORECASE)
        priority_tier = 0
        if priority_match:
            priority_tier = int(priority_match.group(1))
            description_raw = re.sub(r'\s*[,;.-]?\s*\b(?:priority|priority_tier):\s*\d+\s*', '', description_raw, flags=re.IGNORECASE).strip()

        # --- Parse '[lock]' tag — prevents budget_exceeded from ever firing ---
        locked = bool(re.search(r'\[lock\]', description_raw, re.IGNORECASE))

        # --- Parse 'requires: slug1, slug2' dependency declarations ---
        description = re.sub(r'\s*\[lock\]', '', description_raw, flags=re.IGNORECASE).strip()
        description, deps = split_requires_from_description(description)
        description = re.sub(r'\s*\[lock\]', '', description, flags=re.IGNORECASE).strip()

        # --- Check all dependencies are complete before seeding ---
        if deps:
            blocking: list = []
            for dep_slug in deps:
                dep_state_file = project_state_file(dep_slug)
                if not dep_state_file.exists():
                    blocking.append(dep_blocking_reason(dep_slug, None, context="seeding"))
                    continue
                try:
                    dep_state = json.loads(dep_state_file.read_text(encoding="utf-8"))
                    reason = dep_blocking_reason(
                        dep_slug, dep_state.get("status"), context="seeding",
                    )
                    if reason:
                        blocking.append(reason)
                except Exception:
                    blocking.append(f"{dep_slug} (unreadable)")
            if blocking:
                blocked_count += 1
                print(f"  [blocked]  '{title}' blocked - waiting for: {', '.join(blocking)}")
                continue  # try the next idea in the list

        seed_idea(bus, title, description, deps=deps or None, locked=locked, priority_tier=priority_tier)
        return _SEED_SEEDED

    if blocked_count > 0:
        print(f"  [BLOCKED] {blocked_count} idea(s) blocked on dependencies -- will retry next tick")
        return _SEED_BLOCKED  # don't trigger ideation — deps will resolve
    elif not silent:
        if _is_polish_list:
            print("  [polish] No more unchecked entries in polish queue (or all skipped)")
        else:
            print("  ✗ No unchecked ideas found in master_ideas.md")
    return _SEED_EMPTY


def check_resume(bus: MessageBus) -> bool:
    """Check if there's an active pipeline state to resume."""
    from pipeline.pipeline_status import load_pipeline_status

    status = load_pipeline_status()
    if status.get("status") == "running":
        print(f"  🔄 Resuming pipeline (idea: {status.get('current_idea', '?')})")
        return True

    for role in AGENT_ROLES:
        if bus.queue_depth(role) > 0:
            print(f"  🔄 Found pending messages in {role} queue — resuming")
            return True

    return False
