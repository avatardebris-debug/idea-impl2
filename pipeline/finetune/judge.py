#!/usr/bin/env python3
"""
pipeline/finetune/judge.py
LLM Judge for scoring and comparing code outputs.

Two modes:
  1. Single scoring    — score one output against rubric (0-100)
  2. Head-to-head      — compare two outputs, pick winner (for racing system)

The head-to-head mode is used by the Grok Build / fine-tune racing system:
  - Run same phase through Grok Build CLI AND local fine-tuned model
  - Judge picks winner based on rubric
  - Winner enters training pool as "chosen", loser as "rejected"
  - Fine-tune gets reward signal from results

Rubric (weights):
  Correctness    35%  — all tasks marked done, key files present
  Completeness   25%  — all tasks in phase implemented, no stubs
  WS Compliance  20%  — correct workspace paths, no double-nesting
  Code Quality   15%  — clean imports, no hallucinations, proper structure
  Conciseness     5%  — task-scoped, no over-engineering

Usage:
    from pipeline.finetune.judge import CodeJudge
    judge = CodeJudge(llm)
    result = judge.compare(prompt, output_a, output_b, label_a="grok", label_b="finetune")
    print(result.winner, result.scores)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rubric
# ---------------------------------------------------------------------------

RUBRIC = {
    "correctness":   {"weight": 0.35, "desc": "All tasks marked [x], key files present, passes basic sanity checks"},
    "completeness":  {"weight": 0.25, "desc": "All tasks implemented, no TODO stubs, no placeholder functions"},
    "ws_compliance": {"weight": 0.20, "desc": "Files at correct workspace paths, no workspace/workspace/ nesting, correct package structure"},
    "code_quality":  {"weight": 0.15, "desc": "No hallucinated imports, clean structure, proper error handling, follows Python conventions"},
    "conciseness":   {"weight": 0.05, "desc": "Task-scoped output, no unnecessary boilerplate or over-engineering"},
}

TOTAL_WEIGHT = sum(d["weight"] for d in RUBRIC.values())  # should be 1.0


# ---------------------------------------------------------------------------
# Judge results
# ---------------------------------------------------------------------------

@dataclass
class ScoreCard:
    """Scores for a single output."""
    label:       str
    scores:      dict[str, float]   # dimension → 0-100
    weighted:    float              # overall weighted score
    reasoning:   dict[str, str]     # dimension → explanation
    raw_response: str = ""

    @classmethod
    def zero(cls, label: str) -> "ScoreCard":
        return cls(
            label=label,
            scores={d: 0.0 for d in RUBRIC},
            weighted=0.0,
            reasoning={d: "" for d in RUBRIC},
        )


@dataclass
class CompareResult:
    """Result of a head-to-head comparison."""
    winner:       str           # label of winner ("a", "b", or "tie")
    winner_label: str           # human label ("grok" or "finetune")
    score_a:      ScoreCard
    score_b:      ScoreCard
    margin:       float         # abs(weighted_a - weighted_b)
    is_tie:       bool          # True if margin < TIE_THRESHOLD
    dpo_chosen:   str           # the winning output text
    dpo_rejected: str           # the losing output text


TIE_THRESHOLD = 3.0  # margin below which we call it a tie (don't train on ambiguous)


# ---------------------------------------------------------------------------
# Judge prompts
# ---------------------------------------------------------------------------

_SCORE_SYSTEM = """You are an expert code review judge evaluating LLM-generated
software implementations. Score the output objectively using only the provided rubric.
Be strict but fair. Return ONLY valid JSON — no markdown, no commentary."""

_SCORE_USER_TEMPLATE = """Evaluate this code implementation against the rubric.

## Task Prompt (what was asked)
{prompt}

## Implementation Output to Score
{output}

## Scoring Rubric
{rubric_text}

Return JSON in exactly this format:
{{
  "correctness":   {{"score": <0-100>, "reason": "<one sentence>"}},
  "completeness":  {{"score": <0-100>, "reason": "<one sentence>"}},
  "ws_compliance": {{"score": <0-100>, "reason": "<one sentence>"}},
  "code_quality":  {{"score": <0-100>, "reason": "<one sentence>"}},
  "conciseness":   {{"score": <0-100>, "reason": "<one sentence>"}}
}}"""

_COMPARE_USER_TEMPLATE = """Compare two code implementations of the same task.

## Task Prompt
{prompt}

## Implementation A ({label_a})
{output_a}

## Implementation B ({label_b})
{output_b}

