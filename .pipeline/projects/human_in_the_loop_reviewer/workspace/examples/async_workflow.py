"""Async workflow example.

Demonstrates how to integrate the Human-in-the-Loop Reviewer into a
multi-step agent pipeline with approval gates.

This example shows:
    1. An agent generates a draft
    2. A checkpoint is created for human review
    3. The agent waits for approval
    4. Upon approval, the agent proceeds to the next step

Run this script directly:
    python examples/async_workflow.py
"""

import asyncio
import threading
import time
from typing import Optional

from human_in_the_loop_reviewer import Checkpoint, HumanInLoopReviewer


class AgentPipeline:
    """Simulated agent pipeline with approval gates."""

    def __init__(self) -> None:
        self.reviewer = HumanInLoopReviewer()
        self._results: dict[str, str] = {}

    async def run_pipeline(self) -> dict[str, str]:
        """Run the full pipeline with approval gates."""
        print("=" * 60)
        print("  Async Agent Pipeline with Approval Gates")
        print("=" * 60)
        print()

        # Step 1: Generate draft
        draft = await self._generate_draft()
        print(f"[Agent] Draft generated: '{draft}'")
        print()

        # Step 2: Create checkpoint for review
        cp_id = self.reviewer.create_checkpoint(
            review_request="Review the generated draft document.",
            metadata={"step": "draft_review", "agent": "content-gen-v2"},
        )
        print(f"[System] Checkpoint created: {cp_id}")
        print("[System] Waiting for human approval...")
        print()

        # Step 3: Wait for human response (in a separate thread)
        approval_result = await self._wait_for_approval(cp_id)

        if approval_result.status == "approved":
            print(f"[System] ✅ Checkpoint approved! Proceeding...")
            # Step 4: Approve checkpoint (simulated human action)
            self._simulate_human_approval(cp_id)

            # Step 5: Proceed to next step
            final_output = await self._publish_content(draft)
            print(f"[Agent] Final output: '{final_output}'")
        else:
            print(f"[System] ❌ Checkpoint rejected. Pipeline halted.")
            print(f"    Reason: {approval_result.metadata.get('rejection_reason', 'N/A')}")

        print()
        print("=" * 60)
        print("  Pipeline completed!")
        print("=" * 60)
        return self._results

    async def _generate_draft(self) -> str:
        """Simulate draft generation."""
        await asyncio.sleep(0.1)
        return "This is a draft proposal for the new feature."

    async def _wait_for_approval(self, cp_id: str) -> Checkpoint:
        """Wait for approval in a background thread."""
        loop = asyncio.get_event_loop()

        def _wait():
            return self.reviewer.wait_for_response(cp_id, timeout=10.0)

        result = await loop.run_in_executor(None, _wait)
        return result

    def _simulate_human_approval(self, cp_id: str) -> None:
        """Simulate a human approving the checkpoint."""
        time.sleep(0.5)
        self.reviewer.approve(cp_id)

    async def _publish_content(self, draft: str) -> str:
        """Simulate publishing the approved content."""
        await asyncio.sleep(0.1)
        self._results["final_output"] = f"PUBLISHED: {draft}"
        return f"PUBLISHED: {draft}"


async def main() -> None:
    pipeline = AgentPipeline()
    await pipeline.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
