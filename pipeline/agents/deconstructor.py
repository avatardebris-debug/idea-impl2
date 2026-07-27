"""
pipeline/agents/deconstructor.py

LLM deconstructor — target → deconstruct.v0 candidate inventory.

Same pattern as idea_planner / field_test_planner: system prompt + call_llm_direct,
then schema critique and save under PIPELINE_DIR/deconstructs/.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.message_bus import Message


class DeconstructorAgent(AgentProcess):
    role = "deconstructor"
    model_tier = "light"
    num_ctx = 8192
    max_steps = 4
    phase_timeout = 600
    temperature = 0.4
    think = False

    def handle(self, msg: Message) -> AgentOutput:
        from pipeline.deconstructor import run_llm_deconstruct

        target = (
            msg.payload.get("target")
            or msg.payload.get("idea")
            or msg.payload.get("text")
            or ""
        ).strip()
        mode = str(msg.payload.get("mode") or "open").strip().lower()
        max_nodes = int(msg.payload.get("max_nodes") or 20)
        max_depth = int(msg.payload.get("max_depth") or 3)
        deconstruct_id = msg.payload.get("deconstruct_id") or msg.payload.get("id")

        if not target:
            return AgentOutput(
                success=False,
                error="deconstructor requires payload.target (or idea/text)",
            )

        try:
            # AgentProcess.__init__ already applied llm_route (soft ollama → xAI).
            doc = run_llm_deconstruct(
                target,
                mode=mode,
                max_nodes=max_nodes,
                max_depth=max_depth,
                deconstruct_id=str(deconstruct_id) if deconstruct_id else None,
                provider=self.provider,
                model=self.model,
                temperature=self.temperature,
                llm_caller=lambda user, system_addon="": self.call_llm_direct(
                    user, system_prompt_addon=system_addon
                ),
                save=True,
            )
        except Exception as exc:
            self.logger.exception("[deconstructor] failed")
            return AgentOutput(success=False, error=str(exc))

        # run_llm_deconstruct already saved when save=True
        from pipeline.deconstructor import deconstruct_path

        path = deconstruct_path(str(doc.get("id")))
        answer = json.dumps(
            {
                "id": doc.get("id"),
                "status": doc.get("status"),
                "path": str(path),
                "candidate_count": len(doc.get("candidates") or []),
                "critique_ok": (doc.get("critique") or {}).get("ok"),
                "source": doc.get("parse_source"),
            },
            indent=2,
        )
        ok = bool((doc.get("critique") or {}).get("ok")) and not doc.get("needs_structure")
        return AgentOutput(
            success=ok,
            answer=answer,
            files_written=[str(path)],
            error="" if ok else f"critique failed: {(doc.get('critique') or {}).get('issues')}",
        )


def main() -> None:
    """CLI: python -m pipeline.agents.deconstructor"""
    import argparse
    import os

    ap = argparse.ArgumentParser(description="Deconstructor agent (standalone handle)")
    ap.add_argument("--target", required=True)
    ap.add_argument("--mode", default="open")
    ap.add_argument("--provider", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--pipeline-dir", default="")
    args = ap.parse_args()
    if args.pipeline_dir:
        os.environ["PIPELINE_DIR"] = args.pipeline_dir
        try:
            from pipeline.paths import reload_pipeline_dir

            reload_pipeline_dir()
        except Exception:
            pass

    kwargs: dict = {}
    if args.provider:
        kwargs["provider"] = args.provider
    if args.model:
        kwargs["model"] = args.model
    agent = DeconstructorAgent(**kwargs)
    msg = Message.create(
        from_agent="cli",
        to_agent="deconstructor",
        type="task",
        payload={"target": args.target, "mode": args.mode},
    )
    out = agent.handle(msg)
    print(out.answer or out.error)
    raise SystemExit(0 if out.success else 1)


if __name__ == "__main__":
    main()
