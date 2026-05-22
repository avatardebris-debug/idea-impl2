"""CLI entry point for human_in_the_loop_reviewer.

Provides commands: create, approve, reject, status, list, wait.

Each invocation is stateless — checkpoints are stored in a JSON file
(default: ~/.human_in_the_loop_reviewer.json) so that multiple CLI
invocations can share state.

Usage:
    python -m human_in_the_loop_reviewer create "Review this draft"
    python -m human_in_the_loop_reviewer status <checkpoint_id>
    python -m human_in_the_loop_reviewer approve <checkpoint_id>
    python -m human_in_the_loop_reviewer reject <checkpoint_id> --reason "..."
    python -m human_in_the_loop_reviewer list
    python -m human_in_the_loop_reviewer wait <checkpoint_id>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from human_in_the_loop_reviewer import Checkpoint, CheckpointStore, HumanInLoopReviewer


def _get_state_file() -> Path:
    """Return the path to the persistent state file."""
    default = Path.home() / ".human_in_the_loop_reviewer.json"
    return Path(os.environ.get("HUMAN_IN_THE_LOOP_STATE", str(default)))


def _load_store(state_file: Path) -> CheckpointStore:
    """Load or create a CheckpointStore from the state file."""
    store = CheckpointStore()
    if state_file.exists():
        data = json.loads(state_file.read_text())
        for cp_data in data.get("checkpoints", []):
            cp = Checkpoint(
                id=cp_data["id"],
                review_request=cp_data["review_request"],
                status=cp_data["status"],
                created_at=datetime.fromisoformat(cp_data["created_at"]),
                metadata=cp_data.get("metadata"),
            )
            store.create(cp)
    return store


def _save_store(store: CheckpointStore, state_file: Path) -> None:
    """Save the CheckpointStore to the state file."""
    checkpoints = store.list_all()
    data = {
        "checkpoints": [
            {
                "id": cp.id,
                "review_request": cp.review_request,
                "status": cp.status,
                "created_at": cp.created_at.isoformat(),
                "metadata": cp.metadata,
            }
            for cp in checkpoints
        ]
    }
    # Write to temp file first, then rename for atomicity
    fd, tmp_path = tempfile.mkstemp(dir=state_file.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        Path(tmp_path).replace(state_file)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def _get_reviewer(state_file: Path) -> tuple[HumanInLoopReviewer, CheckpointStore]:
    """Create a reviewer backed by the persistent state file."""
    store = _load_store(state_file)
    reviewer = HumanInLoopReviewer(store=store)
    return reviewer, store


# ------------------------------------------------------------------
# Command implementations
# ------------------------------------------------------------------

def cmd_create(args: argparse.Namespace, state_file: Path) -> None:
    """Create a new checkpoint."""
    reviewer, store = _get_reviewer(state_file)
    cp_id = reviewer.create_checkpoint(
        review_request=args.review_request,
        metadata=json.loads(args.metadata) if args.metadata else None,
    )
    _save_store(store, state_file)
    print(f"Checkpoint created: {cp_id}")


def cmd_approve(args: argparse.Namespace, state_file: Path) -> None:
    """Approve a checkpoint."""
    reviewer, store = _get_reviewer(state_file)
    result = reviewer.approve(args.checkpoint_id)
    if result:
        _save_store(store, state_file)
        cp = reviewer.get_checkpoint(args.checkpoint_id)
        print(f"Checkpoint {args.checkpoint_id} approved.")
        print(_format_checkpoint(cp))
    else:
        print(f"Error: Checkpoint {args.checkpoint_id} not found.", file=sys.stderr)
        sys.exit(1)


def cmd_reject(args: argparse.Namespace, state_file: Path) -> None:
    """Reject a checkpoint."""
    reviewer, store = _get_reviewer(state_file)
    result = reviewer.reject(args.checkpoint_id, reason=args.reason or "")
    if result:
        _save_store(store, state_file)
        cp = reviewer.get_checkpoint(args.checkpoint_id)
        print(f"Checkpoint {args.checkpoint_id} rejected.")
        if args.reason:
            print(f"  Reason: {args.reason}")
        print(_format_checkpoint(cp))
    else:
        print(f"Error: Checkpoint {args.checkpoint_id} not found.", file=sys.stderr)
        sys.exit(1)


def cmd_status(args: argparse.Namespace, state_file: Path) -> None:
    """Show status of a checkpoint."""
    reviewer, _ = _get_reviewer(state_file)
    cp = reviewer.get_checkpoint(args.checkpoint_id)
    if cp is None:
        print(f"Error: Checkpoint {args.checkpoint_id} not found.", file=sys.stderr)
        sys.exit(1)
    print(_format_checkpoint(cp))


def cmd_list(args: argparse.Namespace, state_file: Path) -> None:
    """List all checkpoints."""
    reviewer, _ = _get_reviewer(state_file)
    checkpoints = reviewer.list_checkpoints()
    if not checkpoints:
        print("No checkpoints found.")
        return
    for cp in checkpoints:
        print(_format_checkpoint(cp))
        print()


def cmd_wait(args: argparse.Namespace, state_file: Path) -> None:
    """Wait for a checkpoint to be resolved (approved or rejected)."""
    checkpoint_id = args.checkpoint_id
    timeout = args.timeout
    start_time = time.monotonic()

    while True:
        reviewer, store = _get_reviewer(state_file)
        cp = store.get(checkpoint_id)
        if cp is None:
            print(f"Error: Checkpoint '{checkpoint_id}' not found.", file=sys.stderr)
            sys.exit(1)

        if cp.status in ("approved", "rejected"):
            print(f"Checkpoint {cp.id} is {cp.status}.")
            print(_format_checkpoint(cp))
            sys.exit(0)

        elapsed = time.monotonic() - start_time
        if elapsed >= timeout:
            print(f"Timeout waiting for checkpoint {checkpoint_id}.", file=sys.stderr)
            sys.exit(1)

        remaining = timeout - elapsed
        time.sleep(min(0.5, remaining))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _format_checkpoint(cp: Checkpoint) -> str:
    """Format a Checkpoint for display."""
    lines = [
        f"  ID:             {cp.id}",
        f"  Review Request: {cp.review_request}",
        f"  Status:         {cp.status}",
        f"  Created At:     {cp.created_at.isoformat()}",
    ]
    if cp.metadata:
        lines.append(f"  Metadata:       {json.dumps(cp.metadata, indent=4)}")
    return "\n".join(lines)


# ------------------------------------------------------------------
# Argument parsing
# ------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="human_in_the_loop_reviewer",
        description="Human-in-the-loop checkpoint reviewer CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create
    p_create = subparsers.add_parser("create", help="Create a new checkpoint")
    p_create.add_argument("review_request", help="The review request text")
    p_create.add_argument("--metadata", "-m", default=None, help="JSON metadata string")

    # approve
    p_approve = subparsers.add_parser("approve", help="Approve a checkpoint")
    p_approve.add_argument("checkpoint_id", help="Checkpoint ID to approve")

    # reject
    p_reject = subparsers.add_parser("reject", help="Reject a checkpoint")
    p_reject.add_argument("checkpoint_id", help="Checkpoint ID to reject")
    p_reject.add_argument("--reason", "-r", default="", help="Reason for rejection")

    # status
    p_status = subparsers.add_parser("status", help="Show checkpoint status")
    p_status.add_argument("checkpoint_id", help="Checkpoint ID to query")

    # list
    subparsers.add_parser("list", help="List all checkpoints")

    # wait
    p_wait = subparsers.add_parser("wait", help="Wait for checkpoint resolution")
    p_wait.add_argument("checkpoint_id", help="Checkpoint ID to wait on")
    p_wait.add_argument("--timeout", "-t", type=float, default=30.0, help="Timeout in seconds")

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    """Main entry point for the CLI."""
    state_file = _get_state_file()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        "create": cmd_create,
        "approve": cmd_approve,
        "reject": cmd_reject,
        "status": cmd_status,
        "list": cmd_list,
        "wait": cmd_wait,
    }

    cmd_func = commands.get(args.command)
    if cmd_func is None:
        parser.print_help()
        sys.exit(1)

    cmd_func(args, state_file)


if __name__ == "__main__":
    main()
