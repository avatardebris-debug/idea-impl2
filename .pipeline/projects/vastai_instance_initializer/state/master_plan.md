# VASTAI Instance Initializer — Master Implementation Plan

## 1. Idea Analysis

### Core Deliverable
A desktop application that lets users define, store, and execute **batch GPU instance provisioning** on VAST AI. Users configure terminal commands, timing, instance counts, and GPU preferences via a UI, then launch everything with one click. The tool manages the lifecycle of spawned instances and tracks their status.

### Problem Solved
VAST AI's CLI/API requires manual, repetitive commands to spin up GPU instances. Users who need multiple instances with specific terminal setups (e.g., cloning repos, installing dependencies, starting training jobs) must repeat work across instances. This tool automates that workflow.

### Key Capabilities
- **Preset Management**: Create, save, edit, delete command presets stored in a local database
- **Configuration**: GPU type/price filters, command sequences, inter-command/inter-instance delays
- **Batch Execution**: Launch N instances with configurable timing between each
- **Status Tracking**: Monitor running instances, view logs, stop/restart as needed
- **Cost Controls**: Estimated cost display, budget caps, per-instance limits

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Desktop App (Tauri)               │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Preset UI  │  │  Config UI   │  │  Runner   │  │
│  │  (React)    │  │  (React)     │  │  (Rust)   │  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬─────┘  │
│         │                 │                │        │
│  ┌──────▼────────────────▼────────────────▼─────┐  │
│  │           Core Business Logic (Rust)          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────┐  │  │
│  │  │ Preset   │  │ Scheduler│  │ VASTAI    │  │  │
│  │  │ Store    │  │ Engine   │  │ Client    │  │  │
│  │  │ (SQLite) │  │          │  │ (API)     │  │  │
│  │  └──────────┘  └──────────┘  └───────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│                  VAST AI REST API                    │
│         (Instance creation, listing, status)         │
└─────────────────────────────────────────────────────┘
```

### Tech Stack Decisions
| Layer | Choice | Rationale |
|-------|--------|-----------|
| UI Framework | Tauri + React | Lightweight native desktop app, small bundle size |
| Backend | Rust | Safe, fast, excellent SQLite support (sqlx/rusqlite) |
| Database | SQLite (embedded) | Zero-config, single-file, perfect for local presets |
| VAST AI Integration | REST API client | Official API; async HTTP via reqwest |
| State Management | React Context + useReducer | Simple, no extra deps for MVP |

### Data Model (SQLite)
```sql
-- Presets (user-defined configurations)
CREATE TABLE presets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Preset configurations (JSON blob for flexibility)
CREATE TABLE preset_configs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    preset_id   INTEGER REFERENCES presets(id) ON DELETE CASCADE,
    gpu_type    TEXT,           -- e.g. "RTX 4090", "A100"
    max_price   REAL,           -- $/hr budget
    command     TEXT NOT NULL,  -- Shell command to run on instance
    delay_ms    INTEGER DEFAULT 0, -- delay between commands on same instance
    instance_count INTEGER DEFAULT 1,
    instance_delay_ms INTEGER DEFAULT 0, -- delay between instances
    region      TEXT,           -- preferred region
    custom_filters TEXT,        -- JSON: additional VAST AI filter params
    UNIQUE(preset_id)
);

-- Execution history (audit trail)
CREATE TABLE executions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    preset_id       INTEGER REFERENCES presets(id),
    preset_name     TEXT,
    status          TEXT NOT NULL, -- 'running', 'completed', 'failed'
    started_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME,
    instance_ids    TEXT,         -- JSON array of VAST AI instance IDs
    error_message   TEXT,
    estimated_cost  REAL
);

-- Instance status tracking
CREATE TABLE instance_statuses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id    INTEGER REFERENCES executions(id),
    vastai_instance TEXT NOT NULL, -- VAST AI instance ID
    status          TEXT NOT NULL, -- 'pending', 'running', 'completed', 'failed', 'stopped'
    command_output  TEXT,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Phase Breakdown

---

### Phase 1: Single-Instance Preset & Launch (MVP)

**Goal:** A user can define a preset with commands and GPU settings, save it, and launch **one** instance with that configuration.

**Scope:**
- SQLite database with preset CRUD (create, read, update, delete)
- UI form to configure a single preset:
  - Preset name & description
  - GPU type / price filter
  - Terminal command(s) to execute
  - Delay between commands
