"""
Algorithmic troubleshoot gate (v0) for thin-field / ship stall outcomes.

Classifies why ship failed and emits a closed-set recovery decision.
**No LLM in v0.** Emit decision artifacts only — does not spawn repair/replan agents.

Primary trigger: status/outcome ``ship_insufficient`` after thin field ship.
Also supports dry diagnosis for projects already in that (or related) status.

Artifacts:
  projects/{slug}/state/recovery_decision.json
  projects/{slug}/state/recovery_history.jsonl

Sticky state fields (on current_idea when thin ship completes):
  ship_outcome, ship_outcome_at

CLI:
  python -m pipeline.troubleshoot_gate --slug X
  python -m pipeline.troubleshoot_gate --project-dir /path/to/project
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "recovery_decision.v1"

# Closed recommended_action enum
ACTION_FIX_GATE_ONLY = "FIX_GATE_ONLY"
ACTION_FIELD_REPAIR_ONCE = "FIELD_REPAIR_ONCE"
ACTION_DEBUG_TARGETED = "DEBUG_TARGETED"
ACTION_REPLAN_PHASE = "REPLAN_PHASE"
ACTION_REPLAN_MASTER = "REPLAN_MASTER"
ACTION_THIN_FIELD_RETRY = "THIN_FIELD_RETRY"
ACTION_ASK_OPERATOR = "ASK_OPERATOR"
ACTION_PARK = "PARK"
ACTION_AMBIGUOUS = "AMBIGUOUS"

RECOMMENDED_ACTIONS = frozenset(
    {
        ACTION_FIX_GATE_ONLY,
        ACTION_FIELD_REPAIR_ONCE,
        ACTION_DEBUG_TARGETED,
        ACTION_REPLAN_PHASE,
        ACTION_REPLAN_MASTER,
        ACTION_THIN_FIELD_RETRY,
        ACTION_ASK_OPERATOR,
        ACTION_PARK,
        ACTION_AMBIGUOUS,
    }
)

# Primary classes
CLASS_PRODUCT_BUG = "product_bug"
CLASS_PLAN_MISMATCH = "plan_mismatch"
CLASS_PLAN_INSUFFICIENT = "plan_insufficient"
CLASS_GATE_FALSE_BLOCK = "gate_false_block"
CLASS_ENV_RUNTIME = "env_runtime"
CLASS_CREDENTIALS_HUMAN = "credentials_human"
CLASS_SCOPE_DRIFT = "scope_drift"
CLASS_SPIN_NO_PROGRESS = "spin_no_progress"
CLASS_UNKNOWN = "unknown"

PRIMARY_CLASSES = frozenset(
    {
        CLASS_PRODUCT_BUG,
        CLASS_PLAN_MISMATCH,
        CLASS_PLAN_INSUFFICIENT,
        CLASS_GATE_FALSE_BLOCK,
        CLASS_ENV_RUNTIME,
        CLASS_CREDENTIALS_HUMAN,
        CLASS_SCOPE_DRIFT,
        CLASS_SPIN_NO_PROGRESS,
        CLASS_UNKNOWN,
    }
)

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"

SHIP_OUTCOMES = frozenset(
    {"field_proven", "ship_insufficient", "deeper_work_needed"}
)

# Auth / credentials signals (priority 1).
# Intentionally narrow: bare "permission denied" / bare "401" are NOT auth
# (filesystem ACL / generic HTTP codes → env_runtime or other rules).
_AUTH_PATTERNS = re.compile(
    r"(?i)("
    r"\bunauthorized\b|"
    r"\bauthentication\s+failed\b|"
    r"\bauth(?:entication|orization)?\s+error\b|"
    r"\binvalid\s+(?:api\s+)?key\b|"
    r"\bapi[_\s-]?key\s+(?:missing|invalid|required)\b|"
    r"\boauth\b|"
    r"\bsmtp\s+auth\b|"
    r"\bSMTPAuthenticationError\b|"
    r"\blogin\s+failed\b|"
    r"\bcredentials?(?:\s+(?:missing|invalid|required|error))?\b|"
    r"\bnot\s+authenticated\b|"
    r"\bbearer\s+token\b|"
    r"\bpassword\s+(?:required|incorrect|invalid)\b|"
    r"\bWWW-Authenticate\b|"
    r"\btoken\s+(?:expired|invalid|revoked)\b|"
    r"\b401\s+Unauthorized\b|"
    r"\b403\s+Forbidden\b|"
    r"\bHTTP\s*(?:Error\s*)?401\b|"
    r"\bHTTP\s*(?:Error\s*)?403\b"
    r")"
)

# Filesystem / ACL noise — env, not credentials
_FS_PERMISSION_PATTERNS = re.compile(
    r"(?i)\b(permission\s+denied|access\s+denied|PermissionError)\b"
)

# Syntax / import / named-file product bugs (priority 3)
_SYNTAX_PATTERNS = re.compile(
    r"(?i)("
    r"SyntaxError|invalid\s+syntax|IndentationError|unexpected\s+indent|"
    r"TabError|unexpected\s+EOF"
    r")"
)
_IMPORT_PATTERNS = re.compile(
    r"(?i)("
    r"ImportError|ModuleNotFoundError|No\s+module\s+named|"
    r"cannot\s+import\s+name|ImportError:"
    r")"
)
_FILE_PATH_HINT = re.compile(
    r"(?i)(?:File\s+\")([^\"]+\.py)\"|"
    r"((?:[A-Za-z]:)?[\\/][^\s:]+\.py)|"
    r"((?:[\w.-]+[\\/])+[\w.-]+\.py)"
)

# Plan mismatch / wrong package CLI (priority 6)
_PLAN_MISMATCH_PATTERNS = re.compile(
    r"(?i)("
    r"No\s+module\s+named\s+['\"]?[\w.]+['\"]?|"
    r"not\s+recognized\s+as\s+(?:an\s+internal|a\s+command)|"
    r"command\s+not\s+found|"
    r"No\s+such\s+file\s+or\s+directory|"
    r"can't\s+open\s+file|"
    r"Usage:|"
    r"unrecognized\s+arguments|"
    r"no\s+command|"
    r"is\s+not\s+a\s+package"
    r")"
)

# Network / env runtime
_ENV_RUNTIME_PATTERNS = re.compile(
    r"(?i)\b("
    r"ConnectionError|ConnectionRefusedError|TimeoutError|timed?\s+out|"
    r"Temporary failure in name resolution|Name or service not known|"
    r"SSLError|Certificate|ECONNREFUSED|ENETUNREACH|"
    r"PermissionError|Read-only\s+file\s+system|"
    r"Address already in use"
    r")\b"
)

_PHASE_OPEN_IN_BLOCKED = re.compile(
    r"(?i)phase[_\s-]?(\d+)|Task\s+\d+|"
    r"open\s+task\s+checkbox"
)


@dataclass
class EvidenceBundle:
    """Collected signals for rule evaluation (not serialized wholesale)."""

    slug: str = ""
    status: str = ""
    phase: int = 0
    total_phases: int = 1
    complete_blocked_reason: str = ""
    field_results_text: str = ""
    field_passed: int = 0
    field_failed: int = 0
    review_pass: bool = False
    review_fail: bool = False
    current_phase_open: int = 0
    current_phase_done: int = 0
    current_phase_total: int = 0
    earlier_open: int = 0
    later_open: int = 0
    later_phases_with_open: int = 0
    total_open: int = 0
    total_done: int = 0
    prior_history_count: int = 0
    prior_same_fingerprint: int = 0
    field_ship_reason: str = ""
    fail_snippets: list[str] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path, limit: int = 200_000) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _load_state(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "state" / "current_idea.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_state_fields(project_dir: Path, updates: dict[str, Any]) -> dict[str, Any]:
    """Merge updates into current_idea.json; return full state."""
    state = _load_state(project_dir)
    state.update(updates)
    path = project_dir / "state" / "current_idea.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def set_ship_outcome(
    project_dir: Path,
    outcome: str,
    *,
    state: dict[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Sticky ship_outcome + ship_outcome_at on current_idea.

    If write=False and state is provided, mutates state in place only.
    """
    outcome = (outcome or "").strip()
    if outcome not in SHIP_OUTCOMES:
        return state or _load_state(project_dir)
    ts = _utc_now()
    if state is not None:
        state["ship_outcome"] = outcome
        state["ship_outcome_at"] = ts
        if write:
            path = project_dir / "state" / "current_idea.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state
    return _write_state_fields(
        project_dir, {"ship_outcome": outcome, "ship_outcome_at": ts}
    )


