# Phase 1 Tasks

- [ ] Task 1: Create project scaffold and package structure
  - What: Set up the Python package directory with __init__.py files, a pyproject.toml (or setup.py), and a top-level entry point module
  - Files: json_skill/__init__.py, json_skill/loader.py, json_skill/dispatcher.py, json_skill/runtime.py, pyproject.toml
  - Done when: The package can be imported with `import json_skill` without errors, and the directory structure is clean and logical

- [ ] Task 2: Implement the JSON skill loader
  - What: Build a loader module that reads a JSON skill file (with system_prompt, functions, examples keys) and validates its structure, returning a parsed skill object
  - Files: json_skill/loader.py
  - Done when: A JSON file matching the expected schema can be loaded and parsed into a structured Python object; invalid JSON or missing required keys raise a clear error

- [ ] Task 3: Implement the function dispatcher
  - What: Build a dispatcher that takes the parsed skill's function definitions and maps them to callable Python functions, handling the routing of tool calls to the correct implementations
  - Files: json_skill/dispatcher.py
  - Done when: The dispatcher can register functions from the skill's function definitions and route a call to the correct handler by name

- [ ] Task 4: Implement the runtime injector
  - What: Build a runtime module that takes a loaded skill and injects its system_prompt, registered functions, and examples into a model-compatible format (e.g., a dict with system_prompt, tools/functions list, and examples)
  - Files: json_skill/runtime.py
  - Done when: Calling the runtime with a loaded skill produces a properly structured payload ready to be sent to a model API

- [ ] Task 5: Wire up the top-level API and verify end-to-end
  - What: Create the public API surface in __init__.py (e.g., load_skill, run_skill) and write a quick smoke test that loads a sample skill JSON, dispatches a function call, and verifies the injected payload
  - Files: json_skill/__init__.py, tests/test_smoke.py, tests/sample_skill.json
  - Done when: A single script can load a sample skill, call a function through the dispatcher, and get the injected runtime payload — all without errors