- "Run" button that calls VAST AI API to create one instance
- Display execution status (pending → running → completed/failed)
- Basic execution history log

**Deliverable:**
A working desktop app where a user can:
1. Create a named preset with GPU + command config
2. Save it to the local SQLite database
3. Click "Run" to provision one GPU instance on VAST AI
4. See the result (success/failure + instance ID)

**Dependencies:**
- None (foundation phase)

**Success Criteria:**
- [ ] Preset can be created, saved, loaded, edited, and deleted
- [ ] Preset data persists across app restarts (SQLite)
- [ ] VAST AI API integration creates an instance with correct GPU filter
- [ ] Terminal command is sent to the instance's terminal
- [ ] User sees execution status updates in real-time
- [ ] Execution history is recorded in the database
- [ ] App builds and runs on macOS and Windows

**Risks & Mitigations:**
| Risk | Mitigation |
|------|-----------|
| VAST AI API rate limits | Implement retry with exponential backoff |
| VAST AI API auth complexity | Use API key stored in app config; document setup clearly |
| GPU availability | Show real-time availability warnings from VAST AI API |
| Tauri cross-platform issues | Test on macOS first, then Windows; use cross-platform crates |

---

### Phase 2: Multi-Instance Batch Execution & Preset Library

**Goal:** Users can launch **multiple instances** from a preset with configurable timing, and manage a library of presets.

**Scope:**
- Multi-instance support: configure `instance_count` and `instance_delay_ms` in presets
- Batch scheduler engine that:
  - Spawns instances sequentially (or in configurable parallel batches)
  - Waits the configured delay between each instance
  - Tracks per-instance status independently
- Preset library UI:
  - Grid/list view of all saved presets
  - Duplicate preset (fork)
  - Import/export presets as JSON files
- Execution dashboard:
  - Real-time progress bar (X of N instances running)
  - Per-instance status cards (pending / running / completed / failed)
  - Expandable terminal output per instance
- Stop/pause batch execution mid-flight

**Deliverable:**
A user can:
1. Set a preset to launch 5 instances with 30-second delays between each
2. Click "Run Batch" and watch progress in real-time
3. See individual instance statuses and terminal output
4. Stop the batch at any point
5. Manage a library of presets with import/export

**Dependencies:**
- Phase 1 (database schema, VAST AI client, preset CRUD, basic execution flow)

**Success Criteria:**
- [ ] Batch of N instances launches with correct timing
- [ ] Each instance tracks its own status independently
- [ ] User can stop a running batch (cancels remaining instances)
- [ ] Preset library supports 100+ presets without UI lag
- [ ] Import/export presets as JSON works correctly
- [ ] Execution dashboard updates in real-time (< 2s refresh)
- [ ] No race conditions when launching parallel instances

**Risks & Mitigations:**
| Risk | Mitigation |
|------|-----------|
| Concurrent API calls overwhelm VAST AI | Rate-limit concurrent requests; queue-based scheduler |
| Memory usage with many instances | Stream terminal output; don't buffer everything in memory |
| Batch cancellation leaves orphaned instances | Implement cleanup on stop; mark instances as "stopped by user" |
| Preset JSON schema drift | Version the preset schema; migrate on load |

---

### Phase 3: Instance Management, Cost Controls & Templates

**Goal:** Full lifecycle management of provisioned instances with cost awareness and reusable templates.

**Scope:**
- **Instance lifecycle management:**
  - List all instances from active executions
  - Stop, restart, or delete individual instances
  - View live terminal output (WebSocket or polling)
  - Copy instance terminal commands
- **Cost controls:**
  - Estimated cost per preset (based on GPU price × expected duration)
  - Budget cap per batch execution
  - Real-time cost accumulator during batch run
  - Warning alerts when approaching budget limits
- **Template system:**
  - Pre-built templates (e.g., "PyTorch Training", "LLM Fine-tuning", "Docker Dev Environment")
  - Template gallery with community-shared presets
  - One-click template application
- **Advanced scheduling:**
  - Region-based instance selection (prefer cheapest/available region)
  - GPU availability checker before launch
  - Retry failed instances automatically (configurable max retries)
- **Notifications:**
  - System notifications on batch completion/failure
  - Email/webhook alerts (optional)

**Deliverable:**
A user can:
1. See estimated costs before launching a batch
2. Set a $10 budget cap and get warned at $8
3. Manage all provisioned instances from one view
4. Stop/restart individual instances
5. Use pre-built templates to get started quickly
6. Get notified when batches complete or fail

