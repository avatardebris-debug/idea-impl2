# Validation Report — Phase 5
## Summary
- Tests: 174 passed, 97 failed
## Verdict: FAIL

### Details
Phase 5 tests were executed across the workspace. Out of 271 total tests collected:
- **174 passed**
- **97 failed**

### Failure Categories
The 97 failures span multiple modules and test files:

1. **test_database.py** (7 failures): `ForensicDatabase` object missing `execute` and `get_companies` attributes — database API mismatch.
2. **test_ingest.py** (4 failures): `IngestResult.__init__()` rejects `accession_no` keyword argument — model signature mismatch.
3. **test_models.py** (7 failures): `RedFlag.from_dict` missing, `IngestResult`/`AnalysisResult`/`Report` constructor mismatches.
4. **test_normalization.py** (10+ failures): `extract_*` methods return `None` instead of expected values; `normalize_multiple` returns `None`.
5. **test_capital_flow.py** (10 failures): Period extraction returns wrong counts/amounts (e.g., `0.0` vs `300000.0`, `1` vs `2`).
6. **test_capital_flows.py** (2 failures): `'dict' object has no attribute 'amount'` — return type mismatch.
7. **test_cli.py** (4 failures): CLI module attribute errors — CLI interface broken.
8. **test_config.py** (2 failures): Config returns wrong database paths (`forensic.db` vs expected `test.db`/`test_singleton.db`).
9. **test_earnings.py** (1 failure): `inf` returned instead of `0.0` for insufficient data case.
10. **test_advanced_flags.py** (1 failure): Altman Z-score returns `'grey'` instead of `'safe'`.
11. **test_scoring.py** (12 failures): `'dict' object has no attribute 'severity'` — scoring returns dicts instead of objects; risk level mismatch.
12. **test_reporting.py** (4 failures): `RedFlagSeverity.HIGH` missing; report generation broken.
13. **test_web.py** (6 failures): Template files not found (`base.html`, `companies.html`, etc.) — Jinja2 template resolution broken.
14. **test_red_flags.py** (1 failure): Revenue/receivables mismatch check returns `0` instead of `> 0`.

### Root Causes
- API contracts between modules are inconsistent (dicts vs objects, missing methods).
- Model constructors do not match test expectations (missing/extra arguments).
- Database layer missing key methods (`execute`, `get_companies`).
- Template paths not resolved correctly for web module.
- Financial calculation functions return `None` or wrong values.
