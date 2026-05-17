## Phase 1 — MVP: Single-Preset Instance Launcher

**Goal:** A working CLI tool that loads a single preset and launches one VAST.ai instance.

**Description:**
- Implement a preset file format (YAML/JSON) that captures all VAST.ai instance parameters: GPU type, price cap, storage size, SSH commands, environment variables, etc.
- Build a CLI command `vastai-init launch <preset-file>` that:
  1. Reads and validates the preset
  2. Authenticates with the VAST.ai API (supports API key or saved credentials)
  3. Calls the VAST.ai API to create a single instance
  4. Polls and reports the instance status until it's running
  5. Outputs connection details (SSH command, IP, etc.)
- Persist the launched instance metadata in a local session log.

**Deliverable:**
- A working CLI tool (`vastai-init`) that launches one instance from a preset.
- A sample preset file demonstrating the format.
- Session log output with instance details.

**Dependencies:**
- VAST.ai API documentation and Python SDK
- User's VAST.ai API key / authentication

**Success Criteria:**
- [ ] Can define a preset in YAML/JSON and validate it against known VAST.ai parameters
- [ ] Can launch a single instance via CLI with that preset
- [ ] Reports instance status updates until running
- [ ] Outputs SSH connection details on success
- [ ] Handles API errors gracefully (invalid preset, auth failure, no available GPUs)
- [ ] Logs the session to a local file (JSON)

**Estimated Effort:** 2–3 weeks

---

#