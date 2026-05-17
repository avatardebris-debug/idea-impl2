# Phase 1 Tasks

- [ ] Task 1: Scaffold Tauri + Rust + React project
  - What: Create the initial project structure with Tauri backend (Rust) and React frontend. Set up Cargo.toml with required dependencies (sqlx/rusqlite, reqwest, serde, tauri), tauri.conf.json, Vite + React entry point, and the app shell with navigation between Preset and Execution views.
  - Files: Cargo.toml, tauri.conf.json, src/main.rs, src/lib.rs, src-tauri/tauri.conf.json, src-tauri/capabilities/, package.json, vite.config.ts, src/App.tsx, src/index.css, .gitignore
  - Done when: `cargo tauri dev` launches a desktop window showing a basic layout with two tabs (Presets, Executions). The app compiles without errors and runs on macOS.

- [ ] Task 2: Implement SQLite database layer with preset and execution schemas
  - What: Create the Rust database module with schema definitions for presets, preset_configs, executions, and instance_statuses tables. Implement CRUD functions for presets (create, read, update, delete, list) and execution history recording (insert execution, update status, list history). Use rusqlite with migrations or sqlx for schema creation.
  - Files: src/db/mod.rs, src/db/schema.rs, src/db/presets.rs, src/db/executions.rs, src/db/instances.rs, src/db/models.rs
  - Done when: All four tables are created automatically on first run. Preset CRUD operations work correctly (insert, fetch by ID, update, delete, list all). Execution records can be inserted and queried. Data persists across app restarts. Unit tests pass for all CRUD paths.

- [ ] Task 3: Implement VAST AI API client and authentication
  - What: Build the Rust API client module that handles VAST AI REST API interactions. Implement API key storage in app config (stored in the Tauri config directory). Implement functions for: listing available GPU instances (with price/type filtering), creating a new instance with GPU filter and command, polling instance status, and sending terminal commands to a running instance. Add retry logic with exponential backoff for transient failures.
  - Files: src/api/mod.rs, src/api/vastai_client.rs, src/api/models.rs, src/api/auth.rs, src/config/app_config.rs
  - Done when: API key can be set and persisted in app config. `list_instances` returns GPU availability data. `create_instance` returns a valid instance ID when called with a valid API key. `get_instance_status` returns correct status. `send_terminal_command` delivers a command to a running instance. Retry logic handles 429/5xx errors gracefully.

- [ ] Task 4: Wire Tauri commands to connect backend to frontend
  - What: Create Tauri backend commands (pub extern "C" functions) that the React frontend calls via `@tauri-apps/api`. Implement commands for: `create_preset`, `update_preset`, `delete_preset`, `list_presets`, `get_preset`, `run_preset` (triggers instance creation + execution history record), `get_execution_history`, `get_execution_status`. Each command should handle errors and return structured JSON responses.
  - Files: src/commands/mod.rs, src/commands/preset_commands.rs, src/commands/execution_commands.rs, src/commands/config_commands.rs
  - Done when: All Tauri commands are registered in lib.rs. Each command can be called from the frontend and returns the expected data. Error cases (e.g., missing API key, invalid preset ID) return proper error messages. `run_preset` creates a VAST AI instance, records the execution, and returns the instance ID.

- [ ] Task 5: Build React Preset management UI
  - What: Create the Preset tab UI with: a form to create/edit presets (name, description, GPU type, max price, terminal command(s), delay between commands), a list/grid of saved presets with edit/delete buttons, and a "Run" button on each preset card. Use React Context + useReducer for state management. Connect to Tauri commands for all CRUD operations.
  - Files: src/components/PresetForm.tsx, src/components/PresetLibrary.tsx, src/components/PresetCard.tsx, src/hooks/usePresets.ts, src/contexts/PresetContext.tsx
  - Done when: User can create a preset with all fields and see it saved in the list. User can edit an existing preset and save changes. User can delete a preset and it disappears from the list. All changes persist across app restarts. The "Run" button on each preset card is wired to the `run_preset` Tauri command.

- [ ] Task 6: Build React Execution dashboard and real-time status display
  - What: Create the Execution tab UI that shows: a list of past executions with status (pending/running/completed/failed), instance ID, timestamp, and error message if any. When a preset is running, show real-time status updates (polling via Tauri command). Display the result of the most recent run (success/failure + instance ID). Include a simple execution history log.
  - Files: src/components/ExecutionDashboard.tsx, src/components/ExecutionCard.tsx, src/components/ExecutionStatus.tsx, src/hooks/useExecutions.ts, src/contexts/ExecutionContext.tsx
  - Done when: After clicking "Run" on a preset, the Execution tab shows the execution with status "pending" → "running" → "completed"/"failed". The instance ID is displayed on success. Failed executions show the error message. Execution history persists and is queryable. Status updates refresh automatically (polling every 5 seconds while running).