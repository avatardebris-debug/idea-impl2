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