def _review_pass_for_phase(project_dir: Path, phase: int, state: dict[str, Any]) -> tuple[bool, bool]:
    """Return (review_pass, review_fail) from state and/or review.md."""
    rr = state.get("review_result")
    if isinstance(rr, dict):
        if rr.get("review_fail") is True:
            return False, True
        if rr.get("review_fail") is False and not rr.get("blocking_bugs"):
            return True, False
        if rr.get("verdict", "").upper() == "PASS":
            return True, False

    review_path = project_dir / "phases" / f"phase_{phase}" / "review.md"
    text = _read_text(review_path, limit=8000)
    if not text:
        # Fall back to last phase review if current missing
        total = int(state.get("total_phases") or phase or 1)
        review_path = project_dir / "phases" / f"phase_{total}" / "review.md"
        text = _read_text(review_path, limit=8000)
    if not text:
        return False, False
    low = text.lower()
    if "verdict: fail" in low or re.search(r"(?m)^FAIL\b", text):
        return False, True
    if "verdict: pass" in low or re.search(r"(?m)^PASS\b", text):
        return True, False
    return False, False


def _phase_checkbox_map(project_dir: Path) -> dict[int, tuple[int, int, int]]:
    """Map phase_num → (open, done, total)."""
    from pipeline.task_checkboxes import stats_for_phase

    out: dict[int, tuple[int, int, int]] = {}
    phases_root = project_dir / "phases"
    if not phases_root.is_dir():
        return out
    for d in phases_root.glob("phase_*"):
        if not d.is_dir() or "_overflow" in d.name:
            continue
        m = re.match(r"phase_(\d+)$", d.name)
        if not m:
            continue
        pnum = int(m.group(1))
        st = stats_for_phase(project_dir, pnum)
        out[pnum] = (st.open_count, st.done_count, st.total)
    return out


