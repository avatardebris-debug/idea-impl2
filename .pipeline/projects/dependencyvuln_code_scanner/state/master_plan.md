# DependencyVuln Code Scanner — Master Implementation Plan

## Overview

**Idea:** A CLI utility that audits project dependency trees, cross-references CVE databases, and outputs prioritized remediation reports.

**Core Deliverable:** A production-ready CLI tool (`depvuln`) that can be run against any project directory to discover known vulnerabilities in its dependencies, prioritize them by exploitability/severity, and produce actionable remediation reports.

---

## Architecture Notes

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      depvuln CLI                            │
├──────────────┬────────────────┬──────────────┬─────────────┤
│  Dependency  │   CVE Bridge   │  Scorer &    │  Report    │
│  Parsers     │   (Data Layer) │  Prioritizer │  Generators│
│              │                │              │            │
│ • npm        │ • NVD API      │ • CVSS v3.1  │ • JSON     │
│ • pip        │ • OSV API      │ • Exploit    │ • Markdown │
│ • Maven      │ • Local cache  │   availability│ • HTML     │
│ • Cargo      │ • Rate-limit   │ • Age-based  │ • SARIF    │
│ • Go mod     │   debouncing   │   decay      │ • SARIF    │
│ • Podfile    │                │              │            │
└──────────────┴────────────────┴──────────────┴─────────────┘
```

### Key Design Decisions

1. **Plugin-based parser architecture** — Each package manager is a pluggable parser. New formats can be added without touching core logic.
2. **Dual CVE data sources** — OSV (free, no API key) as primary; NVD (authoritative) as secondary. Both are cached locally to avoid rate-limiting.
3. **CVSS-based prioritization** — Uses CVSS v3.1 scores, exploit availability, and package age to rank findings.
4. **No database required** — All state is file-based (JSON cache, SQLite for optional local DB).
5. **CLI-first** — Designed for `depvuln scan ./project` and CI/CD integration.

### Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.10+ | Rich ecosystem for parsing, JSON, HTTP |
| Dependency parsing | `pip-tools`, `pkginfo`, `toml`, `xmltodict` | Mature, well-tested |
| CVE data | OSV API + NVD API | Free tiers, comprehensive coverage |
| Serialization | `rich`, `jinja2` | Pretty CLI output, templated reports |
| CLI framework | `click` or `argparse` | Standard, extensible |
| Caching | SQLite (`sqlite3` stdlib) | Zero-config local cache |

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| CVE API rate limits | High | Aggressive local caching with TTL; request batching |
| Slow scans on large repos | Medium | Parallel parsing; progress bars; `--fast` flag for skip |
| False positives (unaffected versions) | High | Version range matching (not just equality); user override flags |
| Missing CVE data for niche packages | Medium | Fallback to NVD; user can supply custom advisory files |
| Dependency resolution complexity | Medium | Delegate to native tools (`npm ls`, `pipdeptree`, `mvn dependency:tree`) |
| Transitive dependency explosion | Medium | Depth-limited scanning (configurable); tree visualization in Phase 3 |

---

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

## Phase 2 — Multi-Format Support + Richer Data + Prioritized Reports

**Goal:** Expand coverage to all major package ecosystems, enrich vulnerability data, and produce professional-grade reports.

### Description

Build on Phase 1 foundations:
1. **Expand dependency parsers** to support Maven (`pom.xml`), Cargo (`Cargo.toml`), Go modules (`go.mod`), and CocoaPods (`Podfile`).
2. **Integrate NVD API** alongside OSV for broader CVE coverage. Merge deduplicated findings.
3. **Enhance the scorer** with:
   - CVSS v3.1 vector parsing
   - Exploit availability weighting
   - Package age decay (newer packages = higher risk)
   - Transitive dependency depth weighting
4. **Add report formats**: Markdown, HTML (with inline CSS), and SARIF (for GitHub/GitLab integration).
5. **Add a `--diff` mode** to compare two scans and show newly discovered vulnerabilities.
6. **Add a `--fix-suggest` mode** that generates a diff/patch for the dependency file.

### Deliverable

Extended CLI with new commands:
- `depvuln scan <path> --format markdown` — Markdown report.
- `depvuln scan <path> --format html` — Styled HTML report.
- `depvuln scan <path> --format sarif` — SARIF output for CI tools.
- `depvuln scan <path> --ecosystems npm,pip,maven,cargo,go,podfile` — Select ecosystems.
- `depvuln diff <scan1.json> <scan2.json>` — Compare two scans.
- `depvuln suggest-fix <path>` — Generate dependency upgrade suggestions.

**Enhanced output example (HTML):**
- Severity-colored table with CVE details.
- Clickable links to CVE pages and fix PRs.
- Summary statistics (total deps, vulnerable, critical/high/medium/low counts).

### Dependencies

- Phase 1 (parsers, CVE fetcher, scorer, report generator must all exist).

### Success Criteria

1. ✅ All 6 ecosystems (npm, pip, maven, cargo, go, podfile) produce correct dependency lists.
2. ✅ NVD + OSV data is merged correctly with deduplication.
3. ✅ Prioritization order is correct: CRITICAL > HIGH > MEDIUM > LOW.
4. ✅ HTML report renders correctly in a browser with all data visible.
5. ✅ SARIF output passes `sarif-lint` validation.
6. ✅ `--diff` mode correctly identifies new vs. resolved vulnerabilities.
7. ✅ `--fix-suggest` produces valid dependency file diffs.
8. ✅ All Phase 1 tests still pass.

### Tasks

- [ ] Implement `MavenParser` (pom.xml XML parsing)
- [ ] Implement `CargoParser` (TOML parsing)
- [ ] Implement `GoParser` (go.mod parsing)
- [ ] Implement `PodfileParser` (Podfile parsing)
- [ ] Implement `NvdFetcher` (NVD API integration)
- [ ] Implement `CveDataMerger` (OSV + NVD deduplication)
- [ ] Enhance `VulnScorer` with exploit/age/depth weighting
- [ ] Implement `MarkdownReportGenerator`
- [ ] Implement `HtmlReportGenerator`
- [ ] Implement `SarifReportGenerator`
- [ ] Implement `DiffReporter`
- [ ] Implement `FixSuggester`
- [ ] Extend CLI with new commands and flags
- [ ] Write integration tests for new ecosystems
- [ ] Write integration tests for new report formats
- [ ] Update documentation

---

## Phase 3 — Production Hardening + CI/CD + Advanced Features

**Goal:** Make the tool production-ready with CI integration, real-time monitoring, dependency tree visualization, and a plugin system.

### Description

Polish and extend the tool for enterprise use:
1. **CI/CD integration**:
   - GitHub Action (`depvuln-action`)
   - GitLab CI template
   - Jenkins pipeline step
   - Exit-code-based gating (fail on CRITICAL/HIGH)
2. **Dependency tree visualization**:
   - ASCII tree view (`depvuln tree <path>`)
   - Graphviz DOT output for large projects
3. **Plugin system**:
   - Custom CVE source plugins (YAML/JSON advisory files)
   - Custom parser plugins (Python entry points / setuptools)
   - Custom report template plugins
4. **Advanced features**:
   - `--watch` mode for continuous scanning
   - `--exclude` patterns for known-false-positives
   - `--config` file for project-level settings
   - `--export-db` for long-term trend tracking
5. **Performance**:
   - Parallel CVE lookups
   - Incremental scanning (only scan changed deps)
   - Configurable depth limits
6. **Security**:
   - Verify CVE data signatures
   - Audit log of all scan operations

### Deliverable

A fully-featured, production-grade CLI tool with:
- `depvuln tree <path>` — Visual dependency tree with vulnerability annotations.
- `depvuln watch <path>` — Continuous monitoring mode.
- `depvuln config init` — Generate `.depvulnrc` config file.
- `depvuln export-db <path> <output.db>` — Export scan history.
- GitHub Action + GitLab CI template.
- Plugin documentation and example plugins.

### Dependencies

- Phase 2 (all parsers, CVE data, scorers, and report generators).

### Success Criteria

1. ✅ GitHub Action runs `depvuln` in a PR and posts results as a comment.
2. ✅ `depvuln tree` renders a correct dependency tree with vuln annotations.
3. ✅ Plugin system allows a third-party to add a new parser without modifying core code.
4. ✅ `--watch` mode detects new vulnerabilities in real-time.
5. ✅ Incremental scan is ≥ 3× faster than full scan on unchanged projects.
6. ✅ `.depvulnrc` config is respected across all commands.
7. ✅ All Phase 1 and Phase 2 tests still pass.
8. ✅ Tool passes security audit (no secrets in output, safe file handling).

### Tasks

- [ ] Implement `TreeReporter` (ASCII + DOT output)
- [ ] Implement `WatchMode` (file watcher + incremental scan)
- [ ] Implement `ConfigManager` (`.depvulnrc` YAML config)
- [ ] Implement `PluginLoader` (entry point discovery)
- [ ] Implement `CveSourcePlugin` base class
- [ ] Implement `ParserPlugin` base class
- [ ] Implement `ReportTemplatePlugin` base class
- [ ] Implement `ExportDb` command
- [ ] Build GitHub Action (Docker-based)
- [ ] Build GitLab CI template
- [ ] Implement parallel CVE lookups
- [ ] Implement incremental scan logic
- [ ] Implement `--exclude` pattern matching
- [ ] Implement audit logging
- [ ] Write plugin examples (custom parser, custom CVE source)
- [ ] Write CI/CD integration docs
- [ ] Security audit
- [ ] Performance benchmarking
- [ ] Final documentation and release

---

## Summary

| Phase | Scope | Duration (est.) | Key Outcome |
|-------|-------|-----------------|-------------|
| **1** | MVP: npm/pip parsers + OSV + text/JSON reports | 2-3 weeks | Working CLI that finds CVEs in 2 ecosystems |
| **2** | Multi-ecosystem + NVD + rich reports + diff/fix | 3-4 weeks | Professional tool covering all major ecosystems |
| **3** | CI/CD + plugins + tree viz + production hardening | 3-4 weeks | Enterprise-ready with extensibility |

**Total estimated timeline: 8-11 weeks.**
