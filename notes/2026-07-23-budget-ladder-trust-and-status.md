# Budget ladder, open-world trust, and factory status (2026-07-23)

Working notes from design + implementation discussion. **Not runtime config.**
Code refs: `pipeline/budget_ladder.py`, `pipeline/goal_trace.py`, `scripts/run_held_out.py`,
user skill `~/.grok/skills/blocker-identifier/`. Commits around `4cd988c` / `ccfc2de`.

---

## 1. Where we stand (snapshot)

### Done (factory)

| Area | Notes |
|------|--------|
| Overnight Grok from-list (P0) | Serial CLI, plan skills, thin ship, rework caps, fresh-list default |
| Idle field park | Empty-queue field_testing → deeper_work_needed |
| Budget yield ladder | Active clock; strikes BE1→BE2→BE3; prereq reset; rule manager |
| Corpus status weights | field_proven high; BE / deeper_work zero |
| Connector canary | Harness interfaces only — not product field_proven of bridges |
| Held-out skeleton | `python scripts/run_held_out.py` (H1–H5 structural) |
| goal_trace.v1 | Sandbox file_exists oracle under `$PIPELINE_DIR/goal_traces/` |
| blocker-identifier skill | User-scope skill; emits `blocker_report.v1` for manager menu |

### Done (product / thepipeline examples)

| Outcome | Notes |
|---------|--------|
| Operator recovery | `sim_real_comparator` → field_proven (pytest 23/23 + CLI smoke); `last_decision=THIN_FIELD` |
| Overnight after unlock | `sim_real_discriminator` field_proven via grok_build ~35–40 min later |
| Other Grok wins (same window) | e.g. goal_decomposer, domain_randomization_controller, primitive_success_detector |
| Classic BE noise | Multi-thousand-minute notes = calendar/stale session fossils, not real 2h thrash |

**Takeaway on parallel operator + overnight:** Shared `PIPELINE_DIR` state is the bus.
Operator can field_prove a prereq; the running from-list does not need to “own” that
work—it re-scans `requires:` and seeds dependents when deps satisfy. Long-lived runners
do **not** load new factory code until restart.

### Explicitly deferred

- Full knowledge graph / graph engineer / graph field-goal prove
- Soft-skip `requires:` as default policy
- Always-on goal OS with live money/identity
- Infinite idea spawn on stuck chains
- Wiring the skill *file* into the runner (Python classifier already emits same schema)

---

## 2. Budget ladder design (shipped shape)

Semantics: `budget_exceeded` on disk stays for compatibility; meaning is **yield the
slot**, not permanent death.

| Strike | Intent | Code behavior (v1) |
|--------|--------|---------------------|
| 1 | AUTO_RETRY_CLEAN | Resume `pre_budget_status`, fresh session + last_active_work |
| 2 | Tactical BE2 | Resume + set `be2_path` = `debug` \| `thin_field`, `be2_pending` |
| ≥3 | BE3 report + menu | Write `blocker_report.json`, rule `manager_decide`, apply decision |

**Active clock:** charge only while work is fresh; idle &gt; `BUDGET_IDLE_GAP_MINUTES`
(default 45) pauses; long idle on wake **refreshes** session instead of calendar BE.

**Prereq reset:** seed blocked by unlocked BE dep → one reset so the chain can progress;
still does **not** treat BE as full complete for `requires:`.

**Env (defaults on):** `BUDGET_ACTIVE_CLOCK`, `BUDGET_IDLE_GAP_MINUTES`,
`BUDGET_BE1_AUTO_RETRY`, `BUDGET_BE2`, `BUDGET_BE3_BLOCKER`, `BUDGET_PREREQ_RESET`.

**blocker_report.v1 / manager menu (closed):**
`AUTO_RETRY_CLEAN` · `EXTEND_BUDGET` · `DEBUG_AGAIN` · `THIN_FIELD` · `BYPASS_RETURN` ·
`SOFT_SKIP_REQUIRES` · `SUBSTITUTE` · `IGNORE_NEXT` · `ASK_OPERATOR` · `ARCHIVE_GOAL_EDGE`

**next_policy:** `remain_queue` · `ask_again` · `ignore_next` · `ignore_until` · `cooldown`

---

## 3. BE2 / BE3 — serial ladder (post 60m debrief fix)

### 60m run lesson (2026-07-23 evening)

- BE1 used `strikes <= 1`, so **strike-0 fossils** all got `AUTO_RETRY_CLEAN` at once.
- Morning report “16 projects” = mass revive timestamps, not real multi-project work.
- “1000 retries” notes = lifetime `phase_retries` sum / cap path, **not** 1000 real
  attempts in a 60m window.
- Why not BE2? Mass BE1 never let a single project re-yield with `strikes=2` under focus.

### Fixed behavior (serial)

