#!/usr/bin/env python3
"""
pipeline/finetune/race.py
Discriminator/Generator Racing System — Fine-tune vs Base Model Head-to-Head

For each completed phase, submits the same executor prompt to TWO providers:
  - Challenger A: base model (e.g. Grok Build, the reference)
  - Challenger B: local fine-tuned model (or any Ollama model)

The CodeJudge scores both outputs. The winner becomes "chosen", the loser
"rejected". All non-tie results are appended to the DPO training pool.

This closes the self-improvement flywheel:
  pipeline runs → completions → harvest → race → DPO pairs → QLoRA fine-tune
                                                             → better executor
                                                             → fewer retries ↻

Modes:
  --live     Run both models on a LIVE phase (picks the next unraced phase)
  --replay   Race on already-completed phases using workspace as "model B" output
             and a separately provided model-A output (for offline racing)

Usage:
    python pipeline/finetune/race.py --replay --provider-a grok --model-a grok-3-fast
    python pipeline/finetune/race.py --live   --provider-a grok --model-a grok-3-fast \\
                                              --provider-b ollama --model-b qwen3.6:35b-a3b-q4_K_M
    python pipeline/finetune/race.py --stats
"""

from __future__ import annotations

from pipeline.pipeline_config import DEFAULT_PIPELINE_MODEL
import argparse
import json
import logging
import pathlib
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT         = pathlib.Path(__file__).parent.parent.parent.resolve()


def _race_log() -> pathlib.Path:
    return _memory_dir() / "race_log.jsonl"


def _dpo_race() -> pathlib.Path:
    return _memory_dir() / "dpo_race.jsonl"


_pipeline_override: pathlib.Path | None = None


def _pipeline_dir() -> pathlib.Path:
    if _pipeline_override is not None:
        return _pipeline_override
    from pipeline.pipeline_config import get_pipeline_dir

    return get_pipeline_dir()


def _projects_dir() -> pathlib.Path:
    if _pipeline_override is not None:
        return _pipeline_override / "projects"
    from pipeline.paths import projects_dir

    return projects_dir()


def _memory_dir() -> pathlib.Path:
    if _pipeline_override is not None:
        return _pipeline_override / "memory"
    from pipeline.paths import memory_dir

    return memory_dir()

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@dataclass
class RaceResult:
    """One head-to-head race result."""
    slug:         str
    phase:        int
    raced_at:     str          # ISO timestamp
    provider_a:   str
    model_a:      str
    provider_b:   str
    model_b:      str
    score_a:      float
    score_b:      float
    winner:       str          # "a", "b", or "tie"
    winner_label: str          # human-readable (model name of winner)
    margin:       float
    is_tie:       bool
    prompt_chars: int
    # DPO content (not stored in log — written to dpo_race.jsonl separately)
    chosen_text:  str = field(default="", repr=False)
    rejected_text: str = field(default="", repr=False)

    def to_log_dict(self) -> dict:
        """Dict for race_log.jsonl — excludes bulky text fields."""
        d = asdict(self)
        d.pop("chosen_text", None)
        d.pop("rejected_text", None)
        return d


@dataclass
class DPORacePair:
    """DPO pair produced by a race — compatible with trl DPOTrainer."""
    prompt:   str
    chosen:   str
    rejected: str
    _meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_llm(provider: str, model: str):
    """Return an LLMBase adapter. Delegates to project's llm_interface."""
    sys.path.insert(0, str(ROOT))
    from llm_interface import get_llm  # type: ignore[import]
    return get_llm(provider, model=model, temperature=0.2)


def _append_jsonl(path: pathlib.Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_safe(path: pathlib.Path, max_chars: int = 0) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars] if max_chars else text
    except OSError:
        return ""


def _build_executor_prompt(tasks_md: str, master_plan: str,
                            workspace_path: str, phase_num: int) -> str:
    """Reconstruct executor prompt — mirrors harvest.py._build_executor_prompt."""
    plan_snippet = master_plan[:2000] if master_plan else "(no master plan)"
    return (
        f"You are implementing Phase {phase_num} of a project.\n"
        f"IMPORTANT: Only implement Phase {phase_num} tasks. "
        f"Do NOT implement tasks from other phases.\n\n"
        f"## Master Plan\n{plan_snippet}\n\n"
        f"## Phase {phase_num} Tasks\n{tasks_md}\n\n"
        f"## Workspace\n{workspace_path}\n"
    )


def _generate_output(llm, prompt: str, system: str = "") -> str:
    """Call an LLM and return its raw text output."""
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = llm.chat(messages)
    return resp.content or ""


