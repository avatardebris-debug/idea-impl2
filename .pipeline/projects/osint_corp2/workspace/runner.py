"""
runner.py — Pipeline orchestration for the OSINT Corp2 system.

Handles seeding ideas from master_ideas.md, dependency resolution,
dispatching to agents, and running the main pipeline loop.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set

# Add workspace to path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from message_bus import MessageBus, Message, MSG_SEED_IDEA, MSG_TASK_COMPLETE, MSG_ERROR


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PIPELINE_DIR = pathlib.Path(__file__).parent.parent
PROJECT_DIR = PIPELINE_DIR / "projects" / "osint_corp2"
STATE_DIR = PROJECT_DIR / "state"
WORKSPACE_DIR = PROJECT_DIR / "workspace"
MASTER_IDEAS_FILE = STATE_DIR / "master_ideas.md"
MASTER_PLAN_FILE = STATE_DIR / "master_plan.md"
CURRENT_IDEA_FILE = STATE_DIR / "current_idea.json"
CURRENT_PHASE_FILE = STATE_DIR / "current_phase.json"
PHASES_DIR = PROJECT_DIR / "phases"


# ---------------------------------------------------------------------------
# Slug utilities
# ---------------------------------------------------------------------------

def slugify(title: str) -> str:
    """Convert a title to kebab-case slug."""
    s = title.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-+', '-', s)
    s = s.strip('-')
    return s or "untitled"


# ---------------------------------------------------------------------------
# Master ideas parsing
# ---------------------------------------------------------------------------

def parse_master_ideas(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parse master_ideas.md and return list of idea dicts."""
    path = pathlib.Path(filepath) if filepath else MASTER_IDEAS_FILE
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    ideas = []
    current_idea = {}

    for line in content.splitlines():
        line = line.strip()

        # New idea header: ## Title or ### Title
        if line.startswith('## ') or line.startswith('### '):
            if current_idea.get('title'):
                ideas.append(current_idea)
            current_idea = {
                'title': line.lstrip('# ').strip(),
                'slug': slugify(line.lstrip('# ').strip()),
                'description': '',
                'requires': [],
                'status': 'pending',
            }
        elif line.lower().startswith('slug:'):
            current_idea['slug'] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('requires:') or line.lower().startswith('depends_on:'):
            deps_str = line.split(':', 1)[1].strip()
            current_idea['requires'] = [d.strip() for d in deps_str.split(',') if d.strip()]
        elif line.lower().startswith('status:'):
            current_idea['status'] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('phase:'):
            current_idea['phase'] = int(line.split(':', 1)[1].strip())
        elif current_idea:
            current_idea['description'] += line + '\n'

    if current_idea.get('title'):
        ideas.append(current_idea)

    return ideas


def save_master_ideas(ideas: List[Dict[str, Any]], filepath: Optional[str] = None) -> str:
    """Save ideas back to master_ideas.md."""
    path = pathlib.Path(filepath) if filepath else MASTER_IDEAS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# Master Ideas List", ""]
    for idea in ideas:
        lines.append(f"## {idea['title']}")
        lines.append(f"Slug: {idea['slug']}")
        lines.append(f"Status: {idea['status']}")
        if idea.get('phase'):
            lines.append(f"Phase: {idea['phase']}")
        if idea.get('requires'):
            lines.append(f"Requires: {', '.join(idea['requires'])}")
        if idea.get('description'):
            lines.append(f"Description: {idea['description'].strip()}")
        lines.append("")

    path.write_text('\n'.join(lines), encoding="utf-8")
    return f"OK: Saved {len(ideas)} ideas to {path}"


# ---------------------------------------------------------------------------
# Dependency checking
# ---------------------------------------------------------------------------

def check_deps_complete(slug: str, deps: List[str], pipeline_dir: Optional[str] = None) -> bool:
    """Check if all dependencies for an idea are complete or budget_exceeded."""
    if not deps:
        return True

    # Use pipeline_dir-relative master_ideas.md when provided (e.g. in tests)
    ideas_path = None
    if pipeline_dir:
        candidate = pathlib.Path(pipeline_dir) / "master_ideas.md"
        if candidate.exists():
            ideas_path = str(candidate)

    ideas = parse_master_ideas(ideas_path)
    idea_map = {i['slug']: i for i in ideas}

    for dep_slug in deps:
        if dep_slug == slug:
            continue  # skip self-reference
        dep_idea = idea_map.get(dep_slug)
        if dep_idea is None:
            # Dependency not in master list — treat as complete (external)
            continue
        if dep_idea['status'] not in ('complete', 'budget_exceeded'):
            return False

    return True


