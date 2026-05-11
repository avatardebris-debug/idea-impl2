# depvuln — Dependency Vulnerability Scanner

## Overview

`depvuln` is a CLI tool that scans project dependencies for known vulnerabilities.
It parses dependency lockfiles from multiple ecosystems (npm, pip, Maven, Cargo, Go, CocoaPods),
queries the OSV and NVD APIs for CVE data, scores findings by CVSS severity, and generates
reports in text, JSON, or HTML format.

## Architecture

```
depvuln/
├── __init__.py
├── main.py              # CLI entry point (argparse, orchestration)
├── config.py            # ConfigManager (JSON config, defaults)
├── parsers/             # Dependency file parsers
│   ├── __init__.py
│   ├── base.py          # Abstract DependencyParser
│   ├── npm_parser.py    # package-lock.json / yarn.lock
│   ├── pip_parser.py    # requirements.txt / Pipfile.lock
│   ├── maven_parser.py  # pom.xml
│   ├── cargo_parser.py  # Cargo.toml
│   ├── go_parser.py     # go.mod
│   └── podfile_parser.py # Podfile
├── cve/                 # CVE data fetching
│   ├── __init__.py
│   ├── fetcher.py       # CveFetcher (OSV API + SQLite cache)
│   ├── nvd_fetcher.py   # NvdFetcher (NVD API + SQLite cache)
│   ├── cve_data_merger.py # CveDataMerger (dedup + merge)
│   └── cache.py         # CveCache (TTL-based SQLite)
├── reports/             # Report generators
│   ├── __init__.py
│   ├── json_report.py   # JsonReportGenerator
│   ├── text_report.py   # TextReportGenerator
│   └── html_report.py   # HtmlReportGenerator
├── scorer.py            # VulnScorer (CVSS → severity)
└── remediation.py       # RemediationAdvisor (upgrade recommendations)
```

## Key Components

### 1. Dependency Parsers (`depvuln/parsers/`)

Each parser implements the `DependencyParser` abstract base class:

```python
class DependencyParser(ABC):
    @abstractmethod
    def parse(self, filepath: str) -> list[dict[str, Any]]:
        """Returns list of {name, version, ecosystem} dicts."""
```

**Supported ecosystems:**

| Parser | Ecosystem | Input File |
|--------|-----------|------------|
| `NpmParser` | npm | `package-lock.json`, `yarn.lock` |
| `PipParser` | pip | `requirements.txt`, `Pipfile.lock` |
| `MavenParser` | maven | `pom.xml` |
| `CargoParser` | cargo | `Cargo.toml` |
| `GoParser` | go | `go.mod` |
| `PodfileParser` | podfile | `Podfile` |

**Parser design notes:**
- All parsers return `[]` on missing/empty/malformed files (fail-safe)
- `CargoParser` uses `tomllib` (stdlib in Python 3.11+) with `tomli` fallback
- `MavenParser` handles both namespaced and non-namespaced XML
- `PipParser` supports both `requirements.txt` (regex) and `Pipfile.lock` (JSON)
- `NpmParser` handles both v1 and v2/v3 `package-lock.json` formats

### 2. CVE Data Fetching (`depvuln/cve/`)

**CveCache** — TTL-based SQLite cache:
- Stores query results with expiration timestamps
- Key format: `osv:{ecosystem}:{package}:{version}` or `nvd:{cve_id}`
- Default TTL: 3600 seconds (1 hour)
- Database path: `~/.depvuln/cache/osv.db` / `nvd.db`

**CveFetcher** (OSV API):
- Endpoint: `https://api.osv.dev/v1/query`
- POST query with `{package, ecosystem, version}`
- Extracts: CVE ID, CVSS score, severity label, description, vector string
- Severity mapping: CRITICAL (≥9.0), HIGH (≥7.0), MEDIUM (≥4.0), LOW (>0), UNKNOWN (0)
- Results cached for future queries

**NvdFetcher** (NVD API):
- Endpoint: `https://services.nvd.org.az/1.0/json/cve/{cve_id}`
- Also supports keyword search: `https://services.nvd.org.az/1.0/json/cves?keyword={package}`
- Extracts: CVSS v3 base score, vector string, description
- Same severity mapping as OSV

**CveDataMerger**:
- Merges OSV and NVD results by CVE ID
- OSV takes precedence (richer data)
- NVD fills gaps: vector_string, description, higher CVSS
- Final list sorted by CVSS descending

### 3. Vulnerability Scoring (`depvuln/scorer.py`)

**VulnScorer** maps CVSS scores to severity labels:

| CVSS Range | Severity |
|------------|----------|
| ≥ 9.0 | CRITICAL |
| ≥ 7.0 | HIGH |
| ≥ 4.0 | MEDIUM |
| > 0 | LOW |
| 0 | UNKNOWN |

Input format supports both flat (`{"cvss": 7.5, "cve_id": "CVE-..."}`) and nested (`{"cve": {"cvss": 7.5}}`) structures.

Output is sorted by severity order: CRITICAL → HIGH → MEDIUM → LOW.