def _workspace_as_document(workspace: pathlib.Path, max_files: int = 40) -> str:
    """Serialize workspace files — mirrors harvest.py._workspace_as_document."""
    parts: list[str] = []
    skip = ("__pycache__", ".pyc", ".egg-info", ".git")
    files = sorted(
        [f for f in workspace.rglob("*")
         if f.is_file() and not any(p in str(f) for p in skip)],
        key=lambda f: f.suffix != ".py"
    )[:max_files]
    for f in files:
        rel = str(f.relative_to(workspace))
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            if len(content) > 50_000:
                content = content[:50_000] + "\n... (truncated)"
            parts.append(f"=== {rel} ===\n{content}")
        except OSError:
            parts.append(f"=== {rel} ===\n(unreadable)")
    return "\n\n".join(parts)


def _already_raced(slug: str, phase: int) -> bool:
    """Check race_log.jsonl for a prior result on this (slug, phase)."""
    rlog = _race_log()
    if not rlog.exists():
        return False
    try:
        for line in rlog.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("slug") == slug and rec.get("phase") == phase:
                return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Core race function
# ---------------------------------------------------------------------------

EXECUTOR_SYSTEM = (
    "You are an expert software engineer. "
    "Implement the following phase tasks exactly as specified, "
    "writing all required files to the workspace. "
    "Output the complete file contents for each file."
)


def race_phase(
    proj_dir: pathlib.Path,
    phase_num: int,
    llm_a,
    llm_b,
    provider_a: str,
    model_a: str,
    provider_b: str,
    model_b: str,
    judge,
    replay_mode: bool = False,
) -> RaceResult | None:
    """
    Race two models on a single phase.

    In replay mode (--replay):
      - model_b output = existing workspace (the pipeline's own output)
      - model_a output = freshly generated by llm_a
      This is the primary mode: compare the fine-tune/base model against
      what the pipeline already produced.

    In live mode (--live):
      - Both models generate fresh outputs simultaneously
      - The winning output does NOT overwrite the workspace
      - Use for real-time comparison on in-flight phases
    """
    slug = proj_dir.name
    phase_dir = proj_dir / "phases" / f"phase_{phase_num}"
    workspace  = proj_dir / "workspace"

    if not phase_dir.exists():
        return None

    tasks_md    = _read_safe(phase_dir / "tasks.md")
    master_plan = _read_safe(proj_dir / "state" / "master_plan.md")

    if not tasks_md:
        return None

    prompt = _build_executor_prompt(
        tasks_md=tasks_md,
        master_plan=master_plan,
        workspace_path=str(workspace),
        phase_num=phase_num,
    )

    # --- Get output B ---
    if replay_mode:
        # B = what the pipeline already produced
        if not workspace.exists():
            return None
        output_b = _workspace_as_document(workspace)
        if not output_b:
            return None
        label_b = f"{model_b} (pipeline)"
    else:
        # B = freshly generated
        print(f"    [{model_b}] generating...", end="", flush=True)
        t0 = time.time()
        output_b = _generate_output(llm_b, prompt, system=EXECUTOR_SYSTEM)
        print(f" {time.time()-t0:.0f}s")

    # --- Get output A ---
    print(f"    [{model_a}] generating...", end="", flush=True)
    t0 = time.time()
    output_a = _generate_output(llm_a, prompt, system=EXECUTOR_SYSTEM)
    print(f" {time.time()-t0:.0f}s")
    label_a = model_a

    if not output_a or not output_b:
        print(f"    SKIP {slug}/phase_{phase_num} — empty output from one provider")
        return None

    # --- Judge ---
    print(f"    [judge] scoring...", end="", flush=True)
    t0 = time.time()
    compare_result = judge.compare(
        prompt=prompt,
        output_a=output_a,
        output_b=output_b,
        label_a=label_a,
        label_b=label_b if not replay_mode else f"{model_b}_pipeline",
    )
    print(f" {time.time()-t0:.0f}s  winner={compare_result.winner_label}  "
          f"margin={compare_result.margin:.1f}")

    result = RaceResult(
        slug=slug,
        phase=phase_num,
        raced_at=datetime.now(timezone.utc).isoformat(),
        provider_a=provider_a,
        model_a=model_a,
        provider_b=provider_b,
        model_b=model_b,
        score_a=compare_result.score_a.weighted,
        score_b=compare_result.score_b.weighted,
        winner=compare_result.winner,
        winner_label=compare_result.winner_label,
        margin=compare_result.margin,
        is_tie=compare_result.is_tie,
        prompt_chars=len(prompt),
        chosen_text=compare_result.dpo_chosen,
        rejected_text=compare_result.dpo_rejected,
    )

    return result


