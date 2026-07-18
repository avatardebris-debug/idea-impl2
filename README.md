# Idea Development Pipeline (Factory)

A multi-agent **software factory** that turns ideas into working projects: plan → code → test → review → iterate, then optionally **ship-prove** with field tests. Designed to run unattended for hours on a local machine or a cloud GPU box.

Give it a backlog (or a single idea). It seeds projects, manages budgets and queues, reuses capabilities when possible, and can harvest finetune data from completed work.

---

## What this is

| | |
|---|---|
| **Factory repo (this code)** | Agents, runner, prompts, scripts, constitution/mission |
| **Output directory** | Projects, message bus, registry, goals, finetune corpus — **not** mixed into git history of the factory by default |

**Not** a single-chat coding assistant. It is a long-running orchestration system with specialized agents, disk-backed state, and separate **build** vs **ship** loops.

### Mission (short)

Build **reusable** software that compounds: prefer verified capabilities over greenfield rebuilds, keep modules maintainable, capture training signal from runs. See `mission.yaml` and `constitution.yaml`.

---

## Factory vs output

Runtime state is resolved by `pipeline/pipeline_config.py`:

| Environment | Output root |
|---|---|
| Local (default) | Sibling `../thepipeline` if it has `projects/` |
| Explicit | `PIPELINE_DIR=/path/to/output` |
| Cloud | Factory `.pipeline/` when `PIPELINE_CLOUD=1` (often a clone of the output repo) |

On startup, `pipeline/runner.py` bootstraps the output tree and prints the resolved path.

```
factory/  (this repo)          output/  (PIPELINE_DIR)
├── pipeline/                  ├── projects/<slug>/
├── agent.py                   │   ├── workspace/     # generated code
├── mission.yaml               │   ├── state/         # current_idea.json, plans
├── master_ideas.md            │   └── phases/ship/   # field tests, results
└── scripts/                   ├── state/             # bus DB, registry, metrics
                               ├── shared_libs/
                               ├── goals/
                               ├── finetune_corpus/
                               └── queues/
```

---

## Two loops: build and ship

### 1. Main pipeline (build)

Subprocess agents + SQLite message bus (legacy JSONL still migrates in):

```
Idea → Idea Planner → Phase Planner → Executor → Validator → Reviewer → Manager
                         ↑                                              │
                         └──────────── rework / fix ────────────────────┘
                                                                        │
                                                          Ideator ◄─────┘
```

| Agent | Role |
|---|---|
| **Idea Planner** | Raw idea → multi-phase master plan |
| **Phase Planner** | Phase → 3–8 coding tasks |
| **Executor** | Writes code in the project workspace |
| **Validator** | Pytest + optional structural import graph |
| **Reviewer** | Structured code review (blocking vs non-blocking) |
| **Manager** | Routing, queues, non-interrupt except emergencies |
| **Ideator** | Always-on brainstorming (`mission.yaml` construct/deconstruct) |

**Statuses (build track, simplified):**

| Status | Meaning |
|---|---|
| `phase_N_planning` / executing / … | In flight |
| `complete` | All planned phases finished — **eligible for ship-prove** |
| `mvp_complete` | Plan exhausted early; **does not** unlock `requires:` deps; polish later |
| `budget_exceeded` | Time/budget stop; may polish or reset |
| `dep_waiting` | Blocked on prerequisite projects |

### 2. Ship-prove (field test)

Separate agent set (`--ship-prove`). Does **not** seed new ideas from `master_ideas.md`.

```
complete → field_test_planner → field tests
                ↓ fail                    ↓ pass
           debug_loop → executor     thermo_reviewer (optional)
                ↓                         ↓
           retest / ship_insufficient   ship_evaluator
                                              ↓
                                   field_proven | needs more tests | ship_insufficient
```