- BE1 only if `budget_strikes == 1` (real yield via `apply_budget_yield`).
- Strike-0 fossils stay parked (overnight ignores).
- `BUDGET_LADDER_SERIAL=1`: one recovery focus; tick processes **at most one** BE.
- BE2 `debug` enqueues systematic-debug to executor; `thin_field` sets prefer flag.
- Lifetime retry force now uses `apply_budget_yield` so strikes advance.

### Remaining gap

BE2 **thin_field consumer shipped** (`tick_prefer_thin_field_ship` + `prefer_thin_field`
enables classic thin ship; `BUDGET_THIN_FIELD_TICK=1`). BE3 ASK_OPERATOR dropbox loop
not productized. Operator loop still design-only.

### After the 60m run: design then implement

A healthy overnight may produce **zero** new strike-2/3 events (fresh-list + short
seeds + active clock). That is OK.

**Manufacture tests** (preferred over waiting for production pain):

1. Unit: already in `test_budget_ladder.py` (strikes, timer_glitch → AUTO_RETRY_CLEAN).
2. Fixture project: force `budget_strikes=2`, `status=budget_exceeded`, near-done
   pre_budget → process ladder → assert `be2_path` / later assert enqueue once consumer exists.
3. Fixture strike=3 + absurd wall note → BE3 report + decision.
4. Optional integration: temp `PIPELINE_DIR` + one tick of `tick_process_budget_yields`.

Do **not** require a real multi-hour BE on a valuable project just to exercise BE2/BE3.

### BE2 consumer (design only until we implement)

```text
if be2_pending and be2_path == "debug":
    enqueue one systematic-debug / pre_force_debug style pass; clear be2_pending
if be2_pending and be2_path == "thin_field":
    when phase complete / near-done: prefer thin field_ship; clear be2_pending
```

Cap: one package per strike-2; then either success terminal or escalate to strike 3.

---

## 4. Open-world trust / funds / captcha (vision — furthest forward)

Discussed only; **no implementation planned soon.**

### Distinction

| Layer | Role |
|-------|------|
| Software factory | Build tools that *can* call the world |
| Trust / mandate | Decide *whether* they may fire (policy, human, audit) |
| Human | Root of trust for money and legal identity |

**Entitlement ≠ capability.** Secrets and payments are not “another connector skill.”

### Three secret classes

1. **Delegated, revocable** — scoped API keys, OAuth (machine may hold under mandate).
2. **Never machine-held** — bank passwords, seed phrases, full PANs, recovery codes.
3. **Human-gated** — captcha, KYC, 2FA, “confirm transfer” (first-class goal nodes).

### Mandate stack (goal OS later)

```text
Goal → Policy → Mandate → Credential grant → Tool call → Receipt (goal_trace)
```

### Product sketch: push-to-approve funds (future)

```text
Agent requests funds for explicit use case
  → push: human approves *intent*  → mandate "in process"
  → second step: human approves exact $ / payee / rail
  → human completes factor only humans should hold (wallet/bank confirm)
  → agent executes only inside sealed mandate
  → receipt closes mandate (ties to goal_id)
```

- **Dual approve** (intent + execution) beats single blind push.
- Crypto rails already force amount/destination/signature QC; mandate UI is the
  *social* half before settlement.
- “3-factor” story: agent request token + human device push + human-to-institution
  factor — **without** teaching the agent to store passwords.
- Consumer apps (Venmo/Cash App) ≠ first-class bot APIs; design around cooperation.

### Principles to keep

1. Least privilege per goal  
2. Separate planning from power  
3. Ephemeral credentials  
4. No secrets in logs / corpus / FT  
5. Dual control for irreversible acts  
6. Named principal (liability)  
7. Fail closed  
8. Captcha/KYC = `needs_human_attestation`, not “defeat automation”  

Park until software field_prove + goal_trace + connectors are boring.

---

## 5. What next (while / after 60m overnight)

### While run is live

- Do **not** start a second from-list/bulk field_ship on same PIPELINE_DIR.
- Optional: skim logs for `[budget_ladder]`, active-clock refresh, new field_proven.
- Trust/mandate stays notes-only.

### After run debrief

1. New field_proven vs BE  
2. Any ladder language vs only fossil multi-k-minute BE  
3. `python scripts/run_held_out.py`  
4. Decide: implement BE2 consumer next vs product list  

### Factory backlog (priority)

1. **BE2 consumer** (+ manufactured fixtures)  
2. BE3 ASK_OPERATOR surface  
3. Held-out real H1 E2E (tiny idea → field_proven)  
4. GitHub goal_trace demo  
5. Much later: mandate / push-funds product  

### Product backlog (parallel)

- Robot / sim-to-real chain after discriminator  
- Fresh-list overnight continues  
- Ignore classic BE fossils unless chain-critical  

---

## 6. Related notes / commands

- Overnight runbook: `notes/2026-07-22-overnight-grok-from-list-runbook.md`  
- P1 held-out + goal traces plan: `notes/2026-07-22-p1-held-out-and-goal-traces.md`  
- Env + canary + held_out: `COMMANDS.md`  
- Manual triage: `/blocker-identifier <slug>`  
