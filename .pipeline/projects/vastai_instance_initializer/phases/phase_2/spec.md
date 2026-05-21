## Phase 2: Multi-Instance Batch Execution & Preset Library

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

#