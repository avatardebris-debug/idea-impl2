"""CLI walkthrough example.

Demonstrates all CLI commands end-to-end:
    1. Create a checkpoint
    2. Check its status
    3. List all checkpoints
    4. Approve it
    5. Verify the final status

Run this script directly:
    python examples/cli_walkthrough.py
"""

import subprocess
import sys
import time
import threading


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess and return the result."""
    cmd = [sys.executable, "-m", "human_in_the_loop_reviewer"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def main() -> None:
    print("=" * 60)
    print("  Human-in-the-Loop Reviewer — CLI Walkthrough")
    print("=" * 60)
    print()

    # Step 1: Create a checkpoint
    print("Step 1: Creating a checkpoint...")
    result = run_cli("create", "Please review this draft document.")
    print(result.stdout.strip())
    assert result.returncode == 0, f"create failed: {result.stderr}"

    # Extract checkpoint ID from output
    checkpoint_id = result.stdout.strip().split(": ")[1]
    print(f"  → Checkpoint ID: {checkpoint_id}")
    print()

    # Step 2: Check status
    print("Step 2: Checking status...")
    result = run_cli("status", checkpoint_id)
    print(result.stdout.strip())
    assert result.returncode == 0, f"status failed: {result.stderr}"
    print()

    # Step 3: List all checkpoints
    print("Step 3: Listing all checkpoints...")
    result = run_cli("list")
    print(result.stdout.strip())
    assert result.returncode == 0, f"list failed: {result.stderr}"
    print()

    # Step 4: Approve the checkpoint
    print("Step 4: Approving the checkpoint...")
    result = run_cli("approve", checkpoint_id)
    print(result.stdout.strip())
    assert result.returncode == 0, f"approve failed: {result.stderr}"
    print()

    # Step 5: Verify final status
    print("Step 5: Verifying final status...")
    result = run_cli("status", checkpoint_id)
    print(result.stdout.strip())
    assert result.returncode == 0, f"status failed: {result.stderr}"
    assert "approved" in result.stdout.lower(), "Checkpoint should be approved"
    print()

    # Step 6: Demonstrate rejection on a new checkpoint
    print("Step 6: Creating and rejecting a checkpoint...")
    result = run_cli("create", "This draft needs revision.")
    print(result.stdout.strip())
    reject_id = result.stdout.strip().split(": ")[1]

    result = run_cli("reject", reject_id, "--reason", "Content is incomplete.")
    print(result.stdout.strip())
    assert result.returncode == 0, f"reject failed: {result.stderr}"
    print()

    # Step 7: Demonstrate error handling
    print("Step 7: Demonstrating error handling...")
    result = run_cli("status", "nonexistent-id")
    print(f"  (Expected error for nonexistent ID)")
    print(f"  stderr: {result.stderr.strip()}")
    assert result.returncode != 0, "Should have failed for nonexistent ID"
    print()

    print("=" * 60)
    print("  All CLI walkthrough steps completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