| Ship agent | Role |
|---|---|
| **field_test_planner** | LLM product/integration tests + baseline runner |
| **debug_loop** | Structured investigation after field failures |
| **thermo_reviewer** | Deep quality pass (skippable) |
| **ship_evaluator** | Final verdict: `FIELD_PROVEN` / more tests / insufficient |
| **executor** | Shared fixer for ship rework |

**Eligibility:** only `status=complete` is freshly queued. Terminals: `field_proven`, `ship_insufficient`.

**Controlled entry (recommended):**

```bash
./scripts/run_ship_prove.sh --slug my_project --provider grok --model grok-4.3
# or Windows:
.\scripts\run_ship_prove.ps1 -Slug my_project -Provider grok -Model grok-4.3
```

The script clears **stale ship-agent** bus messages first. Avoid unfiltered mass ship-prove over old `field_test_planning` piles without a clean bus.

Prompts: `pipeline/prompts/field_test_planner.md`, `ship_evaluator.md`.

---

## Major subsystems (beyond the original 7 agents)

| Area | What it does |
|---|---|
| **Quality gates** | Soft-by-default `PIPELINE_REQUIRE_TESTS` / `PIPELINE_STRUCTURAL_GATE`; ship-prove turns them on via setdefault |
| **Import graph / layout** | Local stale imports (B3); package layout repair before field tests |
| **Capability registry** | Search/reuse verified tools (`shared_libs/`, registry DB); optional invoke-before-seed |
| **Dependency policy** | `requires:` on ideas; only full complete / field_proven unlock deps (not bare `mvp_complete`) |
| **Seed capacity** | Parallel seed slots, idle seeding policy, starvation fixes |
| **Polish mode** | `--polish` / `PIPELINE_POLISH_FIRST` drain incomplete / mvp work before greenfield |
| **Goals** | `--goal` lines → goal trees; `--attempt-goal`; optional **Hermes** for research-style goals |
| **Finetune corpus** | Collect / weight / gate / polish shards under output `finetune_corpus/` |
| **Workflows** | Registered workflows + n8n-style connectors (optional) |
| **Ops** | `pipeline_status`, activity log, health checks, force-advance, metrics reports |

Full flag tables and cloud ops: **`COMMANDS.md`**.

---

## Quick start

```bash
# Install
pip install -r requirements.txt
# Optional: openai (Grok/xAI), anthropic, etc.

# One idea until done
python pipeline/runner.py "Build a CLI that converts markdown to HTML"

# Backlog (master_ideas.md in output or factory root)
python pipeline/runner.py --from-list

# Overnight (Ollama example)
python pipeline/runner.py --from-list --provider ollama \
  --model qwen3.6:35b-a3b-q4_K_M --time-limit 0 \
  --base-budget 120 --phase-budget 45

# Resume
python pipeline/runner.py --resume

# Status dashboard
python -m pipeline.pipeline_status

# Ship-prove one completed project
./scripts/run_ship_prove.sh --slug <project_slug> --provider grok --model grok-4.3

# Goals
python pipeline/runner.py --list-goals
python pipeline/runner.py --attempt-goal <goal_id> --provider ollama --model qwen3.6:35b-a3b-q4_K_M
```

### Cloud sketch

```bash
git clone https://github.com/avatardebris-debug/idea.git
cd idea
pip install -r requirements.txt
bash cloud_setup.sh          # Ollama, model, .pipeline bootstrap
source .venv/bin/activate
export PIPELINE_CLOUD=1
export PYTHONUTF8=1

# Build overnight (safer default when few projects are complete)
SHIP_PROVE_BACKGROUND=1 ./scripts/run_ship_prove.sh --main-pipeline \
  --provider ollama --model qwen3.6:35b-a3b-q4_K_M
```

---

## Configuration