## Scoring Rubric
{rubric_text}

Score BOTH implementations on each dimension then pick the winner.
Return JSON in exactly this format:
{{
  "a": {{
    "correctness":   {{"score": <0-100>, "reason": "<one sentence>"}},
    "completeness":  {{"score": <0-100>, "reason": "<one sentence>"}},
    "ws_compliance": {{"score": <0-100>, "reason": "<one sentence>"}},
    "code_quality":  {{"score": <0-100>, "reason": "<one sentence>"}},
    "conciseness":   {{"score": <0-100>, "reason": "<one sentence>"}}
  }},
  "b": {{
    "correctness":   {{"score": <0-100>, "reason": "<one sentence>"}},
    "completeness":  {{"score": <0-100>, "reason": "<one sentence>"}},
    "ws_compliance": {{"score": <0-100>, "reason": "<one sentence>"}},
    "code_quality":  {{"score": <0-100>, "reason": "<one sentence>"}},
    "conciseness":   {{"score": <0-100>, "reason": "<one sentence>"}}
  }},
  "winner": "<a or b or tie>",
  "summary": "<one sentence explaining the key difference>"
}}"""


def _build_rubric_text() -> str:
    lines = []
    for dim, meta in RUBRIC.items():
        lines.append(f"- {dim} ({int(meta['weight']*100)}%): {meta['desc']}")
    return "\n".join(lines)


def _weighted_score(scores: dict[str, float]) -> float:
    total = 0.0
    for dim, meta in RUBRIC.items():
        total += scores.get(dim, 0.0) * meta["weight"]
    return round(total, 2)


def _extract_json(text: str) -> dict:
    """Extract first JSON object from a potentially messy LLM response."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first {...} block
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON from judge response: {text[:200]}")


# ---------------------------------------------------------------------------
# Judge class
# ---------------------------------------------------------------------------

class CodeJudge:
    """
    LLM-powered code quality judge.

    Args:
        llm:         Any LLMBase adapter (Ollama, Grok, OpenAI, etc.)
        max_chars:   Truncate outputs to this length before sending to judge
                     (prevents context overflow on long implementations)
    """

    def __init__(self, llm, max_chars: int = 12_000) -> None:
        self._llm = llm
        self._max_chars = max_chars
        self._rubric_text = _build_rubric_text()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, prompt: str, output: str, label: str = "output") -> ScoreCard:
        """
        Score a single implementation against the rubric.

        Returns a ScoreCard with per-dimension scores and reasoning.
        Falls back to ScoreCard.zero() on LLM error.
        """
        output_trunc = output[:self._max_chars]
        prompt_trunc = prompt[:3000]

        user_msg = _SCORE_USER_TEMPLATE.format(
            prompt=prompt_trunc,
            output=output_trunc,
            rubric_text=self._rubric_text,
        )
        messages = [
            {"role": "system",  "content": _SCORE_SYSTEM},
            {"role": "user",    "content": user_msg},
        ]

        try:
            resp = self._llm.chat(messages)
            raw = resp.content or ""
            data = _extract_json(raw)
            scores = {}
            reasoning = {}
            for dim in RUBRIC:
                entry = data.get(dim, {})
                scores[dim]    = float(entry.get("score", 0))
                reasoning[dim] = entry.get("reason", "")
            return ScoreCard(
                label=label,
                scores=scores,
                weighted=_weighted_score(scores),
                reasoning=reasoning,
                raw_response=raw,
            )
        except Exception as exc:
            log.warning("Judge.score failed for %s: %s", label, exc)
            return ScoreCard.zero(label)

    def compare(
        self,
        prompt:   str,
        output_a: str,
        output_b: str,
        label_a:  str = "a",
        label_b:  str = "b",
    ) -> CompareResult:
        """
        Head-to-head comparison of two implementations.

        Used by the racing system:
            result = judge.compare(prompt, grok_output, finetune_output,
                                   label_a="grok", label_b="finetune")
            if result.winner_label == "finetune":
                # fine-tune beat grok build — strong reward signal
                add_to_training(chosen=result.dpo_chosen, rejected=result.dpo_rejected)
        """
        a_trunc = output_a[:self._max_chars]
        b_trunc = output_b[:self._max_chars]
        p_trunc = prompt[:3000]

        user_msg = _COMPARE_USER_TEMPLATE.format(
            prompt=p_trunc,
            output_a=a_trunc,
            output_b=b_trunc,
            label_a=label_a,
            label_b=label_b,
            rubric_text=self._rubric_text,
        )
        messages = [
            {"role": "system", "content": _SCORE_SYSTEM},
            {"role": "user",   "content": user_msg},
        ]

        try:
            resp = self._llm.chat(messages)
            raw = resp.content or ""
            data = _extract_json(raw)

            # Build scorecards
            card_a = self._parse_scorecard(data.get("a", {}), label_a)
            card_b = self._parse_scorecard(data.get("b", {}), label_b)

            llm_winner = data.get("winner", "tie").lower().strip()
            margin = abs(card_a.weighted - card_b.weighted)
            is_tie = margin < TIE_THRESHOLD or llm_winner == "tie"

            if is_tie:
                winner, winner_label = "tie", "tie"
                chosen, rejected = output_a, output_b  # arbitrary on tie
            elif llm_winner == "a" or card_a.weighted > card_b.weighted:
                winner, winner_label = "a", label_a
                chosen, rejected = output_a, output_b
            else:
                winner, winner_label = "b", label_b
                chosen, rejected = output_b, output_a

            return CompareResult(
                winner=winner,
                winner_label=winner_label,
                score_a=card_a,
                score_b=card_b,
                margin=margin,
                is_tie=is_tie,
                dpo_chosen=chosen,
                dpo_rejected=rejected,
            )

        except Exception as exc:
            log.warning("Judge.compare failed: %s", exc)
            # Fall back to individual scores
            card_a = self.score(prompt, output_a, label_a)
            card_b = self.score(prompt, output_b, label_b)
            margin = abs(card_a.weighted - card_b.weighted)
            is_tie = margin < TIE_THRESHOLD
            if is_tie or card_a.weighted >= card_b.weighted:
                winner, winner_label = "a", label_a
                chosen, rejected = output_a, output_b
            else:
                winner, winner_label = "b", label_b
                chosen, rejected = output_b, output_a
            return CompareResult(
                winner=winner,
                winner_label=winner_label,
                score_a=card_a,
                score_b=card_b,
                margin=margin,
                is_tie=is_tie,
                dpo_chosen=chosen,
                dpo_rejected=rejected,
            )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _parse_scorecard(self, data: dict, label: str) -> ScoreCard:
        scores = {}
        reasoning = {}
        for dim in RUBRIC:
            entry = data.get(dim, {})
            scores[dim]    = float(entry.get("score", 0))
            reasoning[dim] = entry.get("reason", "")
        return ScoreCard(
            label=label,
            scores=scores,
            weighted=_weighted_score(scores),
            reasoning=reasoning,
        )


