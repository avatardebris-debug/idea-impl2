# Design: Factory truth-density report

**Date:** 2026-07-24  
**Status:** Draft for implementation planning  
**Scope:** Read-only reporting after overnight / factory runs  
**Out of scope:** Web dashboard, graph engineering, replan product, bulk convert, held-out E2E suite

---

## 1. Purpose

After a factory run (overnight Grok from-list, focused canary, or drain overnight), the operator should get a short report that answers:

1. How many projects reached **field proven** (product field tests passed; status `field_proven`) during this run window?
2. How long did the run take in **hours**?
3. How many **tokens** were spent, if we know?
4. Therefore: **field proven per hour**, and **field proven per million tokens** when tokens are known.

### Why this is next

The factory can already finish and prove software under Grok Build. The missing simple lever is a **trusted scoreboard**. Without it, every change (recovery consumer, Hermes routing, classic-to-Grok, complete-gate) is judged by feel. With it, week-over-week process improvement becomes possible. That is gentle recursive process improvement (RSI-lite), not training a new base model.

### Design principles (operator preference)

- Bang for buck over maximal growth.
- Simple systems that can scale later.
- Business-clear language in the report (avoid dense abbreviation walls).
- Honest partial data: never invent token counts of zero when instrumentation is missing.

---

## 2. Primary metrics

| Metric | Definition |
|--------|------------|
| **Field proven in window** | Count of projects whose status is `field_proven` and whose prove timestamp falls inside the run window |
| **Wall-clock hours** | Elapsed real time from run start to run end (default denominator for “per hour”) |
| **Active work hours (optional)** | Sum of active-work time if available from project state or metrics; second column only when data exists |
| **Field proven per wall-clock hour** | field_proven_in_window ÷ wall_clock_hours |
| **Tokens in window** | Sum of token usage attributed to the run, if available |
| **Field proven per million tokens** | field_proven_in_window ÷ (tokens / 1_000_000), only if tokens known |

Either wall-clock hours or active work hours is acceptable as a rate base. **v1 default: wall-clock hours.** Report active work hours when available, but do not block the report if they are missing.

---

## 3. Run window

### Preferred start sources (first match wins)

1. Overnight log directory / preflight timestamp (e.g. `logs/overnight_YYYYMMDD_HHMMSS/preflight.json` → `ts`).
2. Explicit CLI `--since` ISO timestamp or path to that log directory.
3. Last `runner_start` event in `state/activity.jsonl` for this `PIPELINE_DIR`.
4. Fallback: last 24 hours from “now”.

### Preferred end sources

1. Process end / last line mtime on `runner.log` for that overnight directory.
2. Last activity event timestamp after start.
3. “Now” if the run is still considered open (report should label **partial / in progress**).

### Overrun note

If configured `time_limit_min` from preflight is present and wall-clock elapsed exceeds it by a meaningful margin (e.g. >10%), the report must state that the process **overran the configured limit**. This is a data-quality signal, not a failure of the report.

---

## 4. Data sources

### Field proven count

- Scan `{PIPELINE_DIR}/projects/*/state/current_idea.json`.
- Count projects with `status == "field_proven"`.
- Prefer prove time from `field_proven_at` if present; else `last_active_work_at` or file mtime only as weak fallback (label as low confidence if used).

### Hours

- **Wall clock:** end − start as defined above.
- **Active work (optional):** if projects or metrics already store active-minute style fields for the window, sum them and convert to hours. If not, omit the active-work rate; do not invent it.

### Tokens

Use existing pipeline metrics when present:

- `pipeline/metrics.py` already tracks per-project `tokens_used` and can summarize `total_tokens` / stall tokens for a metrics run directory.
- Activity JSONL may have LLM call records with duration; use token fields only when actually present on events.

Rules:

| Situation | Report behavior |
|-----------|-----------------|
| Full token coverage for the window | Report totals and field-proven per million tokens |
| Partial coverage | Report known tokens as **partial**, do not claim efficiency is complete |
| No token data | Omit per-token rates; state “tokens not instrumented for this window” |

Never display “0 tokens” as if the run was free when the real answer is “unknown.”

---

## 5. Outputs

### A. Markdown report (required)

Write one file per invocation, default path:

```text
{PIPELINE_DIR}/logs/<run_id_or_latest>/truth_density.md
```

or, if no overnight log dir:

```text
{PIPELINE_DIR}/metrics/truth_density_latest.md
```

Content outline (plain English):

1. **Run window** — start, end, wall-clock hours, configured limit if known, overrun flag.
2. **Throughput** — field proven in window, per wall-clock hour; optional active-work hour rate.
3. **Spend** — tokens if known; field proven per million tokens if known; partial flag if needed.
4. **Optional context (counts only)** — ship recoveries, budget yields, Hermes skipped vs run (if easy from activity); no new analytics platform.
5. **Slug list** — short list of projects that became field proven in the window (for spot checks).

### B. History line (recommended, tiny)

Append one JSON object per report to:

```text
{PIPELINE_DIR}/metrics/truth_density_history.jsonl
```

Fields: timestamps, counts, rates, token mode (`full` | `partial` | `missing`), source of window. Enables week-over-week without a database.

### C. Overnight hook (optional, later)

Overnight script may print the report path at shutdown. Not required for v1 if the standalone script is enough.

---

## 6. CLI contract

```text
python scripts/report_truth_density.py
  --pipeline-dir PATH          # default: $PIPELINE_DIR
  --since PATH|ISO             # overnight log dir or start time
  --until ISO                  # optional end
  --out PATH                   # optional report path
```

- Read-only with respect to project status (must not change `current_idea.json` statuses).
- Exit 0 on successful report even if tokens missing.
- Exit non-zero only on hard errors (unreadable pipeline dir, etc.).

---

## 7. Implementation sketch

| Piece | Responsibility |
|-------|----------------|
| `scripts/report_truth_density.py` | CLI entry |
| `pipeline/truth_density.py` (or under metrics) | Window resolution, scans, rate math, markdown + jsonl writers |
| Reuse | `metrics.py` summaries when a metrics dir exists; activity.jsonl for timestamps |
| Tests | Temp pipeline dir with 2–3 fake projects + synthetic preflight/log; assert counts and rates; assert partial tokens wording |

Keep the module small. Prefer pure functions for “count field proven in window” and “format report.”

---

## 8. Success criteria (v1)

1. One command after a run produces a readable markdown report.
2. Field proven per wall-clock hour is always present when at least one end-start pair is known.
3. Token rates appear only when token data exists; otherwise the report says so clearly.
4. Active work hours appear only when available; wall-clock remains the default rate base.
5. No new long-lived services, databases, or dashboards.
6. Unit tests cover counting and formatting without a live overnight.

---

## 9. Explicit non-goals

- Held-out cold-start suite (previously called “H1” in notes — a separate tiny from-scratch idea run; not this design).
- Graph engineering, goal OS, Grok Workflows embedding.
- Full replan / debug solution products for the troubleshoot consumer.
- Web UI or email alerts.
- Optimizing for maximum field proven at the cost of dishonest metrics.

---

## 10. Future scale path (not v1)

Once the report is boring and trusted:

1. Use recovery class histograms to decide whether to build replan or debug packages.
2. Use field-proven-per-hour to evaluate factory changes.
3. When inventory of proven tools is rich and cold-start is proven separately, consider graph composition and feature expander.

---

## 11. Open choices locked for v1

| Choice | Decision |
|--------|----------|
| Default hour base | Wall-clock hours |
| Active work hours | Optional second rate if data exists |
| Token missing | Honest “not instrumented,” not zero |
| UI | Markdown file + optional jsonl history |
| Mutation | Read-only on project status |
