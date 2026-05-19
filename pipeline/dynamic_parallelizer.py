"""
pipeline/dynamic_parallelizer.py
Dynamic parallel-seed tuner for the agent pipeline.

Detects diminishing returns on parallel project seeds and auto-adjusts
the concurrency level to maximize pipeline throughput (tokens/sec) without
causing GPU VRAM thrashing or inference stalls.

How it works
------------
Each observation period (default 5 min) the tuner measures:
  - pipeline_tps  : cumulative_tokens / cumulative_wall_s  (true pipeline speed)
  - inference_tps : cumulative_tokens / cumulative_inference_s  (GPU speed)
  - gpu_loaded    : True if the model is resident in VRAM (from /api/ps)

The tuner maintains a short history of (seeds, pipeline_tps) pairs.
It computes **marginal efficiency** = Δtps / Δseeds between the last
two observations.  If marginal efficiency is positive and above a minimum
threshold, it steps seeds up.  If negative (adding seeds hurt throughput),
it steps down.  If the GPU becomes IDLE (model evicted), it steps down
immediately regardless of throughput.

This mirrors the PufferLib principle of profiling actual throughput and
back-pressuring the environment pool to match real compute capacity.

Usage (wired into runner.py's main loop)
-----------------------------------------
    from pipeline.dynamic_parallelizer import DynamicParallelizer
    tuner = DynamicParallelizer(min_seeds=1, max_seeds=4)

    # Inside the monitoring loop (every health check):
    action = tuner.observe(
        throughput_path=PIPELINE_DIR / "state" / "throughput.json",
        current_seeds=parallel_seeds,
        gpu_idle=gpu_is_idle,   # True if Ollama reports no model loaded
    )
    if action.changed:
        parallel_seeds = action.new_seeds
        print(action.reason)
"""
from __future__ import annotations

import json
import math
import pathlib
import time
from dataclasses import dataclass, field
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Tuning constants (all overridable via env vars for quick experiments)
# ---------------------------------------------------------------------------
import os

_OBS_WINDOW_S      = int(os.environ.get("DP_OBS_WINDOW",     "300"))   # 5 min per sample
_COOLDOWN_S        = int(os.environ.get("DP_COOLDOWN",        "600"))   # 10 min between decisions
_MIN_EFFICIENCY    = float(os.environ.get("DP_MIN_EFFICIENCY", "0.05")) # Δtps/seed below this = no gain
_TPS_DROP_THRESH   = float(os.environ.get("DP_DROP_THRESH",   "0.10")) # 10% tps drop → step down
_HISTORY_WINDOW    = int(os.environ.get("DP_HISTORY",          "4"))   # num samples to trend over
_MIN_CALLS_FOR_OBS = int(os.environ.get("DP_MIN_CALLS",        "5"))   # need ≥N LLM calls in window

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class _Sample(NamedTuple):
    """One observation point."""
    ts:             float   # wall-clock timestamp
    seeds:          int     # active parallel seeds at observation time
    pipeline_tps:   float   # tokens / total_wall_s
    inference_tps:  float   # tokens / inference_s (GPU speed)
    call_count:     int     # cumulative LLM calls (for validity check)
    gpu_loaded:     bool    # model in VRAM?


@dataclass
class TunerDecision:
    """Result returned by DynamicParallelizer.observe()."""
    changed:    bool  = False
    new_seeds:  int   = 1
    old_seeds:  int   = 1
    reason:     str   = ""
    confidence: float = 0.0   # 0-1: how confident we are in this decision


# ---------------------------------------------------------------------------
# DynamicParallelizer
# ---------------------------------------------------------------------------