def _parse_field_counts(text: str) -> tuple[int, int]:
    passed = failed = 0
    m = re.search(r"(?i)-\s*Passed:\s*(\d+)", text)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(?i)-\s*Failed:\s*(\d+)", text)
    if m:
        failed = int(m.group(1))
    return passed, failed


def _fail_snippets(text: str, limit: int = 8) -> list[str]:
    snippets: list[str] = []
    for m in re.finditer(
        r"(?im)^##\s+([^\n]*FAIL[^\n]*)\n(.*?)(?=^##\s|\Z)",
        text,
        re.DOTALL,
    ):
        head = m.group(1).strip()[:120]
        body = " ".join(m.group(2).split())[:200]
        snippets.append(f"{head}: {body}" if body else head)
        if len(snippets) >= limit:
            break
    if not snippets and "fail" in text.lower():
        snippets.append(text[-400:].replace("\n", " ")[:300])
    return snippets


def _history_path(project_dir: Path) -> Path:
    return project_dir / "state" / "recovery_history.jsonl"


def _decision_path(project_dir: Path) -> Path:
    return project_dir / "state" / "recovery_decision.json"


def _count_history(project_dir: Path) -> tuple[int, list[dict[str, Any]]]:
    path = _history_path(project_dir)
    if not path.is_file():
        return 0, []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return 0, []
    return len(rows), rows


def collect_evidence(
    project_dir: Path,
    *,
    state: dict[str, Any] | None = None,
    status_override: str | None = None,
    field_results_text: str | None = None,
) -> EvidenceBundle:
    """Gather rule inputs from project tree + optional in-memory overrides."""
    project_dir = Path(project_dir)
    st = dict(state or _load_state(project_dir))
    slug = (
        st.get("_slug")
        or st.get("slug")
        or project_dir.name
    )
    phase = int(st.get("phase") or 0)
    total = int(st.get("total_phases") or 1) or 1
    status = (status_override or st.get("status") or "").strip()

    # When caller passes explicit field_results_text (e.g. post-repair md),
    # do not let stale on-disk JSON override those counts.
    explicit_field_text = field_results_text is not None
    field_text = field_results_text
    if field_text is None:
        field_text = _read_text(project_dir / "phases" / "ship" / "field_test_results.md")
        # Also fold evaluation / repair log tails for auth signals
        extra_bits = []
        for rel in (
            "phases/ship/field_evaluation.md",
            "phases/ship/field_repair_log.md",
            "phases/ship/debug_report.md",
        ):
            t = _read_text(project_dir / rel, limit=20_000)
            if t:
                extra_bits.append(t)
        if extra_bits:
            field_text = (field_text or "") + "\n" + "\n".join(extra_bits)

    field_text = field_text or ""
    passed, failed = _parse_field_counts(field_text)
    # Prefer structured json only when not using explicit in-memory results text.
    # Use None-aware checks so JSON 0 is not treated as missing.
    if not explicit_field_text:
        json_path = project_dir / "phases" / "ship" / "field_test_results.json"
        if json_path.is_file():
            try:
                j = json.loads(json_path.read_text(encoding="utf-8"))
                if isinstance(j, dict):
                    if "passed" in j and j["passed"] is not None:
                        passed = int(j["passed"])
                    if "failed" in j and j["failed"] is not None:
                        failed = int(j["failed"])
            except Exception:
                pass

    review_pass, review_fail = _review_pass_for_phase(project_dir, phase or total, st)
    cmap = _phase_checkbox_map(project_dir)
    cur_phase = phase or total
    cur = cmap.get(cur_phase, (0, 0, 0))
    earlier_open = sum(v[0] for p, v in cmap.items() if p < cur_phase)
    later_open = sum(v[0] for p, v in cmap.items() if p > cur_phase)
    later_phases_with_open = sum(1 for p, v in cmap.items() if p > cur_phase and v[0] > 0)
    total_open = sum(v[0] for v in cmap.values())
    total_done = sum(v[1] for v in cmap.values())

    # State-level task counts as fallback for current phase
    if cur[2] == 0 and (st.get("tasks_total") or 0):
        td = int(st.get("tasks_done") or 0)
        tt = int(st.get("tasks_total") or 0)
        cur = (max(0, tt - td), td, tt)

    hist_n, hist_rows = _count_history(project_dir)

    return EvidenceBundle(
        slug=str(slug),
        status=status,
        phase=phase,
        total_phases=total,
        complete_blocked_reason=str(st.get("complete_blocked_reason") or ""),
        field_results_text=field_text,
        field_passed=passed,
        field_failed=failed,
        review_pass=review_pass,
        review_fail=review_fail,
        current_phase_open=cur[0],
        current_phase_done=cur[1],
        current_phase_total=cur[2],
        earlier_open=earlier_open,
        later_open=later_open,
        later_phases_with_open=later_phases_with_open,
        total_open=total_open,
        total_done=total_done,
        prior_history_count=hist_n,
        field_ship_reason=str(
            st.get("field_ship_reason") or st.get("ship_insufficient_reason") or ""
        ),
        fail_snippets=_fail_snippets(field_text),
        state=st,
    )


