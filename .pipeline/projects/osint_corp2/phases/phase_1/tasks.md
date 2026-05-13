# Phase 1: Core Infrastructure & Tooling

## Goal
Build the foundational tooling layer: tools.py (agent tools), runner.py (seed/queue logic), message_bus.py, and the harness validation system.

## Tasks

- [ ] Task 1: tools.py — Agent Tool Functions
- [ ] Implement `read_file(path)` — read file contents, handle missing files gracefully
- [ ] Implement `write_file(path, content)` — create or overwrite files with parent dir creation
- [ ] Implement `append_file(path, content)` — append to existing files
- [ ] Implement `list_tree(path)` — recursive directory listing
- [ ] Implement `delete_file(path)` — remove files
- [ ] Implement `run_shell(cmd, cwd)` — execute shell commands with timeout, capture stdout/stderr
- [ ] Implement `search_in_files(pattern, path, glob)` — grep-like search across files
- [ ] Implement `patch_file(path, old, new)` — replace first occurrence of text in file
- [ ] Define `TOOLS` dict mapping tool names to function references
- [ ] Define `TOOL_SCHEMAS` list of JSON schema objects for each tool (for LLM function calling)
- [ ] Ensure all tools handle errors gracefully (return error strings, don't crash)

- [ ] Task 2: message_bus.py — Inter-Agent Communication
- [ ] Implement `Message` class with `from_agent`, `to_agent`, `type`, `payload` fields
- [ ] Implement `Message.create(from_agent, to_agent, type, payload)` — factory method
- [ ] Implement `MessageBus` class with `send(message)` and `receive(agent_name)` methods
- [ ] Implement `MessageBus.wait_for(agent_name, msg_type, timeout)` — blocking receive with timeout
- [ ] Implement `MessageBus.broadcast(type, payload, exclude=None)` — send to all agents
- [ ] Ensure message types are typed: `seed_idea`, `task_complete`, `review_request`, `review_feedback`, `harvest_ready`

- [ ] Task 3: runner.py — Pipeline Orchestration
- [ ] Implement `seed_from_master_list(bus)` — read master_ideas.md, parse ideas, check deps, seed ready ones
- [ ] Implement `_slugify(title)` — convert idea title to kebab-case slug
- [ ] Implement `_parse_requires(description)` — extract `requires: slug1, slug2` from idea description
- [ ] Implement `_check_deps_complete(slug, deps, pipeline_dir)` — verify all deps have status "complete" or "budget_exceeded"
- [ ] Implement `_build_dep_workspace_map(slug, deps, pipeline_dir)` — map dep slugs to workspace paths
- [ ] Implement `seed_idea(bus, title, idea, idea_slug, depends_on, dep_workspaces)` — create and send seed message
- [ ] Implement `process_queue(bus)` — poll queue, dispatch to appropriate agent
- [ ] Implement `_get_next_agent(slug)` — determine which agent handles a seeded idea based on status
- [ ] Implement `run_pipeline()` — main loop: seed → process → repeat until idle
- [ ] Implement `_is_idea_blocked(slug, pipeline_dir)` — check if idea is blocked by incomplete deps

- [ ] Task 4: harness validation system
- [ ] Implement `test_harness_capabilities.py` — validate all tools exist and work
- [ ] Implement `test_dependency_system.py` — validate dependency ordering logic
- [ ] Implement `validate_harness.py` — orchestrator that runs both test suites
- [ ] Implement `harvest.sh` — shell script to run validation, collect results, report status
- [ ] Ensure tests can run without Ollama (use stubs/mocks)
- [ ] Ensure tests can run without network access

- [ ] Task 5: Project structure & configuration
- [ ] Create `.pipeline/projects/osint_corp2/state/` directory
- [ ] Create `current_idea.json` with initial state (status: "phase_1_planning", phase: 1, total_phases: 6)
- [ ] Create `master_plan.md` with all 6 phases documented
- [ ] Create `master_ideas.md` with initial idea list (empty or with first idea)
- [ ] Create `.pipeline/shared_libs/` directory for shared code
- [ ] Create `.pipeline/queues/` directory for message queues
- [ ] Create `.pipeline/config.json` with pipeline configuration

## Acceptance Criteria
- [ ] All 8 tool functions work correctly (verified by test_harness_capabilities.py)
- [ ] Dependency system correctly blocks/unblocks ideas (verified by test_dependency_system.py)
- [ ] Message bus can send/receive messages between agents
- [ ] Pipeline can seed an idea from master_ideas.md and dispatch to idea_planner
- [ ] All tests pass without Ollama or network access
- [ ] Project structure is complete and consistent

## Notes
- Tools should be self-contained in tools.py — no external dependencies beyond stdlib
- Runner should be the single entry point for pipeline logic
- Message types should be documented and validated
- All file paths should use pathlib.Path for cross-platform compatibility