class DynamicParallelizer:
    """
    Adaptive parallel-seed controller.

    Observes pipeline throughput over time and adjusts the number of
    simultaneous active projects to maximise tokens/sec while avoiding
    GPU VRAM pressure.

    Args:
        min_seeds:     Minimum parallel seeds (floor).
        max_seeds:     Maximum parallel seeds (ceiling).
        obs_window_s:  Seconds between throughput samples (default 5 min).
        cooldown_s:    Minimum seconds between seed adjustments (default 10 min).
    """

    def __init__(
        self,
        min_seeds:    int   = 1,
        max_seeds:    int   = 4,
        obs_window_s: int   = _OBS_WINDOW_S,
        cooldown_s:   int   = _COOLDOWN_S,
    ) -> None:
        self.min_seeds    = max(1, min_seeds)
        self.max_seeds    = max(self.min_seeds, max_seeds)
        self.obs_window_s = obs_window_s
        self.cooldown_s   = cooldown_s

        self._history:    list[_Sample]   = []
        self._last_sample_ts: float       = 0.0   # when we last sampled
        self._last_decision_ts: float     = 0.0   # when we last changed seeds
        self._last_tp_snapshot: dict      = {}     # previous throughput.json values

        # Trend tracking: rolling (seeds, tps) pairs for regression
        self._efficiency_log: list[tuple[int, float]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def observe(
        self,
        throughput_path: pathlib.Path,
        current_seeds:  int,
        gpu_idle:       bool = False,
    ) -> TunerDecision:
        """
        Observe current throughput and decide whether to change parallelism.

        Call this once per health-check tick (~60s). The tuner internally
        rate-limits to obs_window_s intervals.

        Args:
            throughput_path:  Path to .pipeline/state/throughput.json
            current_seeds:    Currently active parallel seed count
            gpu_idle:         True if Ollama /api/ps reports no model loaded

        Returns:
            TunerDecision — .changed=True if seeds should change, else False
        """
        now = time.time()

        # --- Immediate downscale if GPU is IDLE (model evicted) ---
        if gpu_idle and current_seeds > self.min_seeds:
            new = max(self.min_seeds, current_seeds - 1)
            self._last_decision_ts = now
            return TunerDecision(
                changed=True, new_seeds=new, old_seeds=current_seeds,
                reason=f"🔽 GPU IDLE — model evicted from VRAM, scaling {current_seeds}→{new} seeds",
                confidence=0.95,
            )

        # --- Cooldown: don't churn ---
        in_cooldown = (now - self._last_decision_ts) < self.cooldown_s
        # Still accept samples during cooldown, just don't act on them
        if (now - self._last_sample_ts) < self.obs_window_s:
            return TunerDecision(changed=False, new_seeds=current_seeds,
                                 old_seeds=current_seeds)

        # --- Sample throughput ---
        sample = self._read_sample(throughput_path, current_seeds, now)
        if sample is None:
            return TunerDecision(changed=False, new_seeds=current_seeds,
                                 old_seeds=current_seeds)

        self._last_sample_ts = now
        self._history.append(sample)
        if len(self._history) > _HISTORY_WINDOW * 2:
            self._history = self._history[-_HISTORY_WINDOW * 2:]

        # Need at least 2 samples to measure trend
        if len(self._history) < 2 or in_cooldown:
            return TunerDecision(changed=False, new_seeds=current_seeds,
                                 old_seeds=current_seeds)

        # --- Compute marginal efficiency ---
        decision = self._evaluate(current_seeds, now)
        if decision.changed:
            self._last_decision_ts = now
        return decision

    def status_line(self, current_seeds: int) -> str:
        """Return a compact one-line status string for the runner's status output."""
        if len(self._history) < 2:
            return f"⚡ parallelizer: {current_seeds} seed(s) — calibrating..."

        last = self._history[-1]
        prev = self._history[-2]
        delta_tps = last.pipeline_tps - prev.pipeline_tps
        arrow = "↑" if delta_tps > 0 else ("↓" if delta_tps < 0 else "→")
        return (
            f"⚡ parallelizer: {current_seeds} seed(s) | "
            f"pipe={last.pipeline_tps:.1f} tok/s {arrow}{abs(delta_tps):.1f} | "
            f"gpu={last.inference_tps:.0f} tok/s | "
            f"{'🟢 VRAM' if last.gpu_loaded else '🔴 EVICTED'}"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_sample(
        self,
        path: pathlib.Path,
        seeds: int,
        ts: float,
    ) -> _Sample | None:
        """Read throughput.json and return a _Sample, or None if stale/invalid."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

        # Reject if data is stale (not updated in the last 2× obs windows)
        updated_at = data.get("updated_at", 0)
        if ts - updated_at > self.obs_window_s * 2:
            return None

        call_count = data.get("call_count", 0)
        cum_tok    = data.get("cumulative_tokens", 0)
        cum_wall   = data.get("cumulative_wall_s", 1) or 1
        cum_inf    = data.get("cumulative_inference_s", 1) or 1

        # Require minimum LLM call delta since last snapshot
        prev_calls = self._last_tp_snapshot.get("call_count", 0)
        if call_count - prev_calls < _MIN_CALLS_FOR_OBS:
            return None

        # Compute delta tps (marginal, not cumulative) for the window
        prev_tok  = self._last_tp_snapshot.get("cumulative_tokens", 0)
        prev_wall = self._last_tp_snapshot.get("cumulative_wall_s", 0)
        delta_tok  = cum_tok  - prev_tok
        delta_wall = cum_wall - prev_wall

        if delta_wall <= 0 or delta_tok <= 0:
            # Fall back to cumulative
            pipeline_tps  = cum_tok / cum_wall
            inference_tps = cum_tok / cum_inf
        else:
            pipeline_tps  = delta_tok / delta_wall
            inference_tps = data.get("tps", pipeline_tps)  # last-call GPU tok/s

        self._last_tp_snapshot = dict(data)

        # GPU loaded: approximate from inference utilisation ratio
        # (No direct /api/ps here — caller passes gpu_idle instead)
        gpu_util = (cum_inf / cum_wall) if cum_wall > 0 else 0
        gpu_loaded = gpu_util > 0.1  # >10% of wall time is inference = model loaded

        return _Sample(
            ts=ts,
            seeds=seeds,
            pipeline_tps=pipeline_tps,
            inference_tps=inference_tps,
            call_count=call_count,
            gpu_loaded=gpu_loaded,
        )

    def _evaluate(self, current_seeds: int, now: float) -> TunerDecision:
        """Decide whether to scale up or down based on throughput trend."""
        # Group history by seed count and compute mean tps per level
        seed_tps: dict[int, list[float]] = {}
        for s in self._history:
            seed_tps.setdefault(s.seeds, []).append(s.pipeline_tps)
        means: dict[int, float] = {k: sum(v)/len(v) for k, v in seed_tps.items()}

        last = self._history[-1]
        prev = self._history[-2]

        tps_now  = last.pipeline_tps
        tps_prev = prev.pipeline_tps

        # --- Drop signal: throughput fell despite same or more seeds ---
        if tps_now < tps_prev * (1 - _TPS_DROP_THRESH) and current_seeds > self.min_seeds:
            new = max(self.min_seeds, current_seeds - 1)
            confidence = min(1.0, (tps_prev - tps_now) / (tps_prev + 1e-6))
            return TunerDecision(
                changed=True, new_seeds=new, old_seeds=current_seeds,
                reason=(
                    f"🔽 Throughput dropped {tps_prev:.1f}→{tps_now:.1f} tok/s "
                    f"({(tps_prev-tps_now)/tps_prev*100:.0f}%) — "
                    f"scaling {current_seeds}→{new} seeds"
                ),
                confidence=confidence,
            )

        # --- Marginal efficiency: did the last seed increase pay off? ---
        # Compare current seed level vs one fewer (from history if available)
        fewer_seeds = current_seeds - 1
        if fewer_seeds in means:
            tps_at_fewer = means[fewer_seeds]
            delta_tps    = tps_now - tps_at_fewer
            marginal_eff = delta_tps / max(1, current_seeds - fewer_seeds)

            if marginal_eff < -_MIN_EFFICIENCY and current_seeds > self.min_seeds:
                # Adding a seed was net-negative
                new = max(self.min_seeds, current_seeds - 1)
                return TunerDecision(
                    changed=True, new_seeds=new, old_seeds=current_seeds,
                    reason=(
                        f"🔽 Diminishing returns: marginal efficiency {marginal_eff:.3f} tok/s/seed "
                        f"(threshold {-_MIN_EFFICIENCY:.3f}) — "
                        f"scaling {current_seeds}→{new} seeds"
                    ),
                    confidence=min(1.0, abs(marginal_eff) / _MIN_EFFICIENCY),
                )

        # --- Growth signal: throughput is stable/growing → try one more seed ---
        if (
            current_seeds < self.max_seeds
            and tps_now >= tps_prev * (1 - _MIN_EFFICIENCY / 2)  # not degrading
        ):
            # Extra guard: only scale up if inference tok/s is high
            # (i.e., GPU is not already the bottleneck at this seed count)
            if last.inference_tps > 10:  # tok/s floor to filter Ollama warmup noise
                new = min(self.max_seeds, current_seeds + 1)
                return TunerDecision(
                    changed=True, new_seeds=new, old_seeds=current_seeds,
                    reason=(
                        f"🔼 Throughput stable {tps_prev:.1f}→{tps_now:.1f} tok/s, "
                        f"GPU at {last.inference_tps:.0f} tok/s — "
                        f"scaling {current_seeds}→{new} seeds"
                    ),
                    confidence=0.6,
                )

        # --- Hold: no clear signal ---
        return TunerDecision(
            changed=False, new_seeds=current_seeds, old_seeds=current_seeds,
            reason=f"→ Holding at {current_seeds} seed(s) (no clear signal)",
        )

    def reset(self) -> None:
        """Clear history (call when provider/model changes)."""
        self._history.clear()
        self._last_tp_snapshot.clear()
        self._last_sample_ts    = 0.0
        self._last_decision_ts  = 0.0


# ---------------------------------------------------------------------------
# Convenience: module-level singleton
# ---------------------------------------------------------------------------
_tuner: DynamicParallelizer | None = None


def get_tuner(min_seeds: int = 1, max_seeds: int = 4) -> DynamicParallelizer:
    """Return (or create) the process-level DynamicParallelizer singleton."""
    global _tuner
    if _tuner is None:
        _tuner = DynamicParallelizer(min_seeds=min_seeds, max_seeds=max_seeds)
    return _tuner
