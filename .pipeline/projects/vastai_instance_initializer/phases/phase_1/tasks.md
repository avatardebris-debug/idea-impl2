# Phase 1 Tasks

- [x] Task 1: Define preset schema and validation
  - What: Create the YAML preset file format and a Python validator that checks all required/optional fields against known VAST.ai instance parameters (GPU type, price cap, storage, SSH commands, environment variables, image, etc.)
  - Files: vastai_init/presets/schema.py, vastai_init/presets/__init__.py, vastai_init/presets/validator.py
  - Done when: Preset schema is defined with all VAST.ai-relevant fields; validator rejects invalid presets with clear error messages; validator accepts valid presets and returns a parsed config dict

- [x] Task 2: Build CLI entry point and preset loading
  - What: Implement the `vastai-init` CLI with a `launch` subcommand that accepts a preset file path, loads the preset, and passes the parsed config to the launcher. Use `typer` or `rich` for CLI framework.
  - Files: vastai_init/cli.py, vastai_init/__init__.py, setup.py or pyproject.toml
  - Done when: Running `vastai-init launch <preset-file>` from the terminal loads the preset without errors; invalid preset paths produce helpful error messages; CLI shows usage help with `--help`

- [x] Task 3: Implement VAST.ai API adapter and authentication
  - What: Build an API adapter module that handles authentication (API key from env var, config file, or interactive prompt) and calls the VAST.ai API to create a single instance using the preset parameters.
  - Files: vastai_init/api/adapter.py, vastai_init/api/auth.py, vastai_init/api/__init__.py
  - Done when: Adapter authenticates using an API key from VASTAI_API_KEY env var or saved config; adapter can create an instance on VAST.ai with preset parameters; adapter raises descriptive exceptions for auth failures, invalid parameters, and no-GPU-availability errors

- [x] Task 4: Implement instance polling and status reporting
  - What: Build a status polling loop that queries the VAST.ai API for the launched instance's state (queued, running, stopped, failed) and reports progress updates to the user until the instance reaches a terminal state.
  - Files: vastai_init/monitor/status.py, vastai_init/monitor/__init__.py
  - Done when: Polling loop reports status updates at regular intervals (e.g., every 10 seconds); loop exits when instance is running, stopped, or failed; user sees clear status messages in the terminal; polling respects a configurable timeout

- [x] Task 5: Implement session logging and connection details output
  - What: After a successful launch, output SSH connection details (SSH command, instance IP, port, etc.) and persist the full session metadata (preset used, instance ID, timestamps, status) to a local JSON session log file.
  - Files: vastai_init/launcher/session.py, vastai_init/utils/config.py
  - Done when: On success, the CLI prints the SSH connection command and instance details to stdout; a JSON session log file is written to ~/.vastai-init/sessions/ with instance ID, preset path, timestamps, and final status; session log is append-only (one entry per launch)

- [x] Task 6: Create sample preset file and verify end-to-end flow
  - What: Write a sample preset YAML file demonstrating the format and all common fields. Verify the complete flow: CLI loads preset → validates → authenticates → creates instance → polls → reports status → logs session.
  - Files: presets/default.yaml, presets/training-gpu.yaml, README.md
  - Done when: Sample preset files are valid and well-documented with comments explaining each field; README describes how to install, configure (API key), and run the tool; end-to-end flow works with a real or mocked VAST.ai API call