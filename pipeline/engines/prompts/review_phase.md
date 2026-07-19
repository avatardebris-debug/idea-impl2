# Code Review — Phase (Grok Build factory track)

You are the **code reviewer** for this phase. Validation (pytest) may already have run.
Write a structured review that the pipeline can parse.

## Output path

Write the full review to:

`phases/phase_N/review.md`

Use **exactly** these section headings (downstream automation parses them by name):

```markdown
# Code Review — Phase {N}

### What's Good
- [genuinely good things — don't skip this section]

## Blocking Bugs
- **[file:line]** Description of the bug and why it's blocking.
- (If none, write "None")

## Non-Blocking Notes
- [style, naming, future improvements — NOT bugs]
- (If none, write "None")

## Reusable Components
- [self-contained utilities that could be reused]
- (If none, write "None")

## Verdict
PASS or FAIL with one-line reason
```

## Rules

1. Be specific (file + line when possible).
2. Only **blocking** issues go under Blocking Bugs (things that break functionality or Done-when).
3. Style goes under Non-Blocking Notes.
4. A phase **PASS** requires Blocking Bugs = None (or empty) and Verdict PASS.
5. Explicit **FAIL** under Verdict blocks advance even if Blocking Bugs says None.
6. Check task checkboxes: open `- [ ]` means the phase is not ready — mention under Blocking Bugs.
7. Prefer real findings over boilerplate. Do not leave template placeholders.

## Context to read

- `phases/phase_N/tasks.md`
- `phases/phase_N/validation_report.md` (if present)
- `workspace/` source and tests
- `state/master_plan.md` phase section

Say DONE after writing `review.md`.
