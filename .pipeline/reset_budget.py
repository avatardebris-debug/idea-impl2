#!/usr/bin/env python3
"""
reset_budget.py

Utility script to reset the budget timer for a stalled or budget_exceeded project.
Usage:
    python .pipeline/reset_budget.py pantrychef_meal_planner
"""
import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

def main():
    parser = argparse.ArgumentParser(description="Reset budget timer for a stalled pipeline project.")
    parser.add_argument("project_slug", help="The folder name of the project (e.g. pantrychef_meal_planner)")
    args = parser.parse_args()

    project_dir = pathlib.Path(".pipeline/projects") / args.project_slug
    state_file = project_dir / "state" / "current_idea.json"

    if not state_file.exists():
        print(f"Error: Could not find state file at {state_file}")
        sys.exit(1)

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading state JSON: {e}")
        sys.exit(1)

    old_status = state.get("status", "unknown")
    
    # If it was marked budget_exceeded, bump it back to reviewing the current phase
    # so the runner can advance it properly
    if old_status == "budget_exceeded":
        current_phase = state.get("phase", 1)
        state["status"] = f"phase_{current_phase}_reviewed"
        print(f"-> Changed status from 'budget_exceeded' to '{state['status']}'")

    now = datetime.now(timezone.utc).isoformat()
    state["session_started_at"] = now
    state["started_at"] = now
    
    # Remove any runner-injected budget notes
    state.pop("budget_note", None)

    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    
    print(f"✅ Successfully reset budget timer for '{args.project_slug}'.")
    print(f"   The runner will automatically pick it back up on its next loop.")

if __name__ == "__main__":
    main()
