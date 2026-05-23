# Workflows and connectors

Compose existing capabilities without a full 7-phase build. Optional **self-hosted n8n** as addition or replacement backend.

## Concepts

| Term | Meaning |
|------|---------|
| **workflow** | Multi-step YAML; chains capabilities, shell commands, and/or n8n steps |
| **connector** | Same engine; usually 2–3 steps bridging two capabilities |
| **backend: native** | Run all steps in-process (default) |
| **backend: hybrid** | Native steps + `n8n_webhook` / `n8n_execute` steps |
| **backend: n8n** | POST input to n8n webhook or API; n8n owns execution |

Definitions live in `.pipeline/workflows/**/*.yaml` and register into the capability registry on rebuild.

## Quick start

```bash
# Register workflows into SQLite
python scripts/build_capability_registry.py

# Run native workflow (example: rebuild registry + backlog audit)
python scripts/run_workflow.py registry_refresh

# Via registry / agents
python -c "from pipeline.capability_tools import invoke_capability; print(invoke_capability('registry_refresh'))"

# Export for self-hosted n8n import
python scripts/run_workflow.py registry_refresh --export-n8n .pipeline/workflows/exports/registry_refresh.n8n.json

# Check n8n connectivity
export N8N_BASE_URL=http://localhost:5678
export N8N_API_KEY=your-key
python scripts/run_workflow.py --n8n-health
```

## Ideator bridges

When the ideator runs **generate_ideas** (30 ideas, 6 groups), **GROUP 4 (COMBINATION)** and **GROUP 5 (BRIDGE)** automatically:

1. Enrich `master_ideas.md` lines with `kind:connector requires: ... connector: <slug>`
2. Write `.pipeline/workflows/connectors/<slug>.yaml` (draft, skipped if file exists)
3. Log to `.pipeline/state/connector_synthesis_<timestamp>.md`
4. Re-register workflows in the capability registry

The ideator prompt requires explicit slugs for groups 4–5. Slugs are also inferred by matching project names in text.

After generation:

```bash
python scripts/build_capability_registry.py --list
python scripts/run_workflow.py bridge_some_slug --force
```

## YAML shape

```yaml
slug: my_chain
title: Human title
kind: workflow          # or connector
status: verified        # draft until tested
backend: native         # native | hybrid | n8n
requires:
  - upstream_capability_slug
purpose: One-line description
domains: [devops]

n8n:                    # optional; required for hybrid/n8n backends
  base_url: "${N8N_BASE_URL:-http://localhost:5678}"
  webhook_path: "/webhook/my-chain"
  workflow_id: ""       # optional: use API trigger instead of webhook
  api_key_env: N8N_API_KEY
  timeout_s: 300

steps:
  - id: step_a
    type: capability    # capability | shell | n8n_webhook | n8n_execute
    capability: some_verified_slug
    args: "--flag value"
    when: "{{ steps.prev.ok }}"   # optional
    save_as: prev
  - id: notify
    type: n8n_webhook
    body:
      event: step_done
      slug: my_chain
```

Templates: `{{ steps.step_id.ok }}`, `{{ input.args }}`, `{{ n8n.base_url }}`.

## n8n integration paths

### A — Addition (export + hybrid)

1. Author workflow in YAML with `backend: hybrid`.
2. `python scripts/run_workflow.py SLUG --export-n8n path.json`
3. Import JSON in n8n UI (Workflow → Import).
4. Activate workflow; copy webhook path into YAML `n8n.webhook_path`.
5. Native runner calls your n8n instance on `n8n_webhook` steps.

### B — Replacement (n8n owns run)

1. Set `backend: n8n` on workflow YAML.
2. Build equivalent flow in n8n (or import export).
3. `python scripts/run_workflow.py SLUG` → POST payload to webhook/API only.

### C — n8n calls pipeline

Exported JSON includes Execute Command nodes like:

`python scripts/run_workflow.py SLUG --step step_id --json-input '{{ ... }}'`

Point n8n at your repo cwd (self-hosted runner or SSH node).

## Ideator bridges

When an idea is glue between two slugs, prefer:

```markdown
- [ ] **Bridge X to Y** kind:connector requires:slug_a,slug_b
```

Add `.pipeline/workflows/connectors/bridge_x_y.yaml` instead of seeding a new 7-phase project.

## Registry

- Kinds: `workflow`, `connector`
- Entrypoint: `python scripts/run_workflow.py <slug>`
- `invoke_capability('<slug>')` runs workflows when `status: verified`
- `requires:` uses the same graph as projects (`capability_graph`)

## Environment

| Variable | Role |
|----------|------|
| `N8N_BASE_URL` | Self-hosted n8n root (default `http://localhost:5678`) |
| `N8N_API_KEY` | API key for `/api/v1/*` and authenticated webhooks |

See also: `.pipeline/docs/capability_registry.md`, `COMMANDS.md`.
