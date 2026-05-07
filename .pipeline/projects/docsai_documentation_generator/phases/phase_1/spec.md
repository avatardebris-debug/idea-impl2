## Phase 1 — MVP: API Spec Generator

### Description
Build the core pipeline engine and the API specification generator. This is the smallest useful thing: a tool that parses source code, extracts function/class signatures, and produces a structured API spec in YAML/JSON.

### Deliverable
- A working CLI (`docsai spec`) that takes a source directory and outputs a structured API spec file.
- AST parser supporting Python and TypeScript.
- Configurable output format (YAML or JSON).
- Basic LLM integration: the spec includes auto-generated docstrings/comments extracted from code.

### Dependencies
- None (foundation phase).

### Success Criteria
- [ ] `docsai spec ./my_project` produces a valid YAML/JSON API spec with all public functions/classes.
- [ ] Supports Python and TypeScript source files.
- [ ] Output includes function signatures, parameter types, return types, and docstrings.
- [ ] Config file (`docsai.yaml`) controls output format and target language.
- [ ] End-to-end test passes on a sample project.

---