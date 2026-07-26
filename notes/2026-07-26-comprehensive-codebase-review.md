# Comprehensive codebase review — 2026-07-26

**Mode:** Report-only (no mass fixes).  
**Review id:** bab4f792  
**Scope:** Factory application source — `pipeline/`, `scripts/`, root `test_*.py`, `COMMANDS.md` / notes.  
**Excluded:** `hermes-agent-main/`, `_archive/`, generated project workspaces under `thepipeline/projects/**`, debug_report dumps, large vendor trees.

---

## 1. Executive summary

**Health score: 7/10** for the factory core (orchestration + recovery + measurement). Overnight throughput is real (~3.2–3.4 field_proven/hour). Critical recovery paths (troubleshoot gate → consumer → thin ship) and measurement (truth-density, connector smoke) are tested and operational.

**Headline risks:**

1. **Capability cwd/entrypoint paths assume factory `.pipeline/projects/...` while live output is `PIPELINE_DIR` (thepipeline)** — explains connector `--execute` `WinError 267` and will break `invoke_capability` / goal compose reuse for many “verified” slugs.
2. **Default `get_pipeline_dir()` from a worktree resolves to empty-ish local `.pipeline` unless `PIPELINE_DIR` is set** — multi-root fixed only for truth-density/smoke CLIs, not the whole factory.
3. **Overnight “incomplete prior” auto-resume can stick forever** until a clean `end` line appears (writing `INCOMPLETE.md` does not clear the trigger).
4. **Swallowed exceptions (~231 bare `except Exception: pass`)** hide real failures on health/metrics/recovery side paths.

Core unit suite on recovery/goal/smoke paths: **143 passed** (selected high-value tests). Connector oracle smoke: **HARD PASS**.

---

## 2. Project context

AICompete is a multi-agent **software factory**: ideas → plan → implement (classic or grok_build) → field_ship → field_proven, with budgets, capability registry, connectors/workflows, goals, and finetune harvest. Runtime state lives under `PIPELINE_DIR` (local default intended as sibling/external `thepipeline`). Entry: `pipeline/runner.py`, overnight `scripts/overnight_grok_from_list.ps1`.

---

## 3. Verification evidence

| Check | Result |
|--------|--------|
| Selected factory tests (troubleshoot, budget ladder, field_ship, goal_*, connector_smoke, truth_density, classic_to_grok, complete_gate) | **143 passed** in ~16s |
| `python scripts/connector_smoke.py --oracle-only` | **HARD PASS** |
| `pipeline/**/*.py` AST parse | **0 syntax errors** (~149 modules) |
| Ruff on new/key modules | **47 issues** (mostly BLE001/S110 swallowed exceptions + 2 unused imports) |
| Default `resolve_pipeline_dir()` from worktree without env | `...\idea-impl2\.pipeline` (not thepipeline) |
| Registry sample (with PIPELINE_DIR=thepipeline) | `cwd_template`: `.pipeline/projects/<slug>/workspace` under **factory** root |

---

## 4. Architecture (critical paths)

```text
runner / overnight
  → run_loop health tick
       → budget_ladder (BE1/2/3)
       → troubleshoot_consumer (act prefer_thin | yield BE)
       → tick_prefer_thin_field_ship
       → grok_build engine hook
  → seed (kind:connector → run_workflow force)
  → field_ship → troubleshoot_gate emit recovery_decision

goal_attempt → goal_policy (reuse|compose|build|research|yield) → goal_trace
capability_tools.invoke_capability → subprocess (cwd = PROJECT_ROOT + cwd_template)
workflow_runner → capability / shell / n8n steps
```

**God-module pressure:** `budget_ladder.py` (~48KB), `troubleshoot_gate.py` (~41KB), `agent_process.py` (~49KB), `seeding.py`, `field_ship.py`, `runner.py` — all high-traffic; consumer is well-factored relative to these.

---

## 5. Key findings

