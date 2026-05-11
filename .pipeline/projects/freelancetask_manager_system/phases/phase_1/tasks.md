# Phase 1 Tasks

- [ ] Task 1: Core Domain Models
  - What: Define the foundational data models — ServiceOffering, ClientProfile, and pipeline state serialization. These models are the foundation that all downstream components depend on.
  - Files: core/service_offering.py, core/client_profile.py, core/state.py
  - Done when: ServiceOffering model enforces required fields (title, description, deliverables, timeline, pricing) via validation; ClientProfile model captures name, email, preferences, and history; state module provides serialize/deserialize for pipeline state; all three models have unit tests covering construction, validation errors, and serialization round-trips.

- [ ] Task 2: SOP Engine — Template Manager, Scope Extractor, Pricing Calculator
  - What: Build the SOP engine that manages service offering templates (CRUD, versioning, validation), extracts deliverables and milestones from SOPs, and computes tiered pricing from SOP inputs.
  - Files: sop_engine/template_manager.py, sop_engine/scope_extractor.py, sop_engine/pricing_calculator.py
  - Done when: template_manager supports create/list/edit/delete SOPs with versioning and enforces minimum field validation; scope_extractor correctly identifies all deliverables and milestones from an SOP's deliverables list; pricing_calculator produces correct tiered pricing (e.g., basic/standard/premium) from SOP pricing inputs; all three modules have unit tests covering happy paths, edge cases, and validation failures.

- [ ] Task 3: Proposal Engine — Builder and Renderer
  - What: Build the proposal engine that assembles a client-ready proposal from an SOP + client profile, and renders it in Markdown and HTML formats.
  - Files: proposal_engine/proposal_builder.py, proposal_engine/template_renderer.py
  - Done when: proposal_builder combines SOP scope/deliverables/pricing with client profile data to produce a structured proposal object; template_renderer outputs the proposal as both Markdown and HTML with proper formatting (sections for overview, scope, timeline, pricing, terms); unit tests cover proposal assembly with various client profiles and rendering to both formats.

- [ ] Task 4: CLI Entry Point
  - What: Build the command-line interface that exposes SOP and proposal commands so users can interact with the system from the terminal.
  - Files: cli/main.py
  - Done when: CLI supports `ftm sop create --file service.json` (creates SOP from JSON file), `ftm sop list` (lists all SOPs), `ftm sop edit` (edits an existing SOP), `ftm proposal generate --sop <name> --client <name> --format <markdown|html>` (generates a proposal); CLI commands are tested via integration tests that invoke the CLI and verify output.

- [ ] Task 5: Benchmark Data and Integration Tests
  - What: Create sample benchmark data files and write integration tests that validate the full pipeline from SOP creation through proposal generation.
  - Files: benchmarks/sample_sops.json, benchmarks/sample_clients.json, tests/test_integration.py
  - Done when: sample_sops.json contains at least 3 realistic SOP examples covering different service types; sample_clients.json contains at least 3 realistic client profiles; integration tests exercise the full flow (create SOP → extract scope → compute pricing → generate proposal → render) and assert correctness of each step.

- [ ] Task 6: Phase 1 Validation and Smoke Tests
  - What: Run the full test suite, verify all success criteria are met, and confirm CLI commands work end-to-end with the benchmark data.
  - Files: tests/test_sop_engine.py, tests/test_proposal_engine.py, tests/test_client_matcher.py (stub), tests/test_contract_engine.py (stub), tests/test_integration.py
  - Done when: All unit and integration tests pass; CLI commands `ftm sop create --file benchmarks/sample_sops.json`, `ftm sop list`, and `ftm proposal generate --sop my-sop --client john --format html` execute successfully and produce correct output; all success criteria checkboxes from the Phase 1 spec are satisfied.