def extract_fail_tags(text: str) -> list[str]:
    """Stable closed-ish fail tag set from field/stderr text."""
    tags: list[str] = []
    low = text or ""
    if _AUTH_PATTERNS.search(low):
        tags.append("auth")
        tags.append("credentials")
    if _SYNTAX_PATTERNS.search(low):
        tags.append("syntax")
    if _IMPORT_PATTERNS.search(low):
        tags.append("import")
    if _ENV_RUNTIME_PATTERNS.search(low) or _FS_PERMISSION_PATTERNS.search(low):
        tags.append("env_runtime")
    if re.search(r"(?i)\bpytest\b", low) and re.search(r"(?i)fail", low):
        tags.append("pytest")
    if re.search(r"(?i)TypeError|AttributeError|NameError|ValueError|KeyError", low):
        tags.append("runtime_error")
    if _PLAN_MISMATCH_PATTERNS.search(low) and "import" not in tags:
        # plan mismatch language without pure import classification still tags
        if re.search(
            r"(?i)not recognized|command not found|No such file|unrecognized arguments",
            low,
        ):
            tags.append("plan_mismatch")
    if re.search(r"(?i)No module named", low):
        tags.append("no_module")
    if re.search(r"(?i)timeout|timed?\s+out", low):
        tags.append("timeout")
    # Dedup preserve order
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def signal_blob(ev: EvidenceBundle) -> str:
    """Unified evidence blob for tags + fingerprint (annotate and classify share this)."""
    return "\n".join(
        [
            ev.field_results_text or "",
            ev.complete_blocked_reason or "",
            ev.field_ship_reason or "",
            "\n".join(ev.fail_snippets or []),
        ]
    )


def tags_and_fingerprint(ev: EvidenceBundle) -> tuple[list[str], str, str]:
    """Return (fail_tags, fail_fingerprint, signal_blob) from one source of truth."""
    blob = signal_blob(ev)
    tags = extract_fail_tags(blob)
    fp = fail_fingerprint(tags, ev.fail_snippets, status=ev.status)
    return tags, fp, blob


def _should_park_spin(ev: EvidenceBundle) -> bool:
    """True when repeated same fingerprint or attempt budget exhausted."""
    return ev.prior_same_fingerprint >= 2 or ev.prior_history_count >= 5


def fail_fingerprint(tags: list[str], snippets: list[str], *, status: str = "") -> str:
    """Stable short hash of fail signatures."""
    # Normalize snippets: drop absolute paths / numbers that churn
    norm_snips = []
    for s in snippets[:6]:
        s2 = re.sub(r"[A-Za-z]:\\[^\s]+", "<path>", s)
        s2 = re.sub(r"/[^\s]+\.py", "<py>", s2)
        s2 = re.sub(r"\d+", "N", s2)
        norm_snips.append(s2[:80])
    payload = "|".join(sorted(tags)) + "||" + "||".join(norm_snips) + f"||{status}"
    return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()[:16]


def _action_cost_minutes(action: str) -> int:
    return {
        ACTION_FIX_GATE_ONLY: 10,
        ACTION_FIELD_REPAIR_ONCE: 20,
        ACTION_DEBUG_TARGETED: 30,
        ACTION_REPLAN_PHASE: 40,
        ACTION_REPLAN_MASTER: 60,
        ACTION_THIN_FIELD_RETRY: 15,
        ACTION_ASK_OPERATOR: 5,
        ACTION_PARK: 0,
        ACTION_AMBIGUOUS: 15,
    }.get(action, 30)


def _next_policy(action: str) -> str:
    return {
        ACTION_FIX_GATE_ONLY: "remain_queue",
        ACTION_FIELD_REPAIR_ONCE: "remain_queue",
        ACTION_DEBUG_TARGETED: "remain_queue",
        ACTION_REPLAN_PHASE: "remain_queue",
        ACTION_REPLAN_MASTER: "remain_queue",
        ACTION_THIN_FIELD_RETRY: "remain_queue",
        ACTION_ASK_OPERATOR: "ask_again",
        ACTION_PARK: "cooldown",
        ACTION_AMBIGUOUS: "remain_queue",
    }.get(action, "remain_queue")


