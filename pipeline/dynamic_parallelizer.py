"""
pipeline/dynamic_parallelizer.py
Dynamic parallel-seed tuner for the agent pipeline.

Detects diminishing returns on parallel project seeds and auto-adjusts
the concurrency level to maximize pipeline throughput (tokens/sec) without
causing GPU VRAM thrashing or inference stalls.

Signal Architecture (three tiers)
-----------------------------------
Tier 1 — Hard veto (always wins):
  GPU IDLE (model evicted) → immediate scale down, no other checks needed.

Tier 2 — GPU headroom gate (blocks scale-up):
  GPU util > _GPU_HIGH_PCT  → don't scale up even if trend is bullish.
  GPU util < _GPU_LOW_PCT   → headroom confirmed, scale-up gated only by trend.

Tier 3 — EMA-3/EMA-10 crossover (directional signal):
  EMA-3 > EMA-10 (uptrend)  + GPU headroom → scale up
  EMA-3 < EMA-10 (downtrend) for ≥2 consecutive reads → scale down
  Signals disagree → hold

Bootstrap fallback (warm-up period):
  Until _EMA_SLOW samples have been collected, the old marginal-efficiency
  comparison is used.  This prevents cold-start decisions on meaningless EMAs.
  EMA is seeded from the FIRST real measurement (not zero) to minimise bias.

Crossover hysteresis:
  A scale-up requires 2 consecutive bullish crossover reads (EMA3 > EMA10).
  Scale-down on trend only requires 2 consecutive bearish reads.
  Eviction bypasses hysteresis entirely.

EMA periods and sampling rate:
  obs_window_s = 300 s (5 min), so 1 sample ≈ 5 min.
  EMA-3  ≈ 15 min lookback (alpha = 0.5)
  EMA-10 ≈ 50 min lookback (alpha = 0.182)
  This covers 0.5–3× a typical phase duration (10–30 min).

Usage (wired into runner.py's main loop)
-----------------------------------------
    from pipeline.dynamic_parallelizer import DynamicParallelizer
    tuner = DynamicParallelizer(min_seeds=1, max_seeds=4)

    # Inside the monitoring loop (every health check):
    action = tuner.observe(
        throughput_path=PIPELINE_DIR / "state" / "throughput.json",
        current_seeds=parallel_seeds,
        gpu_idle=gpu_is_idle,   # True if Ollama reports no model loaded
        gpu_util_pct=gpu_pct,   # 0-100 GPU compute utilisation
    )
    if action.changed:
        parallel_seeds = action.new_seeds
        print(action.reason)
"""
from __future__ import annotations

import json
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
_TPS_DROP_THRESH   = float(os.environ.get("DP_DROP_THRESH",   "0.15")) # 15% pipeline drop needed
_ITPS_DROP_THRESH  = float(os.environ.get("DP_ITPS_DROP",     "0.08")) # 8% inference drop = real contention
_HISTORY_WINDOW    = int(os.environ.get("DP_HISTORY",          "4"))   # num samples to trend over
_MIN_CALLS_FOR_OBS = int(os.environ.get("DP_MIN_CALLS",        "5"))   # need ≥N LLM calls in window

# EMA crossover periods (in samples, not seconds)
_EMA_FAST          = int(os.environ.get("DP_EMA_FAST",         "3"))   # fast EMA period
_EMA_SLOW          = int(os.environ.get("DP_EMA_SLOW",         "10"))  # slow EMA period

# GPU utilisation thresholds (percent of wall time spent in inference)
_GPU_HIGH_PCT      = float(os.environ.get("DP_GPU_HIGH",        "75")) # don't scale up above this
_GPU_LOW_PCT       = float(os.environ.get("DP_GPU_LOW",         "30")) # confirmed headroom below this

# Crossover hysteresis: require N consecutive same-direction crossings before acting
_CROSSOVER_CONFIRM = int(os.environ.get("DP_CROSSOVER_CONFIRM", "2"))

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class _Sample(NamedTuple):
    """One observation point."""
    ts:             float   # wall-clock timestamp
    seeds:          int     # active parallel seeds at observation time
    pipeline_tps:   float   # tokens / total_wall_s
    inference_tps:  float   # tokens / inference_s for THIS window (GPU speed)
    call_count:     int     # cumulative LLM calls (for validity check)
    gpu_loaded:     bool    # model in VRAM?
    gpu_util_pct:   float   # inference_s / wall_s for this window (0-100)


