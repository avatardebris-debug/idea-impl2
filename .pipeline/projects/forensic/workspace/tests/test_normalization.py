"""Tests for financial line-item normalization."""

import pytest
from forensic.normalization import (
    ALIAS_MAP,
    STANDARD_LINE_ITEMS,
    NormalizedCompany,
    normalize_items,
    normalize_multiple,
    get_standard_line_items,
)


class TestStandardLineItems:
    def test_returns_all_standard_items(self):
        items = get_standard_line_items()
        assert len(items) >= 8
        assert "revenue" in items
        assert "net_income" in items
        assert "total_assets" in items

    def test_alias_map_completeness(self):
        """Every standard item should have at least one alias."""
        for item in STANDARD_LINE_ITEMS:
            aliases = [k for k, v in ALIAS_MAP.items() if v == item]
            assert len(aliases) >= 1, f"No aliases for {item}"


class TestNormalizeItems:
    def test_extract_revenue(self):
        text = "Revenue $1,234,567,890"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(1234567890.0)

    def test_extract_revenue_with_suffix(self):
        text = "Revenue of $1.23B"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(1230000000.0)

    def test_extract_revenue_with_m_suffix(self):
        text = "Revenue of $500M"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(500000000.0)

    def test_extract_cogs(self):
        text = "Cost of goods sold $800,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("cogs") == pytest.approx(800000.0)

    def test_extract_net_income(self):
        text = "Net income $434,567"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("net_income") == pytest.approx(434567.0)

    def test_extract_total_assets(self):
        text = "Total assets $3,500,000,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("total_assets") == pytest.approx(3500000000.0)

    def test_extract_operating_income(self):
        text = "Operating income $500,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("operating_income") == pytest.approx(500000.0)

    def test_extract_capex(self):
        text = "Capital expenditures $100,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("capex") == pytest.approx(100000.0)

    def test_extract_free_cash_flow(self):
        text = "Free cash flow $400,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("free_cash_flow") == pytest.approx(400000.0)

    def test_extract_cash_flow_ops(self):
        text = "Cash flow from operations $600,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("cash_flow_ops") == pytest.approx(600000.0)

    def test_extract_total_liabilities(self):
        text = "Total liabilities $2,000,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("total_liabilities") == pytest.approx(2000000.0)

    def test_extract_total_equity(self):
        text = "Total equity $1,500,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("total_equity") == pytest.approx(1500000.0)

    def test_extract_cash_and_equivalents(self):
        text = "Cash and cash equivalents $50,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("cash_and_equivalents") == pytest.approx(50000.0)

    def test_extract_gross_profit(self):
        text = "Gross profit $434,567"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("gross_profit") == pytest.approx(434567.0)

    def test_no_items_extracted(self):
        text = "No financial data here"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert len(norm.items) == 0

    def test_empty_text_parts(self):
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [])
        assert len(norm.items) == 0

    def test_normalized_values(self):
        text_parts = [
            "Revenue $1,000,000",
            "Cost of goods sold $600,000",
            "Net income $200,000",
        ]
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", text_parts)
        assert norm.normalized.get("revenue") == pytest.approx(1.0)
        assert norm.normalized.get("cogs") == pytest.approx(0.6)
        assert norm.normalized.get("net_income") == pytest.approx(0.2)

    def test_normalized_with_total_assets_fallback(self):
        text_parts = [
            "Total assets $2,000,000",
            "Net income $200,000",
        ]
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", text_parts)
        assert norm.normalized.get("net_income") == pytest.approx(0.1)

    def test_normalized_no_normalizer(self):
        text_parts = [
            "Net income $200,000",
        ]
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", text_parts)
        assert norm.normalized.get("net_income") == pytest.approx(200000.0)

    def test_to_dict(self):
        text_parts = ["Revenue $1,000,000"]
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", text_parts)
        d = norm.to_dict()
        assert d["ticker"] == "AAPL"
        assert d["cik"] == "000001"
        assert d["accession_no"] == "001"
        assert d["filing_date"] == "2024-01-01"
        assert "items" in d
        assert "normalized" in d

    def test_multiple_line_items_in_one_text(self):
        text = "Revenue $1,000,000. Cost of goods sold $600,000. Net income $200,000."
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(1000000.0)
        assert norm.items.get("cogs") == pytest.approx(600000.0)
        assert norm.items.get("net_income") == pytest.approx(200000.0)

    def test_alias_sales(self):
        text = "Sales $500,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(500000.0)

    def test_alias_cost_of_sales(self):
        text = "Cost of sales $300,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("cogs") == pytest.approx(300000.0)

    def test_alias_operating_profit(self):
        text = "Operating profit $100,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("operating_income") == pytest.approx(100000.0)

    def test_alias_net_earnings(self):
        text = "Net earnings $50,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("net_income") == pytest.approx(50000.0)

    def test_alias_assets(self):
        text = "Assets $1,000,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("total_assets") == pytest.approx(1000000.0)

    def test_alias_liabilities(self):
        text = "Liabilities $500,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("total_liabilities") == pytest.approx(500000.0)

    def test_alias_shareholders_equity(self):
        text = "Shareholders equity $500,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("total_equity") == pytest.approx(500000.0)

    def test_alias_cash(self):
        text = "Cash $100,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("cash_and_equivalents") == pytest.approx(100000.0)

    def test_alias_capex(self):
        text = "Capex $50,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("capex") == pytest.approx(50000.0)

    def test_alias_purchase_of_property(self):
        text = "Purchase of property and equipment $75,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("capex") == pytest.approx(75000.0)

    def test_alias_operating_cash_flow(self):
        text = "Operating cash flow $200,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("cash_flow_ops") == pytest.approx(200000.0)

    def test_alias_net_revenue(self):
        text = "Net revenue $800,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(800000.0)

    def test_alias_gross_sales(self):
        text = "Gross sales $900,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(900000.0)

    def test_alias_cost_of_revenue(self):
        text = "Cost of revenue $400,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("cogs") == pytest.approx(400000.0)

    def test_alias_income_from_operations(self):
        text = "Income from operations $150,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("operating_income") == pytest.approx(150000.0)

    def test_alias_net_income_loss(self):
        text = "Net income (loss) $-10,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("net_income") == pytest.approx(-10000.0)

    def test_alias_stockholders_equity(self):
        text = "Stockholders equity $300,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("total_equity") == pytest.approx(300000.0)

    def test_extract_k_suffix(self):
        text = "Revenue of $50K"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(50000.0)

    def test_extract_k_suffix_uppercase(self):
        text = "Revenue of $50k"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(50000.0)

    def test_extract_b_suffix_uppercase(self):
        text = "Revenue of $50B"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(50000000000.0)

    def test_extract_b_suffix_lowercase(self):
        text = "Revenue of $50b"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(50000000000.0)

    def test_extract_m_suffix_uppercase(self):
        text = "Revenue of $50M"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(50000000.0)

    def test_extract_m_suffix_lowercase(self):
        text = "Revenue of $50m"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(50000000.0)

    def test_no_dollar_sign(self):
        text = "Revenue 1000000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") is None

    def test_multiple_numbers_in_text(self):
        text = "Revenue $1,000,000 and expenses $500,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(1000000.0)
        assert norm.items.get("cogs") is None  # "expenses" is not in alias map

    def test_complex_numbers(self):
        text = "Revenue $1,234,567.89"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(1234567.89)

    def test_integer_numbers(self):
        text = "Revenue $1000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(1000.0)

    def test_text_parts_are_combined(self):
        text_parts = [
            "Revenue $500,000",
            "Cost of goods sold $300,000",
        ]
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", text_parts)
        assert norm.items.get("revenue") == pytest.approx(500000.0)
        assert norm.items.get("cogs") == pytest.approx(300000.0)

    def test_case_insensitive_matching(self):
        text = "REVENUE $1,000,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("revenue") == pytest.approx(1000000.0)

    def test_case_insensitive_matching_cogs(self):
        text = "COST OF GOODS SOLD $500,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("cogs") == pytest.approx(500000.0)

    def test_case_insensitive_matching_net_income(self):
        text = "NET INCOME $200,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("net_income") == pytest.approx(200000.0)

    def test_case_insensitive_matching_total_assets(self):
        text = "TOTAL ASSETS $3,000,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("total_assets") == pytest.approx(3000000.0)

    def test_case_insensitive_matching_total_liabilities(self):
        text = "TOTAL LIABILITIES $1,500,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("total_liabilities") == pytest.approx(1500000.0)

    def test_case_insensitive_matching_total_equity(self):
        text = "TOTAL EQUITY $1,500,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("total_equity") == pytest.approx(1500000.0)

    def test_case_insensitive_matching_cash_and_equivalents(self):
        text = "CASH AND CASH EQUIVALENTS $100,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("cash_and_equivalents") == pytest.approx(100000.0)

    def test_case_insensitive_matching_operating_cash_flow(self):
        text = "OPERATING CASH FLOW $200,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("cash_flow_ops") == pytest.approx(200000.0)

    def test_case_insensitive_matching_capex(self):
        text = "CAPEX $50,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("capex") == pytest.approx(50000.0)

    def test_case_insensitive_matching_free_cash_flow(self):
        text = "FREE CASH FLOW $150,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("free_cash_flow") == pytest.approx(150000.0)

    def test_case_insensitive_matching_gross_profit(self):
        text = "GROSS PROFIT $400,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("gross_profit") == pytest.approx(400000.0)

    def test_case_insensitive_matching_operating_income(self):
        text = "OPERATING INCOME $300,000"
        norm = normalize_items("AAPL", "000001", "001", "2024-01-01", [text])
        assert norm.items.get("operating_income") == pytest.approx(300000.0)