# ---------------------------------------------------------------------------
# Batch modes
# ---------------------------------------------------------------------------

def run_replay(
    llm_a, provider_a: str, model_a: str,
    provider_b: str, model_b: str,
    judge,
    max_races: int = 0,
    skip_raced: bool = True,
    status_filter: str = "complete",
) -> list[RaceResult]:
    """
    Replay mode: walk all completed phases, race model_a against the
    pipeline's existing workspace output (model_b = pipeline).

    Each non-tie result is appended to race_log.jsonl + dpo_race.jsonl.
    """
    results: list[RaceResult] = []
    raced = 0

    for proj_dir in sorted(_projects_dir().iterdir()):
        if not proj_dir.is_dir():
            continue
        state_file = proj_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if status_filter and state.get("status") != status_filter:
            continue

        total_phases = int(state.get("total_phases", 0))
        for phase_num in range(1, total_phases + 1):
            if skip_raced and _already_raced(proj_dir.name, phase_num):
                continue

            print(f"  Racing {proj_dir.name} / phase_{phase_num}")
            result = race_phase(
                proj_dir=proj_dir,
                phase_num=phase_num,
                llm_a=llm_a,
                llm_b=None,           # not used in replay
                provider_a=provider_a,
                model_a=model_a,
                provider_b=provider_b,
                model_b=model_b,
                judge=judge,
                replay_mode=True,
            )
            if result is None:
                continue

            # Persist
            _append_jsonl(_race_log(), result.to_log_dict())
            if not result.is_tie and result.chosen_text and result.rejected_text:
                dpo_rec = {
                    "prompt":   result.chosen_text[:500] + "...",  # prompt summary
                    "chosen":   result.chosen_text,
                    "rejected": result.rejected_text,
                    "_meta": {
                        "slug":         result.slug,
                        "phase":        result.phase,
                        "winner_label": result.winner_label,
                        "margin":       result.margin,
                        "source":       "race",
                    },
                }
                _append_jsonl(_dpo_race(), dpo_rec)

            results.append(result)
            raced += 1
            if max_races and raced >= max_races:
                return results

    return results


