# Code Review — Phase 2

**Date**: 2025-07-25  
**Reviewer**: AI Code Reviewer  
**Scope**: Phase 2 — Multi-Company Analysis + Earnings Prediction  
**Status**: BLOCKING — Phase 2 deliverables are missing

---

## Executive Summary

Phase 2 requires extending the forensic accounting suite to support multi-company comparison and earnings prediction. The spec calls for three new source modules (`compare.py`, `earnings.py`, `normalization.py`) and three new test files (`test_compare.py`, `test_earnings.py`, `test_normalization.py`).

**Overall verdict**: **FAIL** — None of the Phase 2 deliverables exist. The review file was not properly generated in the previous attempt, and the Phase 2 code was never written.

---

## 1. Blocking Issues (Must Fix Before Merge)

### B1. Missing Phase 2 Source Files

**Severity**: CRITICAL  
**Location**: `src/forensic/`

The following files required by the Phase 2 spec do not exist:
- `src/forensic/compare.py` — Multi-company comparison logic
- `src/forensic/earnings.py` — Earnings prediction module
- `src/forensic/normalization.py` — Financial line-item normalization

**Impact**:
- Phase 2 cannot be validated without these modules
- The CLI command `forensic compare <TICKER1> <TICKER2> ...` cannot be implemented
- No comparative fraud scoring or earnings prediction is available

**Recommendation**:
- Create `src/forensic/normalization.py` with financial line-item normalization for at least 8 standard items (revenue, COGS, operating income, net income, total assets, total liabilities, cash flow from ops, capex, working capital)
- Create `src/forensic/compare.py` with multi-company comparison logic that:
  - Ingests latest 10-K and 10-Q filings for all specified tickers
  - Normalizes financial line items across companies
  - Runs Phase 1 red-flag checks on each company
  - Computes comparative fraud scores (relative ranking)
- Create `src/forensic/earnings.py` with earnings prediction module that:
  - Extracts historical quarterly earnings data from 10-Q filings
  - Fits a simple linear regression or moving-average model
  - Predicts next quarter's EPS and revenue
  - Flags prediction confidence intervals
- Update `cli.py` to add the `forensic compare` command

### B2. Missing Phase 2 Test Files

**Severity**: CRITICAL  
**Location**: `tests/`

The following test files required by the Phase 2 spec do not exist:
- `tests/test_compare.py`
- `tests/test_earnings.py`
- `tests/test_normalization.py`

**Impact**:
- No test coverage for Phase 2 code
- Cannot validate correctness of normalization, comparison, or earnings prediction logic

**Recommendation**:
- Create `tests/test_normalization.py` with tests for all 8+ financial line items
- Create `tests/test_compare.py` with tests for multi-company comparison logic
- Create `tests/test_earnings.py` with tests for earnings prediction module

### B3. Missing Dependencies

**Severity**: HIGH  
**Location**: `requirements.txt`

The Phase 2 spec requires `numpy` and `pandas` for regression and time-series analysis, but these are not listed in the requirements.

**Impact**:
- Phase 2 code cannot run without these dependencies
- `numpy` and `pandas` must be installed for earnings prediction to work

**Recommendation**:
- Add `numpy` and `pandas` to `requirements.txt`
- Verify they are importable in the test environment

---

## 2. Significant Issues (Should Fix)

### S1. No `forensic compare` CLI Command

**Severity**: HIGH  
**Location**: `cli.py`

The Phase 2 spec requires a `forensic compare <TICKER1> <TICKER2> ...` CLI command, but this command does not exist in `cli.py`.

**Recommendation**:
- Add a new CLI command group `compare` using `click` (or the existing CLI framework)
- Accept multiple ticker arguments
- Route to the Phase 2 comparison pipeline

### S2. No Comparative JSON Report Format

**Severity**: HIGH  
**Location**: `models.py`

The Phase 2 spec requires a comparative JSON report with per-company fraud scores, rankings, and earnings predictions with confidence intervals. No model for this report format exists.

**Recommendation**:
- Add a `ComparativeReport` dataclass in `models.py` with:
  - Per-company fraud scores and red flags
  - Comparative ranking
  - Earnings predictions with confidence intervals
- Add a `to_json()` method for serialization

### S3. Normalization Must Handle Cross-Company Differences

**Severity**: MEDIUM  
**Location**: `normalization.py` (to be created)