**Dependencies:**
- Phase 2 (batch scheduler, preset library, execution tracking)

**Success Criteria:**
- [ ] Cost estimation within 10% of actual VAST AI pricing
- [ ] Budget cap enforcement (stops batch when exceeded)
- [ ] Instance management (stop/restart/delete) works reliably
- [ ] Live terminal output updates in < 3 seconds
- [ ] At least 5 pre-built templates included
- [ ] Notifications deliver within 5 seconds of event
- [ ] Retry logic handles transient failures gracefully

**Risks & Mitigations:**
| Risk | Mitigation |
|------|-----------|
| VAST AI pricing changes frequently | Cache pricing data; allow manual override; show "last updated" timestamp |
| Live terminal output reliability | Fallback to polling if WebSocket unavailable; queue output messages |
| Orphaned instances costing money | Auto-detect and alert on instances older than expected; one-click cleanup |
| Template security (arbitrary command execution) | Sanitize template inputs; warn users before running arbitrary commands |

---

## 4. File Structure

```
vastai-instance-initializer/
├── Cargo.toml
├── src/
│   ├── main.rs                 # Tauri app entry point
│   ├── lib.rs                  # Rust library root
│   ├── db/
│   │   ├── mod.rs
│   │   ├── schema.rs           # SQL schema definitions
│   │   ├── presets.rs          # Preset CRUD operations
│   │   ├── executions.rs       # Execution history operations
│   │   └── instances.rs        # Instance status operations
│   ├── api/
│   │   ├── mod.rs
│   │   ├── vastai_client.rs    # VAST AI REST client
│   │   ├── models.rs           # API response models
│   │   └── auth.rs             # API key management
│   ├── engine/
│   │   ├── mod.rs
│   │   ├── scheduler.rs        # Batch execution scheduler
│   │   ├── instance_manager.rs # Per-instance lifecycle
│   │   └── cost_tracker.rs     # Cost estimation & tracking
│   └── config/
│       ├── mod.rs
│       └── app_config.rs       # App settings, API key storage
├── src-tauri/
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   └── capabilities/
├── src/
│   └── components/             # React UI components
│       ├── PresetForm.tsx
│       ├── PresetLibrary.tsx
│       ├── ExecutionDashboard.tsx
│       ├── InstanceManager.tsx
│       ├── CostControls.tsx
│       └── TemplateGallery.tsx
├── src/
│   └── hooks/
│       ├── usePresets.ts
│       ├── useExecutions.ts
│       └── useInstances.ts
├── tests/
│   ├── db_test.rs
│   ├── scheduler_test.rs
│   └── api_mock_test.rs
└── docs/
    ├── setup.md                # Setup & API key guide
    └── templates/              # Pre-built template JSON files
```

---

## 5. Risks & Mitigations (Cross-Phase)

| Risk | Severity | Mitigation |
|------|----------|-----------|
| VAST AI API changes/breaks | High | Abstract API layer; integration tests against mock server |
| GPU availability fluctuations | Medium | Show real-time availability; allow flexible GPU type selection |
| User loses API key | Medium | Secure key storage (OS keychain); export/import backup |
| App crashes during batch | Medium | Write execution state to disk before each step; resume on restart |
| Large terminal output fills disk | Low | Stream output to temp files with rotation; limit per-instance output size |
| Cross-platform UI inconsistencies | Low | Use CSS-in-JS or Tailwind; test on both platforms in CI |

---

## 6. Milestones & Timeline Estimate

| Phase | Duration | Key Milestone |
|-------|----------|---------------|
| Phase 1 | 2-3 weeks | MVP: single instance launch with preset |
| Phase 2 | 3-4 weeks | Batch execution + preset library |
| Phase 3 | 3-4 weeks | Cost controls + instance management + templates |
| **Total** | **8-11 weeks** | **Production-ready application** |

---

## 7. Open Questions

1. **VAST AI API authentication:** Does VAST AI support API keys, or is OAuth required? Need to verify.
2. **Terminal access:** How do we send commands to a VAST AI instance's terminal? Via their API terminal endpoint or SSH?
3. **Webhook vs polling:** Does VAST AI support webhooks for instance status, or do we need to poll?
4. **Template distribution:** Should templates be bundled with the app, or fetched from a remote registry?
5. **Multi-account:** Does a user need to support multiple VAST AI accounts simultaneously?