def run_stats() -> None:
    """Print a summary of all race results from race_log.jsonl."""
    rlog = _race_log()
    if not rlog.exists():
        print("  No race log found at", rlog)
        return

    records: list[dict] = []
    for line in rlog.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except Exception:
                pass

    if not records:
        print("  Race log is empty.")
        return

    total    = len(records)
    ties     = sum(1 for r in records if r.get("is_tie"))
    a_wins   = sum(1 for r in records if r.get("winner") == "a" and not r.get("is_tie"))
    b_wins   = sum(1 for r in records if r.get("winner") == "b" and not r.get("is_tie"))
    avg_margin = sum(r.get("margin", 0) for r in records) / total
    avg_a    = sum(r.get("score_a", 0) for r in records) / total
    avg_b    = sum(r.get("score_b", 0) for r in records) / total

    # DPO pairs generated
    dpo_count = 0
    dpo_path = _dpo_race()
    if dpo_path.exists():
        dpo_count = sum(1 for l in dpo_path.read_text(encoding="utf-8").splitlines() if l.strip())

    SEP = "-" * 55
    print(f"\n  {SEP}")
    print(f"  RACE RESULTS")
    print(f"  {SEP}")
    print(f"  Total races:      {total}")
    print(f"  Ties (skipped):   {ties}  ({100*ties//total}%)")
    print(f"  Model A wins:     {a_wins}")
    print(f"  Model B wins:     {b_wins}")
    print(f"  Avg score A:      {avg_a:.1f}")
    print(f"  Avg score B:      {avg_b:.1f}")
    print(f"  Avg margin:       {avg_margin:.1f}")
    print(f"  DPO pairs gen:    {dpo_count}  →  {dpo_path}")
    print(f"  Race log:         {rlog}")

    # Per-model breakdown
    models_a = {}
    for r in records:
        ma = r.get("model_a", "?")
        models_a.setdefault(ma, {"races": 0, "wins": 0, "score_sum": 0.0})
        models_a[ma]["races"] += 1
        models_a[ma]["score_sum"] += r.get("score_a", 0)
        if r.get("winner") == "a" and not r.get("is_tie"):
            models_a[ma]["wins"] += 1

    print(f"\n  Model A breakdown:")
    for model, stats in sorted(models_a.items()):
        avg = stats["score_sum"] / stats["races"]
        win_pct = 100 * stats["wins"] // stats["races"] if stats["races"] else 0
        print(f"    {model}: {stats['races']} races, "
              f"{stats['wins']} wins ({win_pct}%), avg={avg:.1f}")

    print(f"  {SEP}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Race two LLM providers on pipeline phases — produces DPO pairs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Replay all completed phases, racing grok-3-fast vs the pipeline's own output:
  python pipeline/finetune/race.py --replay --provider-a grok --model-a grok-3-fast

  # Replay with a local fine-tuned challenger:
  python pipeline/finetune/race.py --replay \\
      --provider-a ollama --model-a qwen3_finetune:35b \\
      --provider-b ollama --model-b qwen3.6:35b-a3b-q4_K_M \\
      --max-races 20

  # Show race statistics:
  python pipeline/finetune/race.py --stats
""",
    )
    parser.add_argument("--replay", action="store_true",
                        help="Race model-a against existing pipeline workspace output")
    parser.add_argument("--stats",  action="store_true",
                        help="Print race statistics")
    parser.add_argument("--provider-a", default="grok",
                        choices=["openai", "claude", "gemini", "ollama", "grok"],
                        help="Provider for challenger A (default: grok)")
    parser.add_argument("--model-a", default="grok-3-fast",
                        help="Model for challenger A (default: grok-3-fast)")
    parser.add_argument("--provider-b", default="ollama",
                        choices=["openai", "claude", "gemini", "ollama", "grok"],
                        help="Provider for challenger B / pipeline (default: ollama)")
    parser.add_argument("--model-b",
                        default=None,
                        help=f"Model for challenger B (default: {DEFAULT_PIPELINE_MODEL})")
    parser.add_argument("--judge-provider", default="ollama",
                        help="Provider for the judge LLM (default: ollama)")
    parser.add_argument("--judge-model", default=DEFAULT_PIPELINE_MODEL,
                        help=f"Model for the judge LLM (default: {DEFAULT_PIPELINE_MODEL})")
    parser.add_argument("--max-races", type=int, default=0,
                        help="Stop after N races (0 = unlimited, default: 0)")
    parser.add_argument("--status", default="complete",
                        help="Only race projects with this status (default: complete)")
    parser.add_argument("--re-race", action="store_true",
                        help="Re-race phases already in race_log (default: skip)")
    parser.add_argument("--pipeline-dir", default=None,
                        help="Override .pipeline directory")

    args = parser.parse_args()

    if not args.replay and not args.stats:
        parser.print_help()
        sys.exit(0)

    # Stats-only mode
    if args.stats:
        run_stats()
        return

    # Override pipeline dir if provided
    global _pipeline_override
    if args.pipeline_dir:
        _pipeline_override = pathlib.Path(args.pipeline_dir)

    import os
    model_b = args.model_b or DEFAULT_PIPELINE_MODEL

    print(f"\n  Challenger A:  {args.provider_a} / {args.model_a}")
    print(f"  Challenger B:  {args.provider_b} / {model_b}  (pipeline baseline)")
    print(f"  Judge:         {args.judge_provider} / {args.judge_model}")
    print(f"  Mode:          {'replay' if args.replay else 'live'}")
    print(f"  Status filter: {args.status}")
    print(f"  Max races:     {args.max_races or 'unlimited'}")
    print(f"  Skip raced:    {not args.re_race}")
    print()

    # Init LLMs
    llm_a   = _load_llm(args.provider_a, args.model_a)
    llm_judge = _load_llm(args.judge_provider, args.judge_model)

    sys.path.insert(0, str(ROOT))
    from pipeline.finetune.judge import CodeJudge  # type: ignore[import]
    judge = CodeJudge(llm_judge)

    if args.replay:
        results = run_replay(
            llm_a=llm_a,
            provider_a=args.provider_a,
            model_a=args.model_a,
            provider_b=args.provider_b,
            model_b=model_b,
            judge=judge,
            max_races=args.max_races,
            skip_raced=not args.re_race,
            status_filter=args.status,
        )
        print(f"\n  Races completed: {len(results)}")
        non_tie = [r for r in results if not r.is_tie]
        print(f"  Non-tie results: {len(non_tie)}")
        print(f"  DPO pairs added: {len(non_tie)}")
        print(f"  Race log:        {_race_log()}")
        print(f"  DPO pairs:       {_dpo_race()}\n")
        run_stats()


if __name__ == "__main__":
    main()