def _prompt_inject(
    action: str,
    primary: str,
    evidence: list[str],
    tags: list[str],
) -> str:
    bits = "; ".join(evidence[:4]) if evidence else primary
    tag_s = ",".join(tags[:6]) if tags else "none"
    templates = {
        ACTION_FIX_GATE_ONLY: (
            "Complete is blocked by stale pre-current-phase checkboxes while last "
            f"phase/review look OK. Close or waive older open tasks. Evidence: {bits}"
        ),
        ACTION_FIELD_REPAIR_ONCE: (
            f"Field plan/cmd mismatch likely. Repair plan or one small product fix, "
            f"then re-field. tags={tag_s}. {bits}"
        ),
        ACTION_DEBUG_TARGETED: (
            f"Targeted debug: syntax/import/runtime in product code. tags={tag_s}. {bits}"
        ),
        ACTION_REPLAN_PHASE: (
            f"Current phase tasks incoherent or 0 done at high phase. Replan this phase. {bits}"
        ),
        ACTION_REPLAN_MASTER: (
            f"Multi-phase drift / empty late phases / plan insufficient. Replan master. {bits}"
        ),
        ACTION_THIN_FIELD_RETRY: (
            f"Cheap fix applied path — retry thin field ship. {bits}"
        ),
        ACTION_ASK_OPERATOR: (
            f"Auth/network/credentials need human. tags={tag_s}. {bits}"
        ),
        ACTION_PARK: (
            f"No progress / unknown after prior attempts. Park. {bits}"
        ),
        ACTION_AMBIGUOUS: (
            f"Low-confidence classification (v0 best-effort). tags={tag_s}. {bits}"
        ),
    }
    return templates.get(action, bits)[:500]


def classify_recovery(ev: EvidenceBundle) -> dict[str, Any]:
    """
    Rule priority (v0, no LLM) — evaluation order:

      1. Auth/credential keywords → ASK_OPERATOR / credentials_human
      2. Syntax/Import/named file errors → DEBUG_TARGETED / product_bug
         (beats gate_false_block when both present — video_management dual-signal)
      3. complete_blocked older-phase opens + phase>=total + review OK
         → FIX_GATE_ONLY / gate_false_block
      4. Current phase 0/N done with phase high → REPLAN_PHASE or REPLAN_MASTER
      5. Many open later phases + little done → REPLAN_MASTER / scope_drift
      6. Field fails look like wrong package/CLI → FIELD_REPAIR_ONCE / plan_mismatch
      7. Default → AMBIGUOUS (best-effort)

    Post-classify override:
      Spin / PARK when prior_same_fingerprint >= 2 or prior_history_count >= 5,
      regardless of which rule would have fired (repeated identical failures).
    """
    tags, fp, blob = tags_and_fingerprint(ev)
    decision = _classify_recovery_core(ev, tags=tags, fp=fp, blob=blob)
    if (
        _should_park_spin(ev)
        and decision.get("recommended_action") != ACTION_PARK
    ):
        would_action = decision.get("recommended_action") or ACTION_AMBIGUOUS
        would_primary = decision.get("primary_class") or CLASS_UNKNOWN
        secondary = [would_primary]
        for sc in decision.get("secondary_classes") or []:
            if sc not in secondary:
                secondary.append(sc)
        evidence = [
            f"prior recovery attempts: {ev.prior_history_count}",
            f"same fail fingerprint count: {ev.prior_same_fingerprint}",
            f"would have recommended {would_action} ({would_primary})",
        ]
        evidence.extend((decision.get("evidence") or [])[:4])
        return _decision_body(
            ev,
            primary=CLASS_SPIN_NO_PROGRESS,
            secondary=secondary,
            action=ACTION_PARK,
            confidence=CONFIDENCE_MEDIUM,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )
    return decision