@dataclass
class TunerDecision:
    """Result returned by DynamicParallelizer.observe()."""
    changed:    bool  = False
    new_seeds:  int   = 1
    old_seeds:  int   = 1
    reason:     str   = ""
    confidence: float = 0.0   # 0-1: how confident we are in this decision


# ---------------------------------------------------------------------------
# EMA helper
# ---------------------------------------------------------------------------

def _ema_alpha(period: int) -> float:
    """Standard EMA smoothing factor: 2 / (period + 1)."""
    return 2.0 / (period + 1)


# ---------------------------------------------------------------------------
# DynamicParallelizer
# ---------------------------------------------------------------------------

class DynamicParallelizer:
    """
    Adaptive parallel-seed controller.

    Observes pipeline throughput over time and adjusts the number of
    simultaneous active projects to maximise tokens/sec while avoiding
    GPU VRAM pressure.

    Signal tiers:
      1. Eviction veto  — immediate downscale, no other checks
      2. GPU headroom   — blocks scale-up when GPU already saturated
      3. EMA crossover  — EMA-3/EMA-10 trend signal with hysteresis
      bootstrap         — legacy marginal efficiency until EMA warms up

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
        self._last_sample_ts: float       = 0.0
        self._last_decision_ts: float     = 0.0
        self._last_tp_snapshot: dict      = {}
        self._last_known_call_count: int  = 0

        # EMA state — seeded from first real sample to avoid cold-start bias
        self._ema_fast:   float | None    = None   # EMA-3 of pipeline_tps
        self._ema_slow:   float | None    = None   # EMA-10 of pipeline_tps
        self._alpha_fast: float           = _ema_alpha(_EMA_FAST)
        self._alpha_slow: float           = _ema_alpha(_EMA_SLOW)

        # Crossover hysteresis counter
        # +N = N consecutive bullish (fast>slow), -N = N consecutive bearish
        self._crossover_streak: int       = 0

        # Trend tracking (legacy, used during bootstrap)
        self._efficiency_log: list[tuple[int, float]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def observe(
        self,
        throughput_path: pathlib.Path,
        current_seeds:  int,
        gpu_idle:       bool  = False,
        gpu_util_pct:   float = 0.0,
    ) -> TunerDecision:
        """
        Observe current throughput and decide whether to change parallelism.

        Call this once per health-check tick (~60s). The tuner internally
        rate-limits to obs_window_s intervals.

        Args:
            throughput_path:  Path to .pipeline/state/throughput.json
            current_seeds:    Currently active parallel seed count
            gpu_idle:         True if Ollama /api/ps reports no model loaded
            gpu_util_pct:     GPU compute utilisation 0-100 (from throughput.json
                              or nvidia-smi; passed through from runner).

        Returns:
            TunerDecision — .changed=True if seeds should change, else False
        """
        now = time.time()

        # Best-effort call count update from throughput.json on every observe check
        try:
            if throughput_path.exists():
                _data = json.loads(throughput_path.read_text(encoding="utf-8"))
                self._last_known_call_count = _data.get("call_count", 0)
        except Exception:
            pass

        # ----------------------------------------------------------------
        # TIER 1 — Hard veto: eviction → immediate downscale
        # ----------------------------------------------------------------
        if gpu_idle and current_seeds > self.min_seeds:
            new = max(self.min_seeds, current_seeds - 1)
            self._last_decision_ts = now
            self._crossover_streak = 0   # reset streak — system state changed
            return TunerDecision(
                changed=True, new_seeds=new, old_seeds=current_seeds,
                reason=(
                    f"🔽 GPU IDLE — model evicted from VRAM, "
                    f"scaling {current_seeds}→{new} seeds"
                ),
                confidence=0.95,
            )

        # --- Rate limiting: only sample every obs_window_s ---
        in_cooldown = (now - self._last_decision_ts) < self.cooldown_s
        # During calibration (less than 2 history samples), sample much faster (30s)
        # to avoid keeping the user in a "calibrating..." state indefinitely.
        _window = 30 if len(self._history) < 2 else self.obs_window_s
        if (now - self._last_sample_ts) < _window:
            return TunerDecision(changed=False, new_seeds=current_seeds,
                                 old_seeds=current_seeds)

        # --- Read throughput sample ---
        sample = self._read_sample(throughput_path, current_seeds, now)
        if sample is None:
            return TunerDecision(changed=False, new_seeds=current_seeds,
                                 old_seeds=current_seeds)

        self._last_sample_ts = now
        self._history.append(sample)
        if len(self._history) > _HISTORY_WINDOW * 2:
            self._history = self._history[-_HISTORY_WINDOW * 2:]

        # Use sample's own gpu_util_pct if caller didn't pass one explicitly
        effective_gpu_pct = gpu_util_pct if gpu_util_pct > 0 else sample.gpu_util_pct

        # --- Update EMAs (seed from first real value, not zero) ---
        tps = sample.pipeline_tps
        if self._ema_fast is None:
            # Bootstrap: seed both EMAs from the first measurement
            self._ema_fast = tps
            self._ema_slow = tps
        else:
            self._ema_fast = self._alpha_fast * tps + (1 - self._alpha_fast) * self._ema_fast
            self._ema_slow = self._alpha_slow * tps + (1 - self._alpha_slow) * self._ema_slow

        # Need at least 2 samples for any trend detection
        if len(self._history) < 2 or in_cooldown:
            return TunerDecision(changed=False, new_seeds=current_seeds,
                                 old_seeds=current_seeds)

        # ----------------------------------------------------------------
        # BOOTSTRAP — use legacy method until EMA-slow has warmed up
        # ----------------------------------------------------------------
        # EMA-slow needs ~slow_period samples before it's meaningful.
        # Use the old marginal-efficiency comparison during this window.
        # ----------------------------------------------------------------
        if len(self._history) < _EMA_SLOW:
            return self._legacy_evaluate(current_seeds, now, effective_gpu_pct)

        # ----------------------------------------------------------------
        # TIER 2 + TIER 3 — EMA crossover with GPU headroom gate
        # ----------------------------------------------------------------
        decision = self._crossover_evaluate(
            current_seeds, now, effective_gpu_pct
        )
        if decision.changed:
            self._last_decision_ts = now
        return decision

    def status_line(self, current_seeds: int) -> str:
        """Return a compact one-line status string for the runner's status output."""
        if not self._history:
            if self._last_known_call_count == 0:
                return f"⚡ parallelizer: {current_seeds} seed(s) — calibrating (0/2 samples, waiting for LLM calls)..."
            return f"⚡ parallelizer: {current_seeds} seed(s) — calibrating (0/2 samples)..."

        last = self._history[-1]
        if len(self._history) < 2:
            return (
                f"⚡ parallelizer: {current_seeds} seed(s) | "
                f"pipe={last.pipeline_tps:.1f} tok/s | "
                f"inf={last.inference_tps:.0f} tok/s | "
                f"{last.gpu_util_pct:.0f}% GPU | "
                f"calibrating (1/2 samples)..."
            )

        prev = self._history[-2]

        # Show EMA crossover state once warmed up
        if self._ema_fast is not None and self._ema_slow is not None and len(self._history) >= _EMA_SLOW:
            gap = self._ema_fast - self._ema_slow
            cross_sym = "📈" if gap > 0 else "📉"
            ema_str = f" | EMA {self._ema_fast:.1f}/{self._ema_slow:.1f}{cross_sym}"
        else:
            remaining = max(0, _EMA_SLOW - len(self._history))
            ema_str = f" | warming ({remaining} samples)"

        delta_tps = last.pipeline_tps - prev.pipeline_tps
        arrow = "↑" if delta_tps > 0 else ("↓" if delta_tps < 0 else "→")
        return (
            f"⚡ parallelizer: {current_seeds} seed(s) | "
            f"pipe={last.pipeline_tps:.1f} tok/s {arrow}{abs(delta_tps):.1f} | "
            f"inf={last.inference_tps:.0f} tok/s | "
            f"{last.gpu_util_pct:.0f}% GPU"
            f"{ema_str} | "
            f"{'🟢 VRAM' if last.gpu_loaded else '🔴 EVICTED'}"
        )

    # ------------------------------------------------------------------
    # Internal: EMA crossover evaluation (post-warmup)
    # ------------------------------------------------------------------

    def _crossover_evaluate(
        self,
        current_seeds: int,
        now: float,
        gpu_pct: float,
    ) -> TunerDecision:
        """
        Three-tier decision using EMA crossover + GPU headroom gate.

        Tier 2: GPU headroom check (veto on scale-up when saturated)
        Tier 3: EMA-3/EMA-10 crossover with hysteresis streak counter
        """
        fast = self._ema_fast
        slow = self._ema_slow
        last = self._history[-1]

        bullish = fast > slow   # EMA-fast above EMA-slow → uptrend

        # Update hysteresis streak
        if bullish:
            self._crossover_streak = max(0, self._crossover_streak) + 1
        else:
            self._crossover_streak = min(0, self._crossover_streak) - 1

        streak_up   = self._crossover_streak >= _CROSSOVER_CONFIRM
        streak_down = self._crossover_streak <= -_CROSSOVER_CONFIRM

        ema_gap_pct = abs(fast - slow) / (slow + 1e-6) * 100  # % gap between EMAs

        # ---- SCALE UP: uptrend confirmed + GPU has headroom ----
        if (
            streak_up
            and current_seeds < self.max_seeds
            and gpu_pct < _GPU_HIGH_PCT          # Tier 2: headroom gate
            and last.inference_tps > 10          # GPU is actually working
        ):
            new = min(self.max_seeds, current_seeds + 1)
            headroom_note = (
                f"GPU {gpu_pct:.0f}% (<{_GPU_HIGH_PCT:.0f}% threshold, headroom OK)"
                if gpu_pct < _GPU_LOW_PCT
                else f"GPU {gpu_pct:.0f}% (moderate, proceeding)"
            )
            return TunerDecision(
                changed=True, new_seeds=new, old_seeds=current_seeds,
                reason=(
                    f"🔼 EMA trend bullish {fast:.1f}>{slow:.1f} tok/s "
                    f"({ema_gap_pct:.1f}% gap, {self._crossover_streak} streak) | "
                    f"{headroom_note} — "
                    f"scaling {current_seeds}→{new} seeds"
                ),
                confidence=min(0.9, 0.5 + ema_gap_pct / 20),
            )

        # ---- SCALE UP VETOED by GPU saturation ----
        if streak_up and current_seeds < self.max_seeds and gpu_pct >= _GPU_HIGH_PCT:
            return TunerDecision(
                changed=False, new_seeds=current_seeds, old_seeds=current_seeds,
                reason=(
                    f"→ EMA uptrend ({fast:.1f}>{slow:.1f}) but GPU at {gpu_pct:.0f}% "
                    f"(≥{_GPU_HIGH_PCT:.0f}% threshold) — holding, no headroom"
                ),
            )

        # ---- SCALE DOWN: downtrend confirmed ----
        # Also require GPU to be above the low threshold — if GPU is underutilised,
        # a bearish EMA crossover means overhead (not contention). Hold.
        if streak_down and current_seeds > self.min_seeds:
            if gpu_pct < _GPU_LOW_PCT:
                return TunerDecision(
                    changed=False, new_seeds=current_seeds, old_seeds=current_seeds,
                    reason=(
                        f"→ EMA bearish ({fast:.1f}<{slow:.1f}) but GPU only {gpu_pct:.0f}% "
                        f"(< {_GPU_LOW_PCT:.0f}% threshold) — overhead not contention, holding"
                    ),
                )
            new = max(self.min_seeds, current_seeds - 1)
            return TunerDecision(
                changed=True, new_seeds=new, old_seeds=current_seeds,
                reason=(
                    f"🔽 EMA trend bearish {fast:.1f}<{slow:.1f} tok/s "
                    f"({ema_gap_pct:.1f}% gap, {abs(self._crossover_streak)} streak) | "
                    f"GPU {gpu_pct:.0f}% ≥ {_GPU_LOW_PCT:.0f}% (contention confirmed) — "
                    f"scaling {current_seeds}→{new} seeds"
                ),
                confidence=min(0.9, 0.5 + ema_gap_pct / 20),
            )

        # ---- HOLD: signals not confirmed yet ----
        status = (
            f"bullish streak {self._crossover_streak}/{_CROSSOVER_CONFIRM}"
            if bullish else
            f"bearish streak {abs(self._crossover_streak)}/{_CROSSOVER_CONFIRM}"
        )
        return TunerDecision(
            changed=False, new_seeds=current_seeds, old_seeds=current_seeds,
            reason=f"→ EMA {fast:.1f}/{'>' if bullish else '<'}{slow:.1f} — {status}, holding",
        )

    # ------------------------------------------------------------------
    # Internal: legacy marginal-efficiency evaluation (bootstrap only)
    # ------------------------------------------------------------------

    def _legacy_evaluate(
        self,
        current_seeds: int,
        now: float,
        gpu_pct: float,
    ) -> TunerDecision:
        """
        Original marginal-efficiency comparison — used as bootstrap while
        EMA hasn't seen enough samples yet.  Preserves full behaviour of
        the old _evaluate() method.
        """
        # Group history by seed count and compute mean tps per level
        seed_tps: dict[int, list[float]] = {}
        for s in self._history:
            seed_tps.setdefault(s.seeds, []).append(s.pipeline_tps)
        means: dict[int, float] = {k: sum(v)/len(v) for k, v in seed_tps.items()}

        last = self._history[-1]
        prev = self._history[-2]

        tps_now   = last.pipeline_tps
        tps_prev  = prev.pipeline_tps
        itps_now  = last.inference_tps
        itps_prev = prev.inference_tps

        samples_remaining = max(0, _EMA_SLOW - len(self._history))

        # --- Drop signal ---
        if tps_now < tps_prev * (1 - _TPS_DROP_THRESH) and current_seeds > self.min_seeds:
            itps_also_dropped = itps_now < itps_prev * (1 - _ITPS_DROP_THRESH)
            # KEY RULE: never scale down when GPU is underutilised.
            # Low GPU + low pipeline TPS = overhead noise (phase transitions,
            # health checks, init) NOT contention. Scaling down makes it worse.
            if itps_also_dropped and gpu_pct >= _GPU_LOW_PCT:
                new = max(self.min_seeds, current_seeds - 1)
                confidence = min(1.0, (tps_prev - tps_now) / (tps_prev + 1e-6))
                return TunerDecision(
                    changed=True, new_seeds=new, old_seeds=current_seeds,
                    reason=(
                        f"🔽 [bootstrap, {samples_remaining} to EMA] "
                        f"Throughput dropped {tps_prev:.1f}→{tps_now:.1f} tok/s "
                        f"+ inference {itps_prev:.0f}→{itps_now:.0f} tok/s "
                        f"(GPU {gpu_pct:.0f}% ≥ {_GPU_LOW_PCT:.0f}% — contention confirmed) — "
                        f"scaling {current_seeds}→{new} seeds"
                    ),
                    confidence=confidence,
                )
            elif itps_also_dropped and gpu_pct < _GPU_LOW_PCT:
                return TunerDecision(
                    changed=False, new_seeds=current_seeds, old_seeds=current_seeds,
                    reason=(
                        f"→ [bootstrap] Both TPS signals dropped but GPU only {gpu_pct:.0f}% "
                        f"(< {_GPU_LOW_PCT:.0f}% threshold) — overhead noise not contention, holding"
                    ),
                )
            else:
                return TunerDecision(
                    changed=False, new_seeds=current_seeds, old_seeds=current_seeds,
                    reason=(
                        f"→ [bootstrap] Pipeline dropped but inference stable "
                        f"({itps_now:.0f} tok/s) — overhead noise, holding"
                    ),
                )

        # --- Marginal efficiency ---
        fewer_seeds = current_seeds - 1
        if fewer_seeds in means:
            tps_at_fewer = means[fewer_seeds]
            delta_tps    = tps_now - tps_at_fewer
            marginal_eff = delta_tps / max(1, current_seeds - fewer_seeds)
            if marginal_eff < -_MIN_EFFICIENCY and current_seeds > self.min_seeds:
                new = max(self.min_seeds, current_seeds - 1)
                return TunerDecision(
                    changed=True, new_seeds=new, old_seeds=current_seeds,
                    reason=(
                        f"🔽 [bootstrap] Diminishing returns: "
                        f"marginal efficiency {marginal_eff:.3f} tok/s/seed — "
                        f"scaling {current_seeds}→{new} seeds"
                    ),
                    confidence=min(1.0, abs(marginal_eff) / _MIN_EFFICIENCY),
                )

        # --- Growth signal (also gated by GPU headroom in bootstrap) ---
        if (
            current_seeds < self.max_seeds
            and tps_now >= tps_prev * (1 - _MIN_EFFICIENCY / 2)
            and gpu_pct < _GPU_HIGH_PCT
            and last.inference_tps > 10
        ):
            new = min(self.max_seeds, current_seeds + 1)
            return TunerDecision(
                changed=True, new_seeds=new, old_seeds=current_seeds,
                reason=(
                    f"🔼 [bootstrap, {samples_remaining} to EMA] "
                    f"Throughput stable {tps_prev:.1f}→{tps_now:.1f} tok/s, "
                    f"GPU {gpu_pct:.0f}% — "
                    f"scaling {current_seeds}→{new} seeds"
                ),
                confidence=0.5,
            )

        return TunerDecision(
            changed=False, new_seeds=current_seeds, old_seeds=current_seeds,
            reason=(
                f"→ [bootstrap, {samples_remaining} samples to EMA-{_EMA_SLOW}] "
                f"holding at {current_seeds} seed(s)"
            ),
        )

    # ------------------------------------------------------------------
    # Internal: read throughput.json
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
        _max_stale = (30 * 2) if len(self._history) < 2 else (self.obs_window_s * 2)
        # At very early startup or during calibration, allow up to 10 minutes (600s) stale margin
        if ts - updated_at > max(_max_stale, 600.0):
            return None

        call_count = data.get("call_count", 0)
        cum_tok    = data.get("cumulative_tokens", 0)
        cum_wall   = data.get("cumulative_wall_s", 1) or 1
        cum_inf    = data.get("cumulative_inference_s", 1) or 1

        # Require minimum LLM call delta since last snapshot.
        # During calibration, we allow bootstrapping as soon as 1 call has completed.
        prev_calls = self._last_tp_snapshot.get("call_count", 0)
        _min_calls = 1 if len(self._history) < 2 else _MIN_CALLS_FOR_OBS
        if call_count - prev_calls < _min_calls:
            return None

        # Compute delta tps (marginal, not cumulative) for this window
        prev_tok  = self._last_tp_snapshot.get("cumulative_tokens", 0)
        prev_wall = self._last_tp_snapshot.get("cumulative_wall_s", 0)
        prev_inf  = self._last_tp_snapshot.get("cumulative_inference_s", 0)
        delta_tok  = cum_tok  - prev_tok
        delta_wall = cum_wall - prev_wall
        delta_inf  = cum_inf  - prev_inf

        if delta_wall <= 0 or delta_tok <= 0:
            # Fall back to cumulative
            pipeline_tps  = cum_tok / cum_wall
            inference_tps = cum_tok / cum_inf
            gpu_util_pct  = (cum_inf / cum_wall) * 100
        else:
            pipeline_tps  = delta_tok / delta_wall
            inference_tps = delta_tok / delta_inf if delta_inf > 0 else data.get("tps", pipeline_tps)
            gpu_util_pct  = (delta_inf / delta_wall) * 100 if delta_wall > 0 else 0

        self._last_tp_snapshot = dict(data)

        # GPU loaded: inferred from inference utilisation ratio
        gpu_loaded = gpu_util_pct > 10  # >10% of wall time is inference = model loaded

        return _Sample(
            ts=ts,
            seeds=seeds,
            pipeline_tps=pipeline_tps,
            inference_tps=inference_tps,
            call_count=call_count,
            gpu_loaded=gpu_loaded,
            gpu_util_pct=min(100.0, gpu_util_pct),
        )

    def reset(self) -> None:
        """Clear history (call when provider/model changes)."""
        self._history.clear()
        self._last_tp_snapshot.clear()
        self._last_sample_ts    = 0.0
        self._last_decision_ts  = 0.0
        self._ema_fast          = None
        self._ema_slow          = None
        self._crossover_streak  = 0


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