# ---------------------------------------------------------------------------
# CLI: score or compare outputs from files
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse, pathlib, sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
    from llm_interface import get_llm

    parser = argparse.ArgumentParser(description="LLM Judge for code quality scoring")
    parser.add_argument("--prompt",    required=True, help="File containing the executor prompt")
    parser.add_argument("--output-a",  required=True, help="File containing implementation A")
    parser.add_argument("--output-b",  help="File containing implementation B (enables head-to-head)")
    parser.add_argument("--label-a",   default="a")
    parser.add_argument("--label-b",   default="b")
    parser.add_argument("--provider",  default="ollama")
    parser.add_argument("--model",     default="qwen3.6:35b-a3b-q4_K_M")
    args = parser.parse_args()

    llm   = get_llm(args.provider, model=args.model, temperature=0.1)
    judge = CodeJudge(llm)

    prompt   = pathlib.Path(args.prompt).read_text(encoding="utf-8")
    output_a = pathlib.Path(args.output_a).read_text(encoding="utf-8")

    if args.output_b:
        output_b = pathlib.Path(args.output_b).read_text(encoding="utf-8")
        result = judge.compare(prompt, output_a, output_b, args.label_a, args.label_b)
        print(f"\n  Winner: {result.winner_label}  (margin: {result.margin:.1f})")
        print(f"  {args.label_a}: {result.score_a.weighted:.1f}   {args.label_b}: {result.score_b.weighted:.1f}")
        print(f"  Tie: {result.is_tie}")
        for dim in RUBRIC:
            print(f"    {dim:15s}: A={result.score_a.scores[dim]:.0f}  B={result.score_b.scores[dim]:.0f}")
    else:
        card = judge.score(prompt, output_a, args.label_a)
        print(f"\n  Score: {card.weighted:.1f}")
        for dim, score in card.scores.items():
            print(f"    {dim:15s}: {score:.0f}  — {card.reasoning[dim]}")


if __name__ == "__main__":
    main()