def _classify_recovery_core(
    ev: EvidenceBundle,
    *,
    tags: list[str],
    fp: str,
    blob: str,
) -> dict[str, Any]:
    """Core rules without spin override (see classify_recovery)."""
    evidence: list[str] = []
    secondary: list[str] = []

    phase_done = ev.phase >= ev.total_phases and ev.total_phases > 0
    has_syntax = "syntax" in tags
    has_import = "import" in tags or "no_module" in tags
    has_auth = "auth" in tags or "credentials" in tags
    has_env = "env_runtime" in tags or "timeout" in tags
    named_file_err = bool(_FILE_PATH_HINT.search(blob)) and (
        has_syntax or has_import or "runtime_error" in tags
    )

    # --- Rule 1: credentials / auth ---
    if has_auth:
        evidence.append("auth/credential keywords in field stderr or logs")
        if ev.fail_snippets:
            evidence.append(ev.fail_snippets[0][:160])
        return _decision_body(
            ev,
            primary=CLASS_CREDENTIALS_HUMAN,
            secondary=secondary,
            action=ACTION_ASK_OPERATOR,
            confidence=CONFIDENCE_HIGH,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    # --- Rule 2: syntax/import take priority over FIX_GATE ---
    # (video_management-like: both stale gate + syntax → DEBUG_TARGETED)
    if has_syntax or (has_import and named_file_err) or (
        has_import and "runtime_error" in tags
    ) or (not has_syntax and named_file_err and "runtime_error" in tags):
        if has_syntax:
            evidence.append("SyntaxError / invalid syntax in field results")
        if has_import:
            evidence.append("ImportError / ModuleNotFoundError in field results")
        if named_file_err:
            evidence.append("named file path in traceback")
        if ev.complete_blocked_reason and phase_done and ev.earlier_open > 0:
            secondary.append(CLASS_GATE_FALSE_BLOCK)
            evidence.append(
                f"also complete_blocked with earlier-phase opens ({ev.earlier_open})"
            )
        return _decision_body(
            ev,
            primary=CLASS_PRODUCT_BUG,
            secondary=secondary,
            action=ACTION_DEBUG_TARGETED,
            confidence=CONFIDENCE_HIGH if (has_syntax or named_file_err) else CONFIDENCE_MEDIUM,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    # Broader import/runtime product bugs without plan-mismatch-only
    if has_import and "plan_mismatch" not in tags and ev.field_failed > 0:
        evidence.append("import failures in field suite")
        if ev.fail_snippets:
            evidence.append(ev.fail_snippets[0][:160])
        return _decision_body(
            ev,
            primary=CLASS_PRODUCT_BUG,
            secondary=secondary,
            action=ACTION_DEBUG_TARGETED,
            confidence=CONFIDENCE_MEDIUM,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    if "runtime_error" in tags and ev.field_failed > 0:
        evidence.append("TypeError/AttributeError/NameError style product errors")
        return _decision_body(
            ev,
            primary=CLASS_PRODUCT_BUG,
            secondary=secondary,
            action=ACTION_DEBUG_TARGETED,
            confidence=CONFIDENCE_MEDIUM,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    # --- Rule 3: gate false block ---
    # Prefer review_pass for high confidence. When review is missing (both flags
    # false), only FIX_GATE at medium if blocked reason explicitly cites open
    # checkboxes — may misfire if review simply was not written yet.
    blocked = (ev.complete_blocked_reason or "").strip()
    if blocked and phase_done and ev.earlier_open > 0:
        current_ok = ev.current_phase_open == 0 or (
            ev.current_phase_total > 0 and ev.current_phase_done == ev.current_phase_total
        )
        if current_ok and not ev.review_fail:
            cites_open = bool(_PHASE_OPEN_IN_BLOCKED.search(blocked))
            if ev.review_pass or cites_open:
                evidence.append(
                    f"complete_blocked_reason cites open tasks; earlier_open={ev.earlier_open}"
                )
                evidence.append(
                    f"phase={ev.phase}/{ev.total_phases} current_phase closed; "
                    f"review_pass={ev.review_pass}"
                )
                conf = CONFIDENCE_HIGH if ev.review_pass else CONFIDENCE_MEDIUM
                if not ev.review_pass:
                    evidence.append(
                        "review missing or not PASS — medium confidence FIX_GATE "
                        "(blocked reason cites open checkboxes)"
                    )
                return _decision_body(
                    ev,
                    primary=CLASS_GATE_FALSE_BLOCK,
                    secondary=secondary,
                    action=ACTION_FIX_GATE_ONLY,
                    confidence=conf,
                    evidence=evidence,
                    tags=tags,
                    fingerprint=fp,
                )

    # Also: blocked message without earlier_open map, but review PASS + phase done
    if blocked and phase_done and ev.review_pass and _PHASE_OPEN_IN_BLOCKED.search(blocked):
        if ev.current_phase_open == 0:
            evidence.append(
                f"complete_blocked + review PASS at phase {ev.phase}/{ev.total_phases}"
            )
            evidence.append(blocked[:160])
            return _decision_body(
                ev,
                primary=CLASS_GATE_FALSE_BLOCK,
                secondary=secondary,
                action=ACTION_FIX_GATE_ONLY,
                confidence=CONFIDENCE_MEDIUM,
                evidence=evidence,
                tags=tags,
                fingerprint=fp,
            )

    # --- Rule 4: current phase 0 done at high phase ---
    high_phase = ev.phase >= max(2, int(0.5 * ev.total_phases))
    cur_all_open = (
        ev.current_phase_total > 0
        and ev.current_phase_done == 0
        and ev.current_phase_open == ev.current_phase_total
    )
    if cur_all_open and high_phase:
        evidence.append(
            f"current phase {ev.phase}: {ev.current_phase_done}/{ev.current_phase_total} tasks done"
        )
        if ev.later_phases_with_open >= 2 or ev.later_open >= 5:
            secondary.append(CLASS_SCOPE_DRIFT)
            evidence.append(
                f"later phases open: phases_with_open={ev.later_phases_with_open} open={ev.later_open}"
            )
            return _decision_body(
                ev,
                primary=CLASS_PLAN_INSUFFICIENT,
                secondary=secondary,
                action=ACTION_REPLAN_MASTER,
                confidence=CONFIDENCE_HIGH,
                evidence=evidence,
                tags=tags,
                fingerprint=fp,
            )
        return _decision_body(
            ev,
            primary=CLASS_PLAN_INSUFFICIENT,
            secondary=secondary,
            action=ACTION_REPLAN_PHASE,
            confidence=CONFIDENCE_HIGH if ev.phase >= ev.total_phases else CONFIDENCE_MEDIUM,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    # --- Rule 5: multi-phase drift / empty late phases ---
    if (
        ev.later_phases_with_open >= 3
        or (ev.later_open >= 8 and ev.total_done < max(3, ev.later_open // 2))
        or (
            phase_done
            and ev.total_open >= 8
            and ev.current_phase_done == 0
            and ev.current_phase_total > 0
        )
    ):
        evidence.append(
            f"scope drift signals: later_open={ev.later_open} "
            f"later_phases_with_open={ev.later_phases_with_open} "
            f"total_done={ev.total_done} total_open={ev.total_open}"
        )
        return _decision_body(
            ev,
            primary=CLASS_SCOPE_DRIFT,
            secondary=[CLASS_PLAN_INSUFFICIENT],
            action=ACTION_REPLAN_MASTER,
            confidence=CONFIDENCE_MEDIUM,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    # --- Env runtime (non-auth) ---
    if has_env and not has_auth:
        evidence.append("environment/runtime/network signals in field output")
        return _decision_body(
            ev,
            primary=CLASS_ENV_RUNTIME,
            secondary=secondary,
            action=ACTION_ASK_OPERATOR if "timeout" in tags else ACTION_AMBIGUOUS,
            confidence=CONFIDENCE_MEDIUM,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    # --- Rule 6: plan mismatch / wrong CLI package ---
    plan_mismatch = (
        "plan_mismatch" in tags
        or "no_module" in tags
        or (
            ev.field_failed > 0
            and re.search(
                r"(?i)not recognized|command not found|No such file or directory|"
                r"unrecognized arguments|is not a package|can't open file",
                blob,
            )
        )
    )
    if plan_mismatch and not has_syntax:
        evidence.append("field fails look like wrong package/CLI or plan cmd mismatch")
        if ev.fail_snippets:
            evidence.append(ev.fail_snippets[0][:160])
        conf = CONFIDENCE_MEDIUM
        return _decision_body(
            ev,
            primary=CLASS_PLAN_MISMATCH,
            secondary=secondary,
            action=ACTION_FIELD_REPAIR_ONCE,
            confidence=conf,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    # Partial field pass after cheap signal → maybe retry
    if ev.field_failed == 0 and ev.field_passed > 0 and ev.status == "ship_insufficient":
        evidence.append("field suite green but status ship_insufficient (stale?)")
        return _decision_body(
            ev,
            primary=CLASS_UNKNOWN,
            secondary=secondary,
            action=ACTION_THIN_FIELD_RETRY,
            confidence=CONFIDENCE_LOW,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    # Plan failed path
    if "plan failed" in (ev.field_ship_reason or "").lower():
        evidence.append(ev.field_ship_reason[:160])
        return _decision_body(
            ev,
            primary=CLASS_PLAN_MISMATCH,
            secondary=secondary,
            action=ACTION_FIELD_REPAIR_ONCE,
            confidence=CONFIDENCE_MEDIUM,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    # --- Rule 7: default ---
    if ev.field_failed > 0:
        evidence.append(
            f"field FAIL passed={ev.field_passed} failed={ev.field_failed}; no high-confidence rule"
        )
        if ev.fail_snippets:
            evidence.append(ev.fail_snippets[0][:160])
        return _decision_body(
            ev,
            primary=CLASS_UNKNOWN,
            secondary=secondary,
            action=ACTION_AMBIGUOUS,
            confidence=CONFIDENCE_LOW,
            evidence=evidence,
            tags=tags,
            fingerprint=fp,
        )

    evidence.append(
        f"status={ev.status} phase={ev.phase}/{ev.total_phases}; insufficient signals"
    )
    return _decision_body(
        ev,
        primary=CLASS_UNKNOWN,
        secondary=secondary,
        action=ACTION_AMBIGUOUS if ev.prior_history_count < 2 else ACTION_PARK,
        confidence=CONFIDENCE_LOW,
        evidence=evidence,
        tags=tags,
        fingerprint=fp,
    )


def _decision_body(
    ev: EvidenceBundle,
    *,
    primary: str,
    secondary: list[str],
    action: str,
    confidence: str,
    evidence: list[str],
    tags: list[str],
    fingerprint: str,
) -> dict[str, Any]:
    status = ev.status or "ship_insufficient"
    return {
        "schema": SCHEMA,
        "slug": ev.slug,
        "ts": _utc_now(),
        "status": status,
        "primary_class": primary,
        "secondary_classes": list(secondary),
        "recommended_action": action,
        "confidence": confidence,
        "evidence": evidence[:12],
        "fail_tags": tags,
        "fail_fingerprint": fingerprint,
        "prompt_inject": _prompt_inject(action, primary, evidence, tags),
        "max_cost_minutes": _action_cost_minutes(action),
        "next_policy": _next_policy(action),
        # Diagnostic extras (still schema-compatible; consumers may ignore)
        "phase": ev.phase,
        "total_phases": ev.total_phases,
        "field_passed": ev.field_passed,
        "field_failed": ev.field_failed,
    }


def write_recovery_artifacts(
    project_dir: Path,
    decision: dict[str, Any],
) -> tuple[Path, Path]:
    """Write recovery_decision.json and append recovery_history.jsonl."""
    project_dir = Path(project_dir)
    state_dir = project_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    dec_path = _decision_path(project_dir)
    dec_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")

    hist_path = _history_path(project_dir)
    line = json.dumps(decision, ensure_ascii=False)
    with hist_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return dec_path, hist_path


def _annotate_prior_fingerprint(ev: EvidenceBundle, project_dir: Path) -> None:
    """Fill prior_same_fingerprint from history for spin detection.

    Uses the same blob/tags/fingerprint source as classify_recovery.
    """
    n, rows = _count_history(project_dir)
    ev.prior_history_count = n
    if not rows:
        return
    _tags, fp, _blob = tags_and_fingerprint(ev)
    same = sum(1 for r in rows if r.get("fail_fingerprint") == fp)
    ev.prior_same_fingerprint = same


def run_troubleshoot_gate(
    project_dir: Path,
    *,
    state: dict[str, Any] | None = None,
    status: str | None = None,
    field_results_text: str | None = None,
    write: bool = True,
    set_outcome: bool = True,
) -> dict[str, Any]:
    """
    Classify ship stall and optionally write recovery artifacts.

    Parameters
    ----------
    project_dir : project root
    state : optional in-memory current_idea (avoids re-read)
    status : override status string (e.g. ship_insufficient)
    field_results_text : optional field results md (use just-written content)
    write : persist recovery_decision.json + history
    set_outcome : set sticky ship_outcome on current_idea when status is a ship outcome
    """
    project_dir = Path(project_dir)
    st = dict(state or _load_state(project_dir))
    status_eff = (status or st.get("status") or "ship_insufficient").strip()

    ev = collect_evidence(
        project_dir,
        state=st,
        status_override=status_eff,
        field_results_text=field_results_text,
    )
    _annotate_prior_fingerprint(ev, project_dir)
    decision = classify_recovery(ev)

    if write:
        write_recovery_artifacts(project_dir, decision)
        if set_outcome and status_eff in SHIP_OUTCOMES:
            # Mutate provided state if any; always persist sticky fields
            set_ship_outcome(project_dir, status_eff, state=st if state is not None else None, write=True)
            if state is not None:
                state["ship_outcome"] = status_eff
                state["ship_outcome_at"] = st.get("ship_outcome_at") or decision.get("ts")

    return decision


def diagnose_project(
    project_dir: Path,
    *,
    write: bool = True,
) -> dict[str, Any]:
    """Dry diagnosis entry for projects already in ship_insufficient / related."""
    return run_troubleshoot_gate(project_dir, write=write, set_outcome=True)


def write_field_test_results_json(
    project_dir: Path,
    run: Any,
    *,
    plan_engine: str = "",
    extra: dict[str, Any] | None = None,
) -> Path:
    """Structured field results for later gates (instrumentation)."""
    project_dir = Path(project_dir)
    ship = project_dir / "phases" / "ship"
    ship.mkdir(parents=True, exist_ok=True)
    path = ship / "field_test_results.json"

    results = []
    if hasattr(run, "results"):
        for row in run.results or []:
            if not isinstance(row, dict):
                continue
            results.append(
                {
                    "task_id": row.get("task_id"),
                    "title": row.get("title"),
                    "kind": row.get("kind"),
                    "passed": bool(row.get("passed")),
                    "returncode": row.get("returncode"),
                    "command": row.get("command"),
                    "detail": (row.get("detail") or "")[:500],
                    # Truncate output for artifact size
                    "output_tail": (row.get("output_tail") or "")[-1500:],
                }
            )
    payload: dict[str, Any] = {
        "schema": "field_test_results.v1",
        "ts": _utc_now(),
        "passed": int(getattr(run, "passed", 0) or 0),
        "failed": int(getattr(run, "failed", 0) or 0),
        "all_passed": bool(getattr(run, "all_passed", False)),
        "plan_engine": plan_engine,
        "results": results,
    }
    if extra:
        payload["extra"] = extra
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Troubleshoot gate (v0) — classify ship_insufficient recovery"
    )
    parser.add_argument("--slug", default="", help="Project slug under PIPELINE_DIR/projects")
    parser.add_argument(
        "--project-dir",
        default="",
        help="Explicit project directory (overrides --slug)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Classify only; do not write recovery artifacts",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print decision JSON to stdout",
    )
    args = parser.parse_args(argv)

    project_dir: Path | None = None
    if args.project_dir:
        project_dir = Path(args.project_dir)
    elif args.slug:
        try:
            from pipeline.paths import projects_dir

            project_dir = projects_dir() / args.slug.strip()
        except Exception:
            project_dir = Path("projects") / args.slug.strip()
    else:
        parser.error("Provide --slug or --project-dir")

    assert project_dir is not None
    if not project_dir.is_dir():
        print(f"error: project dir not found: {project_dir}", file=sys.stderr)
        return 2

    decision = run_troubleshoot_gate(
        project_dir,
        write=not args.dry_run,
        set_outcome=not args.dry_run,
    )
    if args.json or args.dry_run:
        print(json.dumps(decision, indent=2))
    else:
        print(
            f"[troubleshoot-gate] {decision.get('slug')}: "
            f"{decision.get('recommended_action')} "
            f"({decision.get('primary_class')}, conf={decision.get('confidence')}) "
            f"fp={decision.get('fail_fingerprint')}"
        )
        print(f"  wrote {_decision_path(project_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