| Severity | Type | Files | Description | Evidence | Recommendation | Effort |
|----------|------|-------|-------------|----------|----------------|--------|
| **High** | Path / logic | `capability_tools.py` ~162–171; `capability_registry.py` ~118–128, registry rows | Invoke resolves `cwd_template` / entrypoint paths against **factory `PROJECT_ROOT`**, but production projects live under **`PIPELINE_DIR/projects`**. Live registry: `cwd_template=.pipeline/projects/ai_movie_generation_suite/workspace` → factory path **missing**; thepipeline path **exists**. Matches overnight/execute `WinError 267 The directory name is invalid`. Goal compose `reuse`/`compose` and seed connectors inherit this. | Resolve cwd as `(get_pipeline_dir() / "projects" / slug / "workspace")` (or absolute under PIPELINE_DIR); store entrypoints relative to pipeline root, not factory `.pipeline/`. Rebuild registry after. | M |
| **High** | Path / env | `pipeline_config.py` `resolve_pipeline_dir`; worktree layout | Without `PIPELINE_DIR`, worktree defaults to local `.pipeline` (few projects), not `~/aicompete/thepipeline`. Only truth-density/smoke multi-root; runner overnight sets env, ad-hoc `python -c` / some scripts do not. | Document + optional home-factory fallback when nested `.pipeline` has no/few projects; keep explicit PIPELINE_DIR as source of truth. | S–M |
| **Medium** | Logic | `scripts/overnight_grok_from_list.ps1` incomplete detection | Prior overnight without `end` line triggers auto-resume **every** subsequent start. Writing `INCOMPLETE.md` does not stop re-detection. Can permanently disable fresh-list after one crash. | After recover, append synthetic `end ... incomplete_recovered` to prior `runner.log`, or skip dirs with `INCOMPLETE.md` / `truth_density.md`. | S |
| **Medium** | State / UX | `goal_policy.py` docs vs code | Doc says `KEEP_GOAL_TRACES` default-on; **env is never read** — always writes traces. Harmless but misleading; no off-switch for disk growth. | Honor env or drop claim; optional rotate/jsonl cap later. | S |
| **Medium** | Error handling | `pipeline/**` ~231 bare `except Exception: pass` | Metrics, recovery history, consumer traces can fail silently; hard to debug overnight. | At least log once (print/debug) on consume/history write failure; do not pass on state write failures. | M |
| **Medium** | Logic | `troubleshoot_consumer.py` empty fingerprint | Same-fp anti-thrash requires non-empty `fp`. Empty fingerprint → only `max_acts` stops thrash. | Treat missing fp as episode key `slug+action` or force yield after first act. | S |
| **Medium** | Security / safety | `workflow_runner` / `capability_tools` shell | Metachar block helps; force invoke still runs draft entrypoints. Acceptable for local factory; document trust boundary. | Keep force offline-default; never expose force over network. | — |
| **Low** | Maintainability | ruff F401 | Unused `GoalTree` import in `goal_attempt.py`; unused `Any` in `truth_density.py`; unused `cur` in `scripts/connector_smoke.py`. | Auto-fix. | S |
| **Low** | Completeness | Product connectors | Structural smoke green; execute soft-red by design until cwd bug fixed. | Fix path High first, then re-run `--execute`. | — |
| **Low** | Docs | Vision vs code | `notes/agi-lmaooo.md` is accurate north star; MCP factory / KG not implemented (correctly deferred). | Keep v0 policy only until path bug fixed. | — |

### No Critical (data loss / RCE) found in scoped review

No secrets committed in scanned modules; API keys via env; subprocess mostly `shell=False` with arg filters. Hermes rmtree and health rmtree are intentional local cleanup (monitor, not CWE critical for this threat model).

---

## 6. Strengths

- Clear **emit vs consume** recovery design; consumer serial, fixture-tested, durable `recovery_consume.v1` history.
- **Truth-density** honest about missing tokens; multi-root bare overnight names work.
- **Connector process oracle** + goal_trace give a real medium-path proof fixture without n8n.
- Overnight preflight canary/smoke + post-run reports (when process survives) is good ops hygiene.
- Dual-engine + BE ladder + thin-ship are production-hardened relative to most agent demos.
- 143 tests green on the critical recovery/goal surface.

---

## 7. Recommendations

### Quick wins (S)

1. Overnight: mark recovered incomplete so auto-resume does not stick forever.  
2. Ruff unused imports.  
3. Read or document `KEEP_GOAL_TRACES` truthfully.  
4. Empty recovery fingerprint → synthetic episode key.

### Should-do soon (M) — **path model**

5. **Fix capability cwd/entrypoint to PIPELINE_DIR** (highest leverage).  
6. Rebuild registry from thepipeline projects.  
7. Re-run connector smoke with `--execute` as regression gate (soft → expect more green).  
8. Log failures when durable history write fails.

### Larger (L) — align with agi-lmaooo

9. Explicit graph store only after path + compose execute are boring.  
10. MCP factory as **separate** loop (do not fold into run_loop god path).  
11. Reduce bare `except: pass` density on health tick path only first.

---

## 8. Verification recipes

| Fix | How to confirm |
|-----|----------------|
| cwd/PIPELINE_DIR | `PIPELINE_DIR=thepipeline python -c "from pipeline.capability_tools import invoke_capability; print(invoke_capability('ai_movie_generation_suite','--help')[:200])"` should not WinError 267 |
| Incomplete overnight | After recover, second overnight start should use fresh-list again (unless still mid-flight by design) |
| Consumer history | Force ship_insufficient fixture → tick → `recovery_history.jsonl` has `recovery_consume.v1` |
| Tests | `pytest test_troubleshoot_consumer.py test_goal_policy.py test_connector_smoke.py -q` |

---

## 9. Next actions (choose)

1. **Report only** (this document)  
2. **Fix High only** (capability path + incomplete overnight stickiness)  
3. **Fix High + Medium quick wins**  
4. **Hand off** to `/check-work` after fixes  
5. **Commit** current uncommitted factory work first, then fix High  

Default recommendation: **2** before next long overnight if you want connector execute / goal reuse to mean anything on thepipeline.
