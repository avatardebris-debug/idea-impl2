"""
goal_trace.v1 — structured goal reasoning traces for FT / always-on later.

Store: {PIPELINE_DIR}/goal_traces/{goal_id}.json and append-only jsonl.

KEEP_GOAL_TRACES (env):
  Default **true** when unset (1/true/yes/on or missing).
  Set to 0/false/no/off to skip writing new goal traces and history appends.
  In-memory trace dicts still update so callers can use goal_id/status.

Closed outcomes (Phase 3 learning hygiene)
------------------------------------------
  outcome ∈ {proven | failed | deeper | revoked | human_rejected}

Legacy ``status`` strings (goal_proven, goal_failed, deeper_work_needed, …)
are mapped into outcome; both fields are written for backward compatibility.

train_weight rules (defaults; callers may override):
  - High (≥3) only for trusted goal/field **proven** claims (dual-gated field_proven,
    process oracle, capability invoke success).
  - Low/zero for draft, deeper, failed, external-untrusted, baseline-only field,
    structural sandbox/promote, mcp_enqueued (not proven).
  - Never high-weight train on untrusted external "success".
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool
from pipeline.paths import get_pipeline_dir


SCHEMA = "goal_trace.v1"

# --- Closed outcome enum ---------------------------------------------------

OUTCOME_PROVEN = "proven"
OUTCOME_FAILED = "failed"
OUTCOME_DEEPER = "deeper"
OUTCOME_REVOKED = "revoked"
OUTCOME_HUMAN_REJECTED = "human_rejected"

CLOSED_OUTCOMES: frozenset[str] = frozenset(
    {
        OUTCOME_PROVEN,
        OUTCOME_FAILED,
        OUTCOME_DEEPER,
        OUTCOME_REVOKED,
        OUTCOME_HUMAN_REJECTED,
    }
)

# Legacy status → closed outcome (old traces still load / normalize)
LEGACY_STATUS_TO_OUTCOME: dict[str, str] = {
    "goal_proven": OUTCOME_PROVEN,
    "proven": OUTCOME_PROVEN,
    "field_proven": OUTCOME_PROVEN,  # dual-gated only when claim/trust say so
    "goal_failed": OUTCOME_FAILED,
    "failed": OUTCOME_FAILED,
    "ship_insufficient": OUTCOME_FAILED,
    "deeper_work_needed": OUTCOME_DEEPER,
    "deeper": OUTCOME_DEEPER,
    # Mechanical field pass alone is NOT high-weight proven
    "field_test_passed": OUTCOME_DEEPER,
    "revoked": OUTCOME_REVOKED,
    "human_rejected": OUTCOME_HUMAN_REJECTED,
}

# Closed outcome → durable legacy status (for callers that still read status)
OUTCOME_TO_LEGACY_STATUS: dict[str, str] = {
    OUTCOME_PROVEN: "goal_proven",
    OUTCOME_FAILED: "goal_failed",
    OUTCOME_DEEPER: "deeper_work_needed",
    OUTCOME_REVOKED: "revoked",
    OUTCOME_HUMAN_REJECTED: "human_rejected",
}

# Default train_weight by closed outcome (before trust/claim adjustments)
_DEFAULT_WEIGHT_BY_OUTCOME: dict[str, float] = {
    OUTCOME_PROVEN: 4.0,
    OUTCOME_FAILED: 0.1,
    OUTCOME_DEEPER: 0.0,
    OUTCOME_REVOKED: 0.5,
    OUTCOME_HUMAN_REJECTED: 0.0,
}

# Hard cap: never high-weight train on untrusted external (even explicit override)
EXTERNAL_MAX_TRAIN_WEIGHT = 0.2

# Common failure_class values (open vocabulary; these are recommended)
FAILURE_SECRET = "secret_fail"
FAILURE_SMOKE = "smoke_fail"
FAILURE_SANDBOX = "sandbox_fail"
FAILURE_INVOKE = "invoke_fail"
FAILURE_PATH = "path_fail"
FAILURE_COMPOSE = "compose_fail"
FAILURE_CAPABILITY = "capability_fail"
FAILURE_SHIP = "ship_insufficient"
FAILURE_POLICY_YIELD = "policy_yield"
FAILURE_EXTERNAL = "external_untrusted"
FAILURE_BASELINE = "baseline_only"
FAILURE_MCP_ENQUEUED = "mcp_enqueued"


def keep_goal_traces() -> bool:
    """Honor KEEP_GOAL_TRACES; default on when unset."""
    return env_bool("KEEP_GOAL_TRACES", default=True)


def goal_traces_dir(*, ensure: bool | None = None) -> Path:
    """Return goal_traces directory. Mkdir only when writing (KEEP_GOAL_TRACES on).

    *ensure*: if True, always mkdir; if False, never mkdir; if None (default),
    mkdir only when keep_goal_traces() is True.
    """
    d = get_pipeline_dir() / "goal_traces"
    do_mkdir = keep_goal_traces() if ensure is None else ensure
    if do_mkdir:
        d.mkdir(parents=True, exist_ok=True)
    return d


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_outcome(value: str | None) -> str | None:
    """Map a status or outcome string to a closed outcome, or None if unknown/non-terminal."""
    if value is None:
        return None
    key = str(value).strip().lower()
    if not key or key == "in_progress":
        return None
    if key in CLOSED_OUTCOMES:
        return key
    return LEGACY_STATUS_TO_OUTCOME.get(key)


def map_legacy_status(status: str | None) -> str | None:
    """Alias for normalize_outcome — map old status strings into closed outcomes."""
    return normalize_outcome(status)


def legacy_status_for_outcome(outcome: str) -> str:
    """Return the durable legacy status string for a closed outcome."""
    o = normalize_outcome(outcome) or OUTCOME_DEEPER
    return OUTCOME_TO_LEGACY_STATUS.get(o, "deeper_work_needed")


def default_train_weight(
    outcome: str | None,
    *,
    failure_class: str | None = None,
    trust: str | None = None,
    claim: str | None = None,
) -> float:
    """Compute default train_weight for an outcome + context.

    Rules:
      - High weight only for trusted proven-like claims (goal/field dual-gated).
      - External / untrusted proven → low (never high).
      - field baseline-only / field_test_passed → low (not proven high weight).
      - failed / deeper / human_rejected → low or zero.
      - revoked → modest positive (policy signal).
    """
    o = normalize_outcome(outcome)
    if o is None:
        return 0.0

    trust_l = (trust or "").strip().lower()
    claim_l = (claim or "").strip().lower()
    fc = (failure_class or "").strip().lower()

    # Explicit anti-patterns first
    if trust_l in ("external", "untrusted") or fc == FAILURE_EXTERNAL:
        # Never high-weight train on untrusted external success
        if o == OUTCOME_PROVEN:
            return EXTERNAL_MAX_TRAIN_WEIGHT
        return min(_DEFAULT_WEIGHT_BY_OUTCOME.get(o, 0.0), 0.1)

    if claim_l in ("field_baseline", "baseline", "field_test_passed") or fc == FAILURE_BASELINE:
        # Mechanical runner pass / B*-only plan — not dual-gated field_proven
        return 0.5 if o in (OUTCOME_PROVEN, OUTCOME_DEEPER) else _DEFAULT_WEIGHT_BY_OUTCOME.get(o, 0.0)

    if claim_l in ("structural", "sandbox", "block_promote", "mcp_smoke"):
        # Infra / structural proofs — keep moderate or zero
        if o == OUTCOME_PROVEN:
            if claim_l == "mcp_smoke":
                return 1.0
            return 0.0  # block sandbox/promote structural
        if o == OUTCOME_REVOKED:
            return 0.5
        return _DEFAULT_WEIGHT_BY_OUTCOME.get(o, 0.0)

    if claim_l in ("field_proven", "dual_gate"):
        # Dual-gated field_proven — high when outcome proven
        if o == OUTCOME_PROVEN:
            return 4.0
        if o == OUTCOME_FAILED:
            return 0.1
        return 0.0

    if claim_l in ("process_oracle", "goal", "capability_invoke"):
        if o == OUTCOME_PROVEN:
            return 4.0
        return _DEFAULT_WEIGHT_BY_OUTCOME.get(o, 0.0)

    if claim_l in ("connector_compose", "connector_execute"):
        if o == OUTCOME_PROVEN:
            return 3.0
        if o == OUTCOME_DEEPER:
            return 0.2
        return _DEFAULT_WEIGHT_BY_OUTCOME.get(o, 0.0)

    if claim_l in ("connector_structural",):
        if o == OUTCOME_PROVEN:
            return 2.0
        if o == OUTCOME_DEEPER:
            return 0.5
        return _DEFAULT_WEIGHT_BY_OUTCOME.get(o, 0.0)

    return float(_DEFAULT_WEIGHT_BY_OUTCOME.get(o, 0.0))


def is_external_untrusted(
    *,
    trust: str | None = None,
    failure_class: str | None = None,
) -> bool:
    """True when trust/failure_class mark this sample as untrusted external."""
    trust_l = (trust or "").strip().lower()
    fc = (failure_class or "").strip().lower()
    return trust_l in ("external", "untrusted") or fc == FAILURE_EXTERNAL


def clamp_train_weight(
    weight: float,
    *,
    trust: str | None = None,
    failure_class: str | None = None,
) -> float:
    """Clamp train_weight so external/untrusted never exceeds EXTERNAL_MAX_TRAIN_WEIGHT."""
    w = float(weight)
    if is_external_untrusted(trust=trust, failure_class=failure_class):
        return min(w, EXTERNAL_MAX_TRAIN_WEIGHT)
    return w


def set_outcome(
    trace: dict[str, Any],
    outcome: str,
    *,
    failure_class: str | None = None,
    train_weight: float | None = None,
    status: str | None = None,
    oracle: dict[str, Any] | None = None,
    trust: str | None = None,
    claim: str | None = None,
    save: bool = True,
) -> dict[str, Any]:
    """Set closed outcome (+ legacy status, failure_class, train_weight) on a trace.

    Does not set ended_at (use finalize_trace for terminal close). Safe to call
    mid-flight to stamp provisional outcome fields.
    """
    o = normalize_outcome(outcome)
    if o is None:
        raise ValueError(
            f"unknown outcome {outcome!r}; expected one of {sorted(CLOSED_OUTCOMES)}"
        )

    trace["outcome"] = o
    # Preserve explicit legacy status if provided and non-empty; else map from outcome
    if status is not None and str(status).strip():
        trace["status"] = str(status).strip()
    else:
        # If prior status was a known legacy form of this outcome, keep it; else map
        prior = str(trace.get("status") or "")
        if normalize_outcome(prior) == o and prior not in CLOSED_OUTCOMES:
            pass  # keep prior legacy spelling
        else:
            trace["status"] = legacy_status_for_outcome(o)

    if failure_class is not None:
        trace["failure_class"] = failure_class or None
    elif "failure_class" not in trace:
        trace["failure_class"] = None

    if oracle is not None:
        trace["oracle"] = oracle

    # Resolve trust/failure for weight + hard external clamp (override cannot bypass)
    t = trust if trust is not None else trace.get("trust")
    c = claim if claim is not None else trace.get("claim")
    fc = failure_class if failure_class is not None else trace.get("failure_class")

    if train_weight is not None:
        raw_w = float(train_weight)
    else:
        raw_w = default_train_weight(o, failure_class=fc, trust=t, claim=c)
    trace["train_weight"] = clamp_train_weight(raw_w, trust=t, failure_class=fc)

    if trust is not None:
        trace["trust"] = trust
    if claim is not None:
        trace["claim"] = claim

    if save:
        save_trace(trace)
    return trace


def start_trace(
    goal_text: str,
    *,
    goal_id: str | None = None,
    mode: str = "sandbox",
    budget: dict[str, Any] | None = None,
    plan: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    gid = goal_id or f"g_{uuid.uuid4().hex[:12]}"
    trace: dict[str, Any] = {
        "schema": SCHEMA,
        "goal_id": gid,
        "goal_text": goal_text,
        "mode": mode,
        "started_at": _iso(),
        "ended_at": None,
        "budget": budget or {"max_tokens": 500000, "max_minutes": 30},
        "plan": plan or [],
        "events": [],
        "oracle": None,
        "status": "in_progress",
        "outcome": None,
        "failure_class": None,
        "train_weight": 0.0,
    }
    save_trace(trace)
    return trace


def append_event(
    trace: dict[str, Any],
    *,
    type: str,
    content: str = "",
    tool: str | None = None,
    args: dict[str, Any] | None = None,
    result_snip: str = "",
    ok: bool | None = None,
) -> dict[str, Any]:
    ev: dict[str, Any] = {
        "t": _iso(),
        "type": type,
        "content": content[:4000],
    }
    if tool is not None:
        ev["tool"] = tool
    if args is not None:
        ev["args"] = args
    if result_snip:
        ev["result_snip"] = result_snip[:2000]
    if ok is not None:
        ev["ok"] = ok
    trace.setdefault("events", []).append(ev)
    save_trace(trace)
    return trace


def finalize_trace(
    trace: dict[str, Any],
    *,
    status: str | None = None,
    outcome: str | None = None,
    failure_class: str | None = None,
    oracle: dict[str, Any] | None = None,
    train_weight: float | None = None,
    trust: str | None = None,
    claim: str | None = None,
) -> dict[str, Any]:
    """Close a trace with status and/or closed outcome.

    Accepts legacy ``status`` (goal_proven | goal_failed | deeper_work_needed | …)
    and/or closed ``outcome`` (proven | failed | deeper | revoked | human_rejected).
    When only one is given, the other is derived. ``train_weight`` defaults from
    outcome + trust/claim when not overridden.
    """
    # Resolve closed outcome
    resolved: str | None = None
    if outcome is not None:
        resolved = normalize_outcome(outcome)
        if resolved is None:
            raise ValueError(
                f"unknown outcome {outcome!r}; expected one of {sorted(CLOSED_OUTCOMES)}"
            )
    elif status is not None:
        resolved = normalize_outcome(status)
        # Unknown custom status: keep as-is, outcome None unless we can guess
        if resolved is None and str(status).strip().lower() not in ("", "in_progress"):
            # Treat unrecognized terminal-ish status as deeper (safe low weight)
            resolved = OUTCOME_DEEPER

    if resolved is None:
        resolved = OUTCOME_DEEPER

    # Legacy status string to persist
    if status is not None and str(status).strip():
        legacy = str(status).strip()
    else:
        legacy = legacy_status_for_outcome(resolved)

    # Backward-compat train_weight defaults when claim/trust unset:
    # preserve historical behavior for the three classic statuses when no claim.
    if train_weight is None and claim is None and trust is None and failure_class is None:
        if legacy == "goal_proven" or resolved == OUTCOME_PROVEN:
            # Only use classic 4.0 when outcome is proven without special claim
            if resolved == OUTCOME_PROVEN:
                train_weight = 4.0
        elif legacy == "goal_failed" or resolved == OUTCOME_FAILED:
            train_weight = 0.1
        elif legacy == "deeper_work_needed" or resolved == OUTCOME_DEEPER:
            train_weight = 0.0
        # else: leave None → set_outcome computes

    # If caller passed only status=goal_proven with explicit train_weight historically,
    # we already honor train_weight override below.

    trace["ended_at"] = _iso()
    set_outcome(
        trace,
        resolved,
        failure_class=failure_class,
        train_weight=train_weight,
        status=legacy,
        oracle=oracle,
        trust=trust,
        claim=claim,
        save=False,
    )
    # If failure_class was not passed, ensure key exists (set_outcome may leave prior)
    if failure_class is None and "failure_class" not in trace:
        trace["failure_class"] = None

    save_trace(trace)
    append_jsonl(trace)
    return trace


def trace_path(goal_id: str) -> Path:
    """Path for a goal id; does not create the directory (read-friendly)."""
    return goal_traces_dir(ensure=False) / f"{goal_id}.json"


def save_trace(trace: dict[str, Any]) -> Path | None:
    """Persist per-goal JSON. No-op (returns None) when KEEP_GOAL_TRACES is off."""
    if not keep_goal_traces():
        return None
    gid = str(trace.get("goal_id") or "unknown")
    # ensure=True: we already know flag is on
    path = goal_traces_dir(ensure=True) / f"{gid}.json"
    path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return path


def load_trace(goal_id: str) -> dict[str, Any] | None:
    path = goal_traces_dir(ensure=False) / f"{goal_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def append_jsonl(trace: dict[str, Any]) -> Path | None:
    """Append to traces.jsonl. No-op when KEEP_GOAL_TRACES is off."""
    if not keep_goal_traces():
        return None
    path = goal_traces_dir(ensure=True) / "traces.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(trace, ensure_ascii=False) + "\n")
    return path


def sandbox_file_exists_goal(
    target_file: Path,
    *,
    goal_text: str | None = None,
) -> dict[str, Any]:
    """One-shot sandbox: prove a file exists (oracle)."""
    text = goal_text or f"Ensure file exists: {target_file}"
    tr = start_trace(text, mode="sandbox", plan=[{"step": 1, "intent": "check_file", "tool": "path.exists"}])
    append_event(tr, type="think", content=f"Check path {target_file}")
    exists = target_file.is_file()
    append_event(
        tr,
        type="tool",
        tool="path.exists",
        args={"path": str(target_file)},
        result_snip=str(exists),
        ok=exists,
    )
    if exists:
        return finalize_trace(
            tr,
            status="goal_proven",
            outcome=OUTCOME_PROVEN,
            oracle={"name": "file_exists", "pass": True, "evidence": str(target_file)},
            claim="goal",
        )
    return finalize_trace(
        tr,
        status="goal_failed",
        outcome=OUTCOME_FAILED,
        failure_class=FAILURE_PATH,
        oracle={"name": "file_exists", "pass": False, "evidence": str(target_file)},
        claim="goal",
    )
