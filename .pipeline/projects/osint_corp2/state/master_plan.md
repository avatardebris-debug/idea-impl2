# Master Plan

## Pipeline Architecture

The OSINT Corp2 pipeline is a multi-agent system that processes ideas through a structured workflow:

### Agent Roles

1. **idea_planner** — Takes seed ideas and produces structured plans with phases, tasks, and dependencies
2. **executor** — Carries out tasks from the idea plan using the tool harness
3. **reviewer** — Validates outputs, checks for errors, provides feedback
4. **orchestrator** — Coordinates all agents, manages the pipeline loop

### Message Types

- `seed_idea` — Seeds a new idea for processing
- `task_complete` — Signals task completion
- `review_request` — Requests review of output
- `review_feedback` — Provides review feedback
- `harvest_ready` — Signals output is ready for harvest
- `error` — Reports an error
- `heartbeat` — Heartbeat signal

### Pipeline Phases

| Phase | Description | Ideas |
|-------|-------------|-------|
| 1 | Core Infrastructure | create-pipeline-infrastructure, define-agent-roles |
| 2 | Agent Implementation | implement-idea-planner, implement-executor, implement-reviewer, build-dependency-resolution, create-phase-management, implement-budget-tracking |
| 3 | Pipeline Assembly | build-pipeline-orchestrator, create-seed-idea-generation, implement-harvest-system, build-error-recovery |
| 4 | Monitoring & Config | create-pipeline-monitoring, implement-pipeline-configuration, build-pipeline-cli, create-integration-tests |
| 5 | Documentation & Deployment | document-pipeline-architecture, create-pipeline-examples, build-pipeline-deployment, final-pipeline-validation |

### Dependency Graph

```
Phase 1:
  create-pipeline-infrastructure (no deps)
  define-agent-roles (no deps)

Phase 2:
  implement-idea-planner → create-pipeline-infrastructure, define-agent-roles
  implement-executor → create-pipeline-infrastructure, define-agent-roles
  implement-reviewer → create-pipeline-infrastructure, define-agent-roles
  build-dependency-resolution → create-pipeline-infrastructure
  create-phase-management → create-pipeline-infrastructure
  implement-budget-tracking → create-pipeline-infrastructure

Phase 3:
  build-pipeline-orchestrator → implement-idea-planner, implement-executor, implement-reviewer, build-dependency-resolution, create-phase-management, implement-budget-tracking
  create-seed-idea-generation → build-pipeline-orchestrator
  implement-harvest-system → build-pipeline-orchestrator
  build-error-recovery → build-pipeline-orchestrator

Phase 4:
  create-pipeline-monitoring → build-pipeline-orchestrator, implement-budget-tracking
  implement-pipeline-configuration → build-pipeline-orchestrator
  build-pipeline-cli → build-pipeline-orchestrator, implement-pipeline-configuration
  create-integration-tests → build-pipeline-orchestrator, implement-pipeline-cli

Phase 5:
  document-pipeline-architecture → build-pipeline-orchestrator, create-integration-tests
  create-pipeline-examples → document-pipeline-architecture
  build-pipeline-deployment → document-pipeline-architecture, create-pipeline-examples
  final-pipeline-validation → build-pipeline-deployment, create-integration-tests
```

### Budget Limits

- Total budget: 1000000 tokens
- Per-idea budget: 100000 tokens
- Per-phase budget: 300000 tokens

### File Structure

```
osint_corp2/
├── state/
│   ├── master_ideas.md      # Master list of ideas
│   ├── master_plan.md       # This file
│   ├── current_idea.json    # Currently processing idea
│   └── current_phase.json   # Current phase state
├── workspace/
│   ├── tools.py             # Tool harness
│   ├── message_bus.py       # Inter-agent communication
│   ├── runner.py            # Pipeline orchestrator
│   ├── conftest.py          # Pytest config
│   ├── test_harness_capabilities.py
│   └── test_dependency_system.py
└── phases/
    └── phase_1/             # Phase outputs
```