Different companies report financial data differently (e.g., different fiscal year ends, different line item names). The normalization module must handle these differences.

**Recommendation**:
- Build a mapping of common line item aliases to canonical names
- Handle fiscal year differences
- Validate that all required line items are present after normalization

---

## 3. Minor Issues (Nice to Have)

### M1. Earnings Prediction Model Choice

**Severity**: LOW  
**Location**: `earnings.py` (to be created)

The spec allows "simple linear regression or moving-average model." Consider which approach is more appropriate for financial data.

**Recommendation**:
- Linear regression may overfit on limited data points
- Moving average with configurable window size may be more robust
- Consider adding model selection as a CLI option

### M2. Confidence Interval Calculation

**Severity**: LOW  
**Location**: `earnings.py` (to be created)

Confidence intervals require proper statistical treatment. Simple standard deviation may not be sufficient.

**Recommendation**:
- Use proper confidence interval formulas (e.g., t-distribution for small samples)
- Flag when sample size is too small for reliable intervals

### M3. CLI Output Format

**Severity**: LOW  
**Location**: `cli.py` (to be updated)

The comparative report should support both JSON and human-readable output formats.

**Recommendation**:
- Add `--format json|text` option to the `compare` command
- Default to JSON for machine readability

---

## 4. Architecture Review

### Strengths of Phase 1 Foundation

1. **Modular analyzer design**: The four analyzer classes in Phase 1 can be reused for per-company red-flag checks in Phase 2
2. **SQLite persistence**: The database layer can store normalized financial data for comparison
3. **Config-driven design**: The config system can be extended with Phase 2-specific settings
4. **CLI framework**: The existing CLI can be extended with the `compare` command

### Areas for Improvement

1. **Dependency injection**: Phase 2 modules should accept dependencies (database, config) via constructor for testability
2. **Error handling**: Phase 2 should handle cases where some tickers fail to ingest gracefully
3. **Caching**: Normalized data should be cached to avoid re-reading the database for each comparison

---

## 5. Test Coverage Gap Analysis

| Module | Estimated Coverage | Key Missing Tests |
|--------|-------------------|-------------------|
| `normalization.py` | 0% | Line item mapping, cross-company normalization, missing data handling |
| `compare.py` | 0% | Multi-company ingestion, fraud score comparison, ranking logic |
| `earnings.py` | 0% | Historical data extraction, regression/moving-average fitting, prediction accuracy |
| `cli.py` (compare) | 0% | CLI argument parsing, output formatting, error handling |

---

## 6. Security & Safety Observations

1. **Input validation on tickers**: The `compare` command should validate all ticker inputs before processing
2. **Rate limiting**: Fetching data for multiple tickers should respect SEC API rate limits
3. **Data privacy**: No personal data is involved, but financial data should be handled responsibly

---

## 7. Recommendations for Phase 2 Implementation

1. **Create `normalization.py` first** — it is the foundation for comparison
2. **Create `compare.py` second** — it depends on normalization
3. **Create `earnings.py` third** — it can be developed independently
4. **Update `cli.py` last** — it depends on all three modules
5. **Write tests alongside code** — not after
6. **Add `numpy` and `pandas` to requirements.txt**

---

## 8. Final Verdict

**Status**: ❌ **BLOCKING — Phase 2 deliverables are missing**

The Phase 2 review file was not properly generated in the previous attempt. The Phase 2 code (compare.py, earnings.py, normalization.py) and tests (test_compare.py, test_earnings.py, test_normalization.py) do not exist.

**Blocking Issues**:
1. Missing `compare.py`, `earnings.py`, `normalization.py` source files
2. Missing `test_compare.py`, `test_earnings.py`, `test_normalization.py` test files
3. Missing `numpy` and `pandas` dependencies

**Priority order for fixes**:
1. Add `numpy` and `pandas` to requirements.txt
2. Create `src/forensic/normalization.py`
3. Create `src/forensic/compare.py`
4. Create `src/forensic/earnings.py`
5. Create `tests/test_normalization.py`
6. Create `tests/test_compare.py`
7. Create `tests/test_earnings.py`
8. Update `cli.py` with `forensic compare` command
9. Update `models.py` with `ComparativeReport` model

---

*Review completed by AI Code Reviewer. All findings are actionable and prioritized.*
