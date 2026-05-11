"""Unit tests for core module functions: _safe_divide, _normalize_key, _extract_numeric, build_metrics_dict."""

import pytest
from financial_document_analyzer.core import (
    _safe_divide,
    _normalize_key,
    _extract_numeric,
    build_metrics_dict,
)


# ── _safe_divide ──────────────────────────────────────────────────────────

class TestSafeDivide:
    def test_normal_division(self):
        assert _safe_divide(10.0, 2.0) == 5.0

    def test_division_by_zero_returns_zero(self):
        assert _safe_divide(10.0, 0) == 0.0

    def test_zero_divided_by_zero(self):
        assert _safe_divide(0.0, 0) == 0.0

    def test_negative_numerator(self):
        assert _safe_divide(-10.0, 2.0) == -5.0

    def test_negative_denominator(self):
        assert _safe_divide(10.0, -2.0) == -5.0

    def test_float_denominator(self):
        assert _safe_divide(10.0, 3.0) == pytest.approx(3.333333, rel=1e-4)


# ── _normalize_key ────────────────────────────────────────────────────────

class TestNormalizeKey:
    def test_simple_lowercase(self):
        assert _normalize_key("Revenue") == "revenue"

    def test_spaces_to_underscores(self):
        assert _normalize_key("Cost of Goods") == "cost_of_goods"

    def test_hyphens_to_underscores(self):
        assert _normalize_key("gross-profit") == "gross_profit"

    def test_mixed_case_and_whitespace(self):
        assert _normalize_key("  Net Income  ") == "net_income"

    def test_already_normalized(self):
        assert _normalize_key("already_normalized") == "already_normalized"

    def test_empty_string(self):
        assert _normalize_key("") == ""

    def test_multiple_hyphens(self):
        assert _normalize_key("a-b-c") == "a_b_c"


# ── _extract_numeric ──────────────────────────────────────────────────────

class TestExtractNumeric:
    def test_plain_integer(self):
        assert _extract_numeric("1234") == 1234.0

    def test_plain_float(self):
        assert _extract_numeric("1234.56") == 1234.56

    def test_currency_symbol(self):
        assert _extract_numeric("$1,234.56") == 1234.56

    def test_commas(self):
        assert _extract_numeric("1,234,567") == 1234567.0

    def test_parenthetical_negative(self):
        assert _extract_numeric("(1,234)") == -1234.0

    def test_parenthetical_negative_float(self):
        assert _extract_numeric("(567.89)") == -567.89

    def test_none_input(self):
        assert _extract_numeric(None) == 0.0

    def test_empty_string(self):
        assert _extract_numeric("") == 0.0

    def test_whitespace_only(self):
        assert _extract_numeric("   ") == 0.0

    def test_non_numeric_string(self):
        assert _extract_numeric("abc") == 0.0

    def test_negative_number(self):
        assert _extract_numeric("-500") == -500.0

    def test_dollar_with_commas_and_parentheses(self):
        assert _extract_numeric("$(1,000,000)") == -1000000.0

    def test_euro_symbol(self):
        assert _extract_numeric("€1,234.56") == 1234.56

    def test_pound_symbol(self):
        assert _extract_numeric("£1,234.56") == 1234.56


# ── build_metrics_dict ────────────────────────────────────────────────────

class TestBuildMetricsDict:
    def test_basic_structure(self):
        result = build_metrics_dict("test.csv", revenue=100, cogs=50, gross_profit=50)
        assert isinstance(result, dict)
        assert "filename" in result
        assert "metrics" in result
        assert "margins" in result
        assert "raw_rows" in result

    def test_filename(self):
        result = build_metrics_dict("my_file.csv")
        assert result["filename"] == "my_file.csv"

    def test_metrics_keys(self):
        result = build_metrics_dict("test.csv", revenue=100, cogs=50, gross_profit=30, operating_income=20, net_income=10)
        assert set(result["metrics"].keys()) == {"revenue", "cogs", "gross_profit", "operating_income", "net_income"}

    def test_margins_keys(self):
        result = build_metrics_dict("test.csv", revenue=100, cogs=50, gross_profit=30, operating_income=20, net_income=10)
        assert set(result["margins"].keys()) == {"gross_margin", "operating_margin", "net_margin"}

    def test_gross_margin_calculation(self):
        result = build_metrics_dict("test.csv", revenue=100, gross_profit=25)
        assert result["margins"]["gross_margin"] == 25.0

    def test_operating_margin_calculation(self):
        result = build_metrics_dict("test.csv", revenue=200, operating_income=40)
        assert result["margins"]["operating_margin"] == 20.0

    def test_net_margin_calculation(self):
        result = build_metrics_dict("test.csv", revenue=500, net_income=50)
        assert result["margins"]["net_margin"] == 10.0

    def test_zero_revenue_margins_are_zero(self):
        result = build_metrics_dict("test.csv", revenue=0, gross_profit=100, operating_income=50, net_income=25)
        assert result["margins"]["gross_margin"] == 0.0
        assert result["margins"]["operating_margin"] == 0.0
        assert result["margins"]["net_margin"] == 0.0

    def test_raw_rows_default(self):
        result = build_metrics_dict("test.csv")
        assert result["raw_rows"] == 0

    def test_raw_rows_custom(self):
        result = build_metrics_dict("test.csv", raw_rows=42)
        assert result["raw_rows"] == 42

    def test_all_metrics_preserved(self):
        result = build_metrics_dict(
            "test.csv",
            revenue=1000,
            cogs=600,
            gross_profit=400,
            operating_income=200,
            net_income=100,
        )
        assert result["metrics"]["revenue"] == 1000
        assert result["metrics"]["cogs"] == 600
        assert result["metrics"]["gross_profit"] == 400
        assert result["metrics"]["operating_income"] == 200
        assert result["metrics"]["net_income"] == 100