class TestNormalizeMultiple:
    def test_normalize_multiple_empty(self):
        result = normalize_multiple([])
        assert result == []

    def test_normalize_multiple_single_company(self):
        comp = NormalizedCompany(
            ticker="AAPL",
            cik="000001",
            accession_no="001",
            filing_date="2024-01-01",
            items={"revenue": 1000000, "net_income": 200000},
            normalized={},
        )
        result = normalize_multiple([comp])
        assert len(result) == 1
        assert result[0].normalized.get("revenue") == pytest.approx(1.0)
        assert result[0].normalized.get("net_income") == pytest.approx(0.2)

    def test_normalize_multiple_multiple_companies(self):
        comp1 = NormalizedCompany(
            ticker="AAPL",
            cik="000001",
            accession_no="001",
            filing_date="2024-01-01",
            items={"revenue": 1000000, "net_income": 200000},
            normalized={},
        )
        comp2 = NormalizedCompany(
            ticker="MSFT",
            cik="000002",
            accession_no="002",
            filing_date="2024-01-01",
            items={"revenue": 2000000, "net_income": 500000},
            normalized={},
        )
        result = normalize_multiple([comp1, comp2])
        assert len(result) == 2
        assert result[0].normalized.get("revenue") == pytest.approx(1.0)
        assert result[0].normalized.get("net_income") == pytest.approx(0.2)
        assert result[1].normalized.get("revenue") == pytest.approx(1.0)
        assert result[1].normalized.get("net_income") == pytest.approx(0.25)

    def test_normalize_multiple_with_total_assets(self):
        comp1 = NormalizedCompany(
            ticker="AAPL",
            cik="000001",
            accession_no="001",
            filing_date="2024-01-01",
            items={"total_assets": 2000000, "net_income": 200000},
            normalized={},
        )
        comp2 = NormalizedCompany(
            ticker="MSFT",
            cik="000002",
            accession_no="002",
            filing_date="2024-01-01",
            items={"total_assets": 3000000, "net_income": 300000},
            normalized={},
        )
        result = normalize_multiple([comp1, comp2])
        assert len(result) == 2
        assert result[0].normalized.get("net_income") == pytest.approx(0.1)
        assert result[1].normalized.get("net_income") == pytest.approx(0.1)

    def test_normalize_multiple_no_normalizer_available(self):
        comp1 = NormalizedCompany(
            ticker="AAPL",
            cik="000001",
            accession_no="001",
            filing_date="2024-01-01",
            items={"net_income": 200000},
            normalized={},
        )
        comp2 = NormalizedCompany(
            ticker="MSFT",
            cik="000002",
            accession_no="002",
            filing_date="2024-01-01",
            items={"net_income": 300000},
            normalized={},
        )
        result = normalize_multiple([comp1, comp2])
        assert len(result) == 2
        assert result[0].normalized.get("net_income") == pytest.approx(200000.0)
        assert result[1].normalized.get("net_income") == pytest.approx(300000.0)

    def test_normalize_multiple_preserves_items(self):
        comp1 = NormalizedCompany(
            ticker="AAPL",
            cik="000001",
            accession_no="001",
            filing_date="2024-01-01",
            items={"revenue": 1000000, "net_income": 200000},
            normalized={},
        )
        result = normalize_multiple([comp1])
        assert result[0].items.get("revenue") == pytest.approx(1000000.0)
        assert result[0].items.get("net_income") == pytest.approx(200000.0)

    def test_normalize_multiple_preserves_ticker(self):
        comp1 = NormalizedCompany(
            ticker="AAPL",
            cik="000001",
            accession_no="001",
            filing_date="2024-01-01",
            items={"revenue": 1000000},
            normalized={},
        )
        result = normalize_multiple([comp1])
        assert result[0].ticker == "AAPL"
        assert result[0].cik == "000001"
        assert result[0].accession_no == "001"
        assert result[0].filing_date == "2024-01-01"
