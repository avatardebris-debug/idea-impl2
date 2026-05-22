# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and core data models
  - What: Create the project directory structure and define the core data classes — Subgoal, DependencyGraph, and the main SubgoalGenerator class skeleton.
  - Files: subgoal_generator/__init__.py, subgoal_generator/models.py, subgoal_generator/generator.py
  - Done when: All modules import cleanly with no errors; models have fields for title, description, dependencies, and priority; generator class has a stub `generate(goal: str) -> list[Subgoal]` method.

- [ ] Task 2: LLM prompt builder and response parser
  - What: Implement the prompt construction logic that takes a high-level goal and produces an LLM-ready prompt, plus a parser that extracts structured subgoals (title, description, dependencies) from the LLM's text response.
  - Files: subgoal_generator/prompt_builder.py, subgoal_generator/parser.py
  - Done when: `build_prompt(goal)` returns a valid string prompt; `parse_response(text)` returns a list of Subgoal objects with correctly parsed titles, descriptions, and dependency lists for a known-format LLM response.

- [ ] Task 3: Core decomposition engine — wire LLM call end-to-end
  - What: Connect the prompt builder and parser inside the `generate()` method. Use a configurable LLM backend (default: OpenAI-compatible API via `openai` SDK) to call the model, send the prompt, and parse the response into subgoals. Make the LLM provider configurable via a simple interface.
  - Files: subgoal_generator/generator.py (complete), subgoal_generator/llm_client.py
  - Done when: Calling `generator.generate("learn Spanish")` returns a non-empty list of Subgoal objects with valid dependencies; the LLM provider can be swapped via a config parameter (e.g., `provider="openai"` or `provider="ollama"`).

- [ ] Task 4: Master ideas injection and output formatting
  - What: Implement the logic that formats each subgoal as a pipeline idea entry (YAML or JSON) and writes/appends it to `master_ideas.md`. Also implement a `to_pipeline_entry()` method on Subgoal for consistent formatting.
  - Files: subgoal_generator/output.py (new), subgoal_generator/models.py (add method)
  - Done when: `generator.generate()` can optionally write its output to a specified `master_ideas.md` file; each subgoal appears as a well-formed pipeline entry with title, description, dependencies, and priority fields.

- [ ] Task 5: CLI entry point and integration smoke test
  - What: Build a minimal CLI (`python -m subgoal_generator --goal "..."`) that invokes the generator and prints or saves the result. Write a smoke test that runs the full pipeline with a mock or real LLM call and verifies output structure.
  - Files: subgoal_generator/__main__.py, tests/test_smoke.py
  - Done when: `python -m subgoal_generator --goal "build a house"` runs end-to-end and outputs a list of subgoals; the smoke test passes, confirming importability and core functionality.