### 4. Remediation Advisor (`depvuln/remediation.py`)

**RemediationAdvisor** generates actionable upgrade recommendations:

- Parses `fix` field (e.g., `"upgrade to requests>=2.31.0"`)
- Extracts package name and target version
- Generates `recommended_action` string: `"Upgrade {package} to {version}"`
- Assigns priority: CRITICAL=1, HIGH=2, MEDIUM=3, LOW=4
- Sorts results by priority (highest severity first)
- Handles missing fix info gracefully

### 5. Report Generators (`depvuln/reports/`)

All generators implement `generate(findings: list[dict]) -> str`:

**JsonReportGenerator**:
- Outputs JSON array with fields: severity, package, version, cve_id, cvss, description, fix
- Pretty-printed with 2-space indent

**TextReportGenerator**:
- Human-readable format: `[SEVERITY] package==version → CVE-ID (CVSS X.X)`
- Truncates descriptions > 120 chars
- Shows fix information

**HtmlReportGenerator**:
- Styled HTML table with severity color coding
- Colors: CRITICAL=#d32f2f, HIGH=#f44336, MEDIUM=#ff9800, LOW=#4caf50
- Empty state: "No vulnerabilities found" message
- Includes vulnerability count

## CLI Interface (`depvuln/main.py`)

```bash
depvuln scan [OPTIONS] [PATH]
```

**Options:**
- `--ecosystem` — Force ecosystem (npm/pip/maven/cargo/go/podfile)
- `--format` — Output format: text (default), json, html
- `--severity` — Minimum severity threshold: LOW, MEDIUM, HIGH, CRITICAL
- `--output` — Output file path (default: stdout)
- `--config` — Config file path
- `--no-cache` — Disable caching
- `--cache-ttl` — Cache TTL in seconds (default: 3600)
- `--osv-api-key` — OSV API key
- `--nvd-api-key` — NVD API key
- `--verbose` — Enable debug logging

**Config file** (JSON):
```json
{
  "cache_ttl": 3600,
  "severity_threshold": "LOW",
  "default_format": "text",
  "osv_api_key": null,
  "nvd_api_key": null
}
```

**Workflow:**
1. Detect or use `--ecosystem` to select parser
2. Parse dependency file → list of `{name, version, ecosystem}`
3. For each dependency, query OSV API (with cache)
4. For each CVE found, query NVD API for enriched data (with cache)
5. Merge OSV + NVD results (dedup by CVE ID)
6. Score by CVSS severity
7. Generate remediation advice
8. Format and output report

## Testing

### Test Suite Structure

```
tests/
├── test_parsers.py      # Parser unit tests
├── test_cve_fetcher.py  # CVE fetcher tests
├── test_scorer.py       # Scorer unit tests
├── test_remediation.py  # Remediation advisor tests
└── test_reports.py      # Report generator tests
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_parsers.py

# With verbose output
pytest tests/ -v
```

### Test Coverage

| Module | Tests | Key Scenarios |
|--------|-------|---------------|
| `NpmParser` | 5 | v1/v3 lockfiles, missing file, empty file, malformed JSON |
| `PipParser` | 5 | requirements.txt, comments, Pipfile.lock, missing/empty files |
| `VulnScorer` | 5 | All severity levels, sorting, nested/flat format |
| `RemediationAdvisor` | 6 | Single/multiple findings, empty input, no fix, sorting, format |
| `JsonReportGenerator` | 2 | Normal output, empty findings |
| `TextReportGenerator` | 2 | Normal output, empty findings |

### Test Design Notes

- **Parsers**: Use `tempfile.mkdtemp()` for isolated file creation; test edge cases (missing, empty, malformed)
- **Scorer**: Test all severity boundaries (9.0, 7.0, 4.0) and sorting order
- **Remediation**: Test sorting by severity priority, missing fix handling, and output format
- **Reports**: Verify JSON structure and text content inclusion
- **CVE Fetcher**: Tests require network access or mocking; use `responses` library for HTTP mocking

## Dependencies

- **stdlib**: `argparse`, `json`, `os`, `sys`, `logging`, `re`, `xml.etree.ElementTree`, `sqlite3`, `urllib.request`, `tomllib` (3.11+)
- **Optional**: `tomli` (fallback for Python < 3.11)
- **Test**: `pytest`, `responses` (for HTTP mocking)

## Error Handling

- Missing dependency files → return `[]` (no crash)
- Malformed JSON/XML → return `[]` (no crash)
- Network failures → return `[]` with warning log
- Invalid config → use defaults with warning
- All parsers are fail-safe: never raise exceptions on bad input

## Future Enhancements

1. **GitHub Advisory DB** integration for additional CVE sources
2. **Fix version database** for more accurate remediation advice
3. **CI/CD integration** (GitHub Actions, GitLab CI)
4. **Dependency graph** visualization
5. **Trend analysis** (vulnerability count over time)
6. **Custom severity thresholds** per ecosystem
7. **Batch scanning** for monorepos
8. **Export to SARIF** format for IDE integration
