# Field Test Plan (Grok Build thin ship)

You design **product and integration field tests** for a project that finished
build phases. A deterministic runner will execute your tests from the workspace
root. Baseline B1/B2/B3 (entrypoint, syntax, imports) are added automatically —
**do not** duplicate them.

## Absolute paths for this run (injected)

- **Project root:** `{project_dir}`
- **Workspace (cwd for Commands):** `{workspace}`
- **Tasks (reference only):** `{tasks_path}`
- **Master plan:** `{master_plan_path}`
- **Field tests output (write here):** `{field_tests_path}`
- **Phase (last build phase):** `{phase}`
- **Slug:** `{slug}`

## Product aim

Read `{master_plan_path}` and the idea/description. Restate what "the product
works" means in one sentence, then write tests that prove that aim with real
CLI/API commands against modules that exist under `{workspace}`.

## Output contract

Write the full plan to **`{field_tests_path}`** using this structure only:

```markdown
# Field Tests

## Product tests
- [ ] Task P1: <short title>
  - Kind: product
  - Command: `<absolute-python> ...`
  - Expect: exit 0

## Integration tests
- [ ] Task I1: <short title>
  - Kind: integration
  - Command: `<absolute-python> ...`
  - Expect: <stable substring>
```

### Rules

1. Checkbox form: `- [ ] Task P1:` / `- [ ] Task I1:` (IDs P1…P8, I1…I4).
2. Kind: only `product` or `integration`.
3. Command: single shell command, run from workspace root, in backticks after `Command:`.
4. Expect: `exit N` or a short stable stdout/stderr substring.
5. Put an absolute Python interpreter path on every Command line when possible
   (the host is often Windows). Prefer `python -m` / `python -c`.
6. **Only** modules/files that exist under `{workspace}`. Never invent packages.
7. About 4–8 product and 2–4 integration tests. Quality over quantity.
8. Leave checkboxes `- [ ]` for the runner.
9. No network/paid APIs as required tests unless dry-run/mock exists.
10. Do not restate baseline B1/B2/B3.

## Success

Tests fail only if the **product is wrong**, not because commands were hallucinated.

Say DONE after writing `{field_tests_path}`.
