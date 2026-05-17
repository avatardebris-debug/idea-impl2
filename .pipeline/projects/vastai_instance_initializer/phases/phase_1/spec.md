## Phase 1: Single-Instance Preset & Launch (MVP)

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

#