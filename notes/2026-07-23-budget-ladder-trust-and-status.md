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
- **Grok Workflows (Rhai) inside idea-impl** — see §7 vocabulary (enhancement later, not earned yet)
- Tiny graph.v1 + MCP factory v0 shipped via plan 2026-07-26-goal-compose-mcp-factory-v0; **graph engineer product still deferred**

---

## 7. Vocabulary: “workflow” vs “Grok Workflows” (2026-07-24)

**Convention going forward:**

| Phrase | Means |
|--------|--------|
| **workflow** (unqualified) | **Our** plan: org/SOP/CEO architecture, connectors, Lego products, factory assemblies, graph nodes for goal execution |
| **Grok Workflow** / **Rhai** | Grok Build TUI multi-agent scripts (`.rhai`, `/workflow`, `/workflows` dashboard) |

**Relationship (same pattern as Grok Build skills):**

- Factory / graph / overnight **worked first** without Grok-specific enhancements.
- **Grok Skills** were added as enhancements inside the software-building architecture once the base loop worked.
- **Grok Workflows (Rhai)** will be the same class of enhancement: optional callable Lego later, **not** a replacement for our workflow/org/SOP plan.
- They do **not** replace CEO/org modeling; a graph node may one day *bind* a Grok Workflow the way it binds a skill or field_proven slug.

**Earn order:**

1. Build out **graph engineering** (and goal/architecture selection) in idea-impl / thepipeline first.  
2. We have **not** earned embedding Grok Workflows into idea-impl until that foundation exists.  
3. Authoring/using Rhai is a **side story** only when there is a clear use case — not a current factory dependency.

**Nested “workflow in workflow” in our language** = org/SOP subgraphs and Lego composition on the knowledge graph — **not** Rhai-in-Rhai (host also does not support nested Grok Workflows today).

---

## 8. Ambitious / AGI experimental: recursive improvement via successors (not yet)

**Status:** Discussion only. **Not earned.** Do not implement. Needs more safety procedures before any prototype.

### The idea (user framing)

Recursive self-improvement (RSI) does imply the system can improve “itself.” That need **not** mean mutating the live original in place.

Safer mental model: **successor copies**, not hot self-surgery:

```text
v1 (frozen original, never edited by the improver)
  └── works on / proposes v2 (isolated copy or worktree / branch / PIPELINE_DIR variant)
        └── once v2 is proven under QC, humans (or later policy) may promote v2 → next outer
              └── optionally v2 hosts a nested improver that only authors v3 …
```

- **At most two live depths** for a long time (outer supervisor + one inner improver), not infinite nesting.
- **Original stays untouched** until an explicit promote step.
- Improver does not have to “push and overwrite production”; it can leave a candidate successor for review.

That *is* a form of RSI (each generation improves the next), with **ordering and rigidity** as the current safety rails.

### Why not ready (reasons, not dismissal)

| Gap | Why it blocks RSI-now |
|-----|------------------------|
| Graph engineering not built | No durable map of process + outcomes to choose architectures |
| Held-out / proof gates still thin | No automatic “v2 is better than v1” oracle |
| Budget ladder / factory only recently rigidified | Nested improver would thrash without serial focus lessons |
| No promote protocol | Without dual control, “successor” becomes silent takeover |
| Grok Workflows = enhancement later | Reflection/eval SOPs not yet encoded; manual path first |
| Trust/mandate deferred | Self-mod of spend/identity must never free-run |

**Possible ≠ ready.** Full RSI remains experimental direction after quality controls, ordering, and rigidity prove out; then carefully add **slack** (knowledge-graph change tracking, process graph engineering, measured experiment).

### Intended path (manual → automated under oversight)

1. **Prove rigid factory** (overnight serial ladder, field_prove, held-out, no mass thrash).  
2. **Manual meta path:** discuss → decide next factory/process change → implement with review (human oversees).  
3. **Encode** that discussion/eval/self-reflection path as a **Grok Workflow** (and/or skills) once the manual path is stable.  
4. **Replace only the manual *routine*** under oversight — not free rewrite of the root.  
5. **Successor model:** improver authors **v_next** in isolation; promote only after QC; outer original stays frozen until promote.  
6. **Later slack:** KG tracks process changes; graph engineering of process; less rigid only where evidence supports it.

### Safety procedures to design before any prototype (checklist for later)

- [ ] Max nesting depth = 2 (outer + one improver) unless explicitly raised  
- [ ] Improver **cannot write** the live original tree / production `PIPELINE_DIR`  
- [ ] Candidate successor path/worktree only  
- [ ] Held-out + factory smoke must not regress before promote  
- [ ] Human (or dual control) **promote** step  
- [ ] Substrate vs product goals labeled; substrate changes never silent overnight  
- [ ] Full audit log (who proposed, what diff, what proof)  
- [ ] Kill switch / freeze improver without killing product factory  

### One-line stance

**Yes:** recursive improvement via **isolated successors** and proven promote is a coherent AGI-experimental direction.  
**No (now):** nesting self as a free tool or mutating the original in place.  
**Next earn:** graph + selection + held-out; then optional Grok Workflow encoding of the *manual* improve loop; RSI promote chain last.

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

---

## 7. Classic → Grok canary (2026-07-24)