def build_dep_workspace_map(slug: str, deps: List[str], pipeline_dir: Optional[str] = None) -> Dict[str, str]:
    """Map dependency slugs to their workspace paths."""
    if not deps:
        return {}

    base_dir = pathlib.Path(pipeline_dir) / "projects" if pipeline_dir else PROJECT_DIR / "workspace"
    workspace_map = {}
    for dep_slug in deps:
        dep_workspace = base_dir / dep_slug / "workspace"
        if dep_workspace.exists():
            workspace_map[dep_slug] = str(dep_workspace)

    return workspace_map


def is_idea_blocked(slug: str, pipeline_dir: Optional[str] = None) -> bool:
    """Check if an idea is blocked by incomplete dependencies."""
    # Resolve the ideas file from pipeline_dir (for tests) or the default
    ideas_path = None
    if pipeline_dir:
        candidate = pathlib.Path(pipeline_dir) / "master_ideas.md"
        if candidate.exists():
            ideas_path = str(candidate)

    ideas = parse_master_ideas(ideas_path)
    idea_map = {i['slug']: i for i in ideas}
    idea = idea_map.get(slug)
    if not idea:
        return False

    deps = idea.get('requires', [])
    return not check_deps_complete(slug, deps, pipeline_dir)


# ---------------------------------------------------------------------------
# Seeding ideas
# ---------------------------------------------------------------------------

def seed_idea(bus: MessageBus, title: str, description: str,
              idea_slug: str, depends_on: Optional[List[str]] = None,
              dep_workspaces: Optional[Dict[str, str]] = None) -> str:
    """Create and send a seed message for an idea."""
    if depends_on is None:
        depends_on = []
    if dep_workspaces is None:
        dep_workspaces = {}

    message = Message.create(
        from_agent="pipeline",
        to_agent="idea_planner",
        type=MSG_SEED_IDEA,
        payload={
            "title": title,
            "description": description,
            "slug": idea_slug,
            "depends_on": depends_on,
            "dep_workspaces": dep_workspaces,
            "seeded_at": time.time(),
        }
    )
    return bus.send(message)


def seed_from_master_list(bus: MessageBus, pipeline_dir: Optional[str] = None) -> List[str]:
    """Read master_ideas.md, parse ideas, check deps, seed ready ones. Returns list of seeded slugs."""
    ideas = parse_master_ideas()
    seeded = []

    for idea in ideas:
        if idea['status'] != 'pending':
            continue

        slug = idea['slug']
        deps = idea.get('requires', [])

        if is_idea_blocked(slug, pipeline_dir):
            continue

        dep_workspaces = build_dep_workspace_map(slug, deps, pipeline_dir)
        result = seed_idea(
            bus=bus,
            title=idea['title'],
            description=idea.get('description', ''),
            idea_slug=slug,
            depends_on=deps,
            dep_workspaces=dep_workspaces,
        )
        seeded.append(slug)

    return seeded


# ---------------------------------------------------------------------------
# Agent dispatch
# ---------------------------------------------------------------------------

def get_next_agent(slug: str) -> str:
    """Determine which agent should handle a seeded idea."""
    # Default: idea_planner handles all seeded ideas
    return "idea_planner"


def process_queue(bus: MessageBus, pipeline_dir: Optional[str] = None) -> List[str]:
    """Poll the queue and dispatch messages to agents. Returns list of dispatched message types."""
    dispatched = []

    # Check idea_planner queue
    msg = bus.receive("idea_planner")
    if msg:
        agent = get_next_agent(msg.payload.get('slug', ''))
        dispatched.append(f"dispatched {msg.type} to {agent}")

    # Check executor queue
    msg = bus.receive("executor")
    if msg:
        dispatched.append(f"dispatched {msg.type} to executor")

    # Check reviewer queue
    msg = bus.receive("reviewer")
    if msg:
        dispatched.append(f"dispatched {msg.type} to reviewer")

    return dispatched


# ---------------------------------------------------------------------------
# Pipeline state management
# ---------------------------------------------------------------------------

