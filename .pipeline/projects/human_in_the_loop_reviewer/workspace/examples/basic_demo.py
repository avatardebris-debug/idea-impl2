"""Basic demo: create a checkpoint, approve it, and show the result."""

import threading
import time

from human_in_the_loop_reviewer import Checkpoint, HumanInLoopReviewer


def main() -> None:
    reviewer = HumanInLoopReviewer()

    # 1. Create a checkpoint
    cp_id = reviewer.create_checkpoint(
        review_request="Please review this draft proposal.",
        metadata={"author": "agent-42", "priority": "high"},
    )
    print(f"[1] Checkpoint created with id: {cp_id}")

    # 2. Simulate a human approving it in a separate thread
    def human_action() -> None:
        time.sleep(1)  # pretend the human takes a moment
        reviewer.approve(cp_id)
        print("[2] Human approved the checkpoint.")

    t = threading.Thread(target=human_action, daemon=True)
    t.start()

    # 3. Wait for the response (blocks until approve/reject)
    print("[3] Waiting for human response...")
    result = reviewer.wait_for_response(cp_id)
    print(f"[4] Checkpoint status: {result.status}")
    print(f"    Review request: {result.review_request}")
    print(f"    Metadata: {result.metadata}")

    # 4. Verify
    assert result.status == "approved", f"Expected 'approved', got '{result.status}'"
    print("\n✅ Demo completed successfully — checkpoint was created, approved, and retrieved.")


if __name__ == "__main__":
    main()
