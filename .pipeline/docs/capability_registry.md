# Capability registry (fork)

Phased catalog of what the pipeline can reuse. **Legacy mode** preserves pre-fork behavior.

## Modes

| Mode | CLI | Behavior |
|------|-----|----------|
| **Capabilities** (default) | `python pipeline/runner.py --from-list` | Registry via `context_cache`; executor tools when `PIPELINE_CAPABILITY_TOOLS=1` |
| **Legacy** | `python pipeline/runner.py --from-list --legacy` | No registry build; `reusable_tools.md` + `shared_libs/` only |

Environment: `PIPELINE_LEGACY=1` (set for agent subprocesses when `--legacy` is used).

## Artifacts

| Path | Role |
|------|------|
| `.pipeline/state/capability_registry.sqlite` | Source of truth |
| `.pipeline/state/capability_edges` table | Phase 5 dependency graph |
| `.pipeline/state/CAPABILITIES.md` | Generated human/agent view |
| `.pipeline/state/capability_overrides.yaml` | Phase 7 manual requires/status fixes |
| `scripts/capability_graph.dot` | Optional Graphviz export |

## Commands

```bash
python scripts/build_capability_registry.py
python scripts/build_capability_registry.py --list --domain video
python scripts/build_capability_registry.py --graph
python scripts/build_capability_registry.py --blocked
python scripts/gen_backlog_audit.py   # includes "Blocked downstream" section
python health_check.py                # stale requires: warnings
```

## Phase status

| Phase | Status | Deliverable |
|-------|--------|-------------|
| 0 | Done | Schema + this doc |
| 1 | Done | `build_capability_registry.py` + SQLite scan |
| 2 | Done | `context_cache` + executor injection |
| 3 | Done | `capability_router.py` — goal_decomposer + phase_planner |
| 4 | Done | `list_capabilities`, `invoke_capability`, etc. |
| 5 | Done | `capability_edges`, graph rebuild, router blocks unmet `requires:` |
| 6 | Done | Hermes `register_hermes_capability`; shared_lib draft→verified on project complete; `capability_gap` branches |
| 7 | Done | Metrics JSONL, `capability_metrics_report.py`, prune orphans on rebuild, overrides YAML |
| 8 | Done | Cursor MCP + multi-instance JSON/SQLite sync |

## Phase 8 — MCP (Cursor)

Project config: `.cursor/mcp.json`

```bash
pip install mcp>=1.2.0
# Reload: Cursor Settings → Tools & MCP
python scripts/mcp_idea_capabilities_server.py   # stdio test (needs SDK)
```

| Tool | Purpose |
|------|---------|
| `list_capabilities` | Verified/draft catalog |
| `describe_capability` | One slug metadata |
| `suggest_capabilities` | Router + FTS + deps |
| `invoke_capability` | Safe CLI entrypoint |
| `registry_blocked_ideas` | master_ideas blocked by requires: |

Legacy fallback: `scripts/mcp_capability_server.py` (one JSON line per request).

## Phase 8 — Multi-instance sync

| Mode | When |
|------|------|
| **JSON merge** (default) | Git-friendly; merge newer `updated_at` per row |
| **SQLite replace** | Fast full copy from another machine |
| **Zip auto** | `extract.py` embeds export; `import_zip.py` merges on import |

```bash
# Cloud instance A (before extract)
export CAPABILITY_SYNC_INSTANCE=vast-cloud
python scripts/sync_capability_registry.py export --metrics

# Local / instance B
git pull   # if capability_registry_export.json committed
python scripts/sync_capability_registry.py merge
# OR unzip + import_zip.py --yes (merges export from zip)

# Nuclear option: copy entire DB
python scripts/sync_capability_registry.py replace --sqlite .pipeline/state/capability_registry.sqlite
```

Files:
- `.pipeline/state/capability_registry_export.json` (primary)
- `capability_registry_export.json` at repo root (`--copy-root` for git)
- `capability_registry.sqlite` included in pipeline_extract zip

## Phase 6 add-ons

- **FTS search** (`capability_search.py`) — Porter-stemmed index on title/purpose; router merges FTS + keyword scores
- **Bandit boost** — invoke success rate from `capability_metrics.jsonl` nudges routing
- **Capability gaps queue** — `.pipeline/state/capability_gaps.md`; manager category `CAPABILITY_GAP`; seeded before `master_ideas.md`
- **Auto-rebuild** — `import_zip.py` after import; `extract.py --rebuild-registry`

## Phase 5 — dependency graph

Edges built from:

- `master_ideas.md` `requires:` lines
- `.pipeline/goals/*.json` branch `requires`
- Project `depends_on` in `current_idea.json`
- `capability_overrides.yaml`

**Router:** capabilities with unmet prerequisites are **not suggested** (unless `include_blocked=True`).

**Exit checks:**

- `movie_player` only routable when `ai_movie_generation_suite` is verified
- `python scripts/build_capability_registry.py --blocked` lists blocked master_ideas rows

## Phase 6 — tool lifecycle

1. Reviewer lists **Reusable Components** → `_extract_shared_libs` → `register_shared_lib_capability` (draft)
2. Project completes → `refresh_capability` (verified) + `promote_draft_shared_libs_for_project`
3. Hermes `--hermes` line with critic **achieved** → `register_hermes_capability` (`kind=hermes_task`, verified)
4. `goal_decomposer` `capability_gap` branches → reuse verified slug via `requires:` or queue build line
5. Agent tools log route/suggest/invoke to `capability_metrics.jsonl`

## Phase 7 — operations

| Activity | Command |
|----------|---------|
| Rebuild registry + edges | `python scripts/build_capability_registry.py` |
| After zip import / weekly | Same + `extract.py --rebuild-truth` |
| Prune deprecated | Rebuild drops missing projects; delete stale sqlite rows manually |
| Human override | Edit `capability_overrides.yaml` then rebuild |
| Backlog blocked view | `python scripts/gen_backlog_audit.py` |

## Tool lifecycle (COMMANDS summary)

See `COMMANDS.md` § Capability registry for runner flags and agent tools.

## Workflows and connectors (Phase 9)

Multi-step composition in `.pipeline/workflows/**/*.yaml`. Native runner by default; optional self-hosted **n8n** (`backend: n8n|hybrid`, export, webhooks).

```bash
python scripts/run_workflow.py registry_refresh
python scripts/run_workflow.py registry_refresh --export-n8n exports/registry_refresh.n8n.json
python scripts/run_workflow.py --n8n-health
```

Full doc: `.pipeline/docs/workflows.md`