| File | Purpose |
|---|---|
| `mission.yaml` | Mission text, hard/soft values, ideator pass wording |
| `constitution.yaml` | Quality standards, agent weights, pipeline limits |
| `master_ideas.md` | Idea backlog (`requires:`, tags, `--goal`, `--hermes`, …) |
| `pipeline/prompts/*.md` | Per-role system prompts |
| `.env` | Local secrets/paths (`PIPELINE_DIR`, `XAI_API_KEY`, `PIPELINE_MODEL`, …) — do not commit secrets |

### Environment variables (common)

| Variable | Purpose |
|---|---|
| `PIPELINE_DIR` | Output root override |
| `PIPELINE_CLOUD=1` | Use factory `.pipeline/` |
| `PIPELINE_MODEL` / `PIPELINE_PROVIDER` | Defaults when CLI omits them |
| `PIPELINE_LIGHT_MODEL` | Smaller model for light-tier agents |
| `PIPELINE_REQUIRE_TESTS` | Require tests at validation (default off; on for ship) |
| `PIPELINE_STRUCTURAL_GATE` | Local import-graph gate (default off; on for ship) |
| `PIPELINE_POLISH_FIRST` | Prefer polish queue before new seeds |
| `PIPELINE_INVOKE_BEFORE_SEED` | Capability reuse hard skip when match is strong |
| `MAX_FIELD_TEST_LOOPS` | Field-test retry budget (script default often `2`) |
| `XAI_API_KEY` | Grok / xAI (`--provider grok`) |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` | Other providers |
| `PYTHONUTF8=1` | Recommended on Windows |

---

## Repository map

```
.
├── pipeline/
│   ├── runner.py              # Main entry — build or --ship-prove
│   ├── startup.py / run_loop* # Startup, budgets, stalls, seed idle
│   ├── message_bus.py         # SQLite-backed agent queues
│   ├── agents/                # Build + ship agent processes
│   ├── prompts/               # System prompts (markdown)
│   ├── field_test_runner.py   # Baseline + LLM field tests
│   ├── ship_*.py              # Ship-prove mode, status, recovery
│   ├── capability_*.py        # Registry, reuse, metrics
│   ├── corpus_*.py            # Finetune harvest / gates / weights
│   ├── goal_*.py              # Goal trees and attempts
│   ├── hermes_runner.py       # Optional Hermes research tasks
│   └── workspace_layout.py    # Package layout repair for ship
├── agent.py                   # Shared ReAct loop
├── llm_interface.py           # Ollama / Grok / OpenAI / Claude / Gemini
├── scripts/
│   ├── run_ship_prove.sh|.ps1 # Controlled ship or main overnight
│   ├── build_capability_registry.py
│   └── sync_output_repo.py
├── cloud_setup.sh
├── COMMANDS.md                # Full ops reference
├── mission.yaml
├── constitution.yaml
└── _archive/                  # Earlier self-improvement stack (preserved)
```

---

## Design notes worth knowing

1. **Honest completion** — `complete` vs `mvp_complete` matter for dependencies and ship eligibility.  
2. **Soft defaults for legacy workspaces** — strict tests/structural gates are opt-in for the main loop; ship-prove prefers strict.  
3. **Ship bus isolation** — main-pipeline noise should not block ship exit; still **clear ship queues** before a controlled prove (use the run script).  
4. **Capabilities > copy-paste** — registry + `shared_libs/` reduce rebuild of the same primitives.  
5. **Training loop** — finished projects can feed `finetune_corpus/` with optional quality gates.

---

## Documentation

| Doc | Contents |
|---|---|
| **`COMMANDS.md`** | Flags, Ollama, cloud, polish, ship-prove, corpus, registry, resume |
| **`mission.yaml`** | Product mission and values |
| **`constitution.yaml`** | Governance / quality knobs |
| **`notes/`** | Design discussion notes (futures, not runtime config) |
| **`BACKLOG_AUDIT.md`** | Backlog / dependency audit snapshots (generated ops) |

---

## License / origin

Internal factory for autonomous idea implementation. Output projects live in the configured `PIPELINE_DIR` (often a separate git remote for cloud sync).