**supportagent_workflow_builder (BE1 active_yield, p3 near-done):**
- Converted with `classic_be_to_grok.py` → `engine=grok_build`, `prefer_thin_field`.
- Serial resume **without** `--fresh-list-only` (that flag cleared canary work earlier).
- Thin-field ship: first field pass 1/14 (import/syntax), repair → **14/14 field_proven** ~11m.
- Post-success idle seeded Hermes/list (Ollama 404 noise) — stop runner after focus batch.

**BE0 lifetime fossils converted next (force-lifetime + phase_retries reset):**
- `ai_author_suite` p6/6
- `dropshipserviceecommerce_autoseo_autometa` p3/3
- `email_tool` p6/6
- `pocketknife_of_the_internet` p9 (total clamped 6→9)

Grok Build runs have been healthy; no mass BE1 revive.

### If fossils still fail after Grok

Consider a **plan-sufficiency / re-plan evaluation** step (not built yet):
- After N gate blocks or field fail-repair exhaustion: ask whether master_plan /
  phase tasks were sufficient vs product aim.
- Options: re-run idea-plan/phase-plan, thin-field ship, archive, ASK_OPERATOR.
- Distinct from blocker-identifier (cost/benefit on stuck work) — this questions
  the *plan artifact*, not only budget/deps.


### BE0 lifetime batch result (2026-07-24, ~55m serial)

| slug | result | field | notes |
|------|--------|-------|-------|
| ai_author_suite | field_proven | 10/10 | bad_plan + product_bug repair |
| dropshipservice… | field_proven | 10/10 | full grok phase3 + thin ship |
| email_tool | field_proven | 11/11 | grok_driver blocked on pytest; thin field still proved product |
| pocketknife_of_the_internet | budget_exceeded | 2/10 fail | "Phase 9 stuck: 0/3 tasks after 15m"; never got dedicated driver window |

**Lesson:** Grok thrives on near-done fossils with real code; thin-field can ship product proof even when unit-test suite is broken. Hard fails are plan/phase mismatch fossils (pocketknife p9/9 zero tasks) — re-plan evaluation candidate.


---

## 8. Recovery classes, re-plan, feature expander (2026-07-24)

Grok Build has been healthy on classic BE canaries. Remaining stalls are often
**not** "code is wrong" — we need better **analytics / reporting / routing** so
the manager (or a recovery skill) picks the right next move.

### Recovery classes (route, don't thrash)

| Class | Signal | Better route |
|-------|--------|--------------|
| **Env / runtime** | e.g. ONsquared loading hang, local service down, path/env | diagnose infra; don't rewrite product |
| **Connectivity / credentials** | field tests need IMAP/SMTP/API keys; human 2FA | `needs_human_attestation` / dry-run / mock rails — not infinite implement |
| **Plan insufficient** | field plan invents wrong package/CLI; tasks don't match workspace layout | **re-plan evaluation** (master + phase tasks vs product aim) |
| **Artifact vandalism** | agent deleted/truncated master_plan; auto-trim removed critical code | restore from bak/git; re-plan if incomplete; ban destructive trim of gates |
| **Spin no progress** | same status long wall, 0 checkbox movement | blocker-identifier + re-plan or thin-field, not more same-agent retries |
| **Product incomplete but shippable** | unit suite broken, product API works | thin-field / field_proven path (seen on email_tool) |

**email_tool lesson:** field-proving and "spin in place" may be **connectivity /
credential** more often than pure logic bugs. Route to mock/dry-run fixtures and
human credential grant instead of endless executor loops.

### Re-plan evaluation (design — not built)

After N gate blocks, field fail-repair exhaustion, or "phase stuck 0/N tasks":

1. Ask: was master_plan / phase tasks **sufficient vs product aim**?
2. Options: re-run idea-plan + phase-plan · thin-field only · archive · ASK_OPERATOR
3. Distinct from blocker-identifier (cost/benefit) — this questions the **plan artifact**

Historical failure modes to encode:
- AI **deleted master_plan** then partial recovery → incomplete plan
- **Auto-trim** of content that was crucial for functionality
- Need bak/git restore + plan quality gate before re-implement

### Feature expander (design — later goal-prove)

After **field_proven**, optional process (human-driven or automated later):

1. **Inventory** what the product already does (from field tests / CAPABILITIES / code)
2. **Reason** about ways to make it better (gaps, UX, connectors, reliability)
3. **Plan** additive features (not greenfield restart)
4. **Implement** incrementally → re-field-prove

Intent: factory starts **minimal on purpose** to reach field_proven. Feature expander
is how products grow without "add another product / connector / start over."

Likely sits in **goal-prove** pipeline later; for now notes-only.

### Active BE1 batch (this session)

Serial classic→grok: `extraction`, `udemy_training_tool`, `video_management`.


### BE1 trio result (2026-07-24, ~45m)

| slug | result | field | notes |
|------|--------|-------|-------|
| extraction | field_proven | 11/11 | thin ship; status clobber race after ship (fixed) |
| udemy_training_tool | field_proven | 12/12 | thin ship from planning |
| video_management | ship_insufficient | 3/5 | p5 review PASS 71/71 but complete blocked by **stale phase-1 checkboxes** (20/25); no prefer_thin until manual; heuristic plan 3 pass/2 fail |

**Factory bug pattern:** complete gate counts *all* open checkboxes across old phases → grok can finish last phase + review PASS and still never `complete` / never auto thin-field. Recovery should: (a) only gate current phase, or (b) auto prefer_thin when phase>=total + review PASS, or (c) re-plan evaluation on stuck checkboxes.

