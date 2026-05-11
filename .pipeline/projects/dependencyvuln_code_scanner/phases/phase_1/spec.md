## Phase 1 — MVP: Core Parser + Single CVE Source + Basic Report

**Goal:** A working CLI that can scan a project, find dependencies, check them against one CVE source, and output a prioritized text/JSON report.

### Description

Build the foundational pipeline:
1. A dependency parser that handles **npm** (`package-lock.json` / `yarn.lock`) and **pip** (`requirements.txt` / `Pipfile.lock`).
2. A CVE data fetcher that queries the **OSV API** (free, no auth required) and caches results in a local SQLite store.
3. A vulnerability scorer that assigns a simple severity score (CVSS from OSV data).
4. A report generator that outputs a prioritized list in **JSON** and **plain text** formats.

### Deliverable

A runnable CLI (`depvuln`) with the following commands:
- `depvuln scan <path>` — Scans a project directory and prints results.
- `depvuln scan <path> --format json` — Outputs machine-readable JSON.
- `depvuln scan <path> --format text` — Outputs human-readable text (default).
- `depvuln scan <path> --cache` — Uses cached CVE data (faster, may be stale).

**Example output:**
```
[CRITICAL] requests==2.28.0  →  CVE-2023-32681  (CVSS 7.5)
  Uncontrolled resource consumption in requests library
  Fix: upgrade to requests>=2.31.0

[HIGH] flask==2.2.0  →  CVE-2023-30861  (CVSS 7.5)
  Cookie handling vulnerability in Flask
  Fix: upgrade to flask>=2.3.2

[LOW] pyyaml==5.4  →  CVE-2020-14343  (CVSS 5.3)
  Arbitrary code execution via yaml.load()
  Fix: use yaml.safe_load() or upgrade to pyyaml>=6.0
```

### Dependencies

- Phase 0 (none — this is the first phase).

### Success Criteria

1. ✅ `depvuln scan` runs against a sample npm project and returns at least 3 CVE findings.
2. ✅ `depvuln scan` runs against a sample pip project and returns at least 3 CVE findings.
3. ✅ JSON output is valid and parseable (no schema errors).
4. ✅ Text output is human-readable with severity, CVE ID, score, description, and fix version.
5. ✅ Local cache reduces subsequent scan time by ≥ 50%.
6. ✅ All tests pass (unit + integration).

### Tasks

- [ ] Set up project skeleton (package structure, `pyproject.toml`, CI config)
- [ ] Implement `DependencyParser` base class and `NpmParser` / `PipParser`
- [ ] Implement `CveFetcher` with OSV API integration and SQLite caching
- [ ] Implement `VulnScorer` (CVSS extraction + severity mapping)
- [ ] Implement `ReportGenerator` (JSON + text output)
- [ ] Implement CLI entry point with `click`
- [ ] Write unit tests for each component
- [ ] Write integration tests with sample projects
- [ ] Package as installable wheel (`pip install .`)
- [ ] Write README with usage examples

---