def update_current_idea(idea_slug: str, status: str, extra: Optional[Dict] = None) -> str:
    """Update current_idea.json with the latest idea state."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "slug": idea_slug,
        "status": status,
        "updated_at": time.time(),
    }
    if extra:
        data.update(extra)
    CURRENT_IDEA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return f"OK: Updated current_idea.json ({idea_slug}: {status})"


def update_current_phase(phase_num: int, status: str, notes: str = "") -> str:
    """Update current_phase.json."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "phase_num": phase_num,
        "status": status,
        "updated_at": time.time(),
        "notes": notes,
    }
    CURRENT_PHASE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return f"OK: Updated current_phase.json (phase {phase_num}: {status})"


def get_current_phase() -> Dict[str, Any]:
    """Get the current phase state."""
    if CURRENT_PHASE_FILE.exists():
        return json.loads(CURRENT_PHASE_FILE.read_text(encoding="utf-8"))
    return {"phase_num": 0, "status": "not_started"}


# ---------------------------------------------------------------------------
# Main pipeline loop
# ---------------------------------------------------------------------------

def run_pipeline(max_iterations: int = 100, verbose: bool = True) -> str:
    """Run the main pipeline loop. Returns summary string."""
    bus = MessageBus()

    # Register agents
    for agent in ["idea_planner", "executor", "reviewer", "orchestrator"]:
        bus.register_agent(agent)

    iteration = 0
    seeded_count = 0
    completed_count = 0
    error_count = 0

    while iteration < max_iterations:
        iteration += 1

        # Phase 1: Seed ideas from master list
        if iteration <= 10:  # Seed phase
            seeded = seed_from_master_list(bus)
            if seeded:
                seeded_count += len(seeded)
                if verbose:
                    print(f"[seed] Seeded {len(seeded)} ideas: {', '.join(seeded)}")

        # Phase 2: Process queue
        dispatched = process_queue(bus)
        if dispatched:
            if verbose:
                for d in dispatched:
                    print(f"[dispatch] {d}")

        # Phase 3: Check for completion signals
        msg = bus.receive("orchestrator")
        if msg and msg.type == MSG_TASK_COMPLETE:
            completed_count += 1
            if verbose:
                print(f"[complete] Task complete: {msg.payload.get('slug', 'unknown')}")

        # Phase 4: Check for errors
        msg = bus.receive("orchestrator")
        if msg and msg.type == MSG_ERROR:
            error_count += 1
            if verbose:
                print(f"[error] {msg.payload.get('message', 'Unknown error')}")

        # Check if all ideas are done
        ideas = parse_master_ideas()
        pending = [i for i in ideas if i['status'] == 'pending']
        if not pending and seeded_count > 0:
            if verbose:
                print(f"[pipeline] All ideas processed. Seeded: {seeded_count}, Completed: {completed_count}, Errors: {error_count}")
            break

        # Small delay to prevent tight loop
        time.sleep(0.01)

    summary = (
        f"Pipeline run complete. "
        f"Iterations: {iteration}, "
        f"Seeded: {seeded_count}, "
        f"Completed: {completed_count}, "
        f"Errors: {error_count}"
    )
    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """CLI entry point for the pipeline runner."""
    import argparse

    parser = argparse.ArgumentParser(description="OSINT Corp2 Pipeline Runner")
    parser.add_argument("--seed", action="store_true", help="Seed ideas from master_ideas.md")
    parser.add_argument("--run", action="store_true", help="Run the full pipeline loop")
    parser.add_argument("--list", action="store_true", help="List all ideas")
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--max-iterations", type=int, default=100, help="Max pipeline iterations")

    args = parser.parse_args()

    if args.list:
        ideas = parse_master_ideas()
        for idea in ideas:
            print(f"  [{idea['status']:15}] {idea['title']} (slug: {idea['slug']})")
        print(f"\nTotal: {len(ideas)} ideas")

    elif args.status:
        phase = get_current_phase()
        print(f"Current phase: {phase.get('phase_num', 'N/A')} ({phase.get('status', 'N/A')})")
        ideas = parse_master_ideas()
        pending = sum(1 for i in ideas if i['status'] == 'pending')
        complete = sum(1 for i in ideas if i['status'] == 'complete')
        print(f"Ideas: {pending} pending, {complete} complete")

    elif args.seed:
        bus = MessageBus()
        for agent in ["idea_planner", "executor", "reviewer", "orchestrator"]:
            bus.register_agent(agent)
        seeded = seed_from_master_list(bus)
        print(f"Seeded {len(seeded)} ideas: {', '.join(seeded)}")

    elif args.run:
        summary = run_pipeline(max_iterations=args.max_iterations, verbose=args.verbose)
        print(summary)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
