"""Tests for capital_flow module."""

import pytest
from forensic.capital_flow import (
    extract_cash_flow_periods,
    analyze_capital_flows,
    analyze_capital_flow,
    compute_capex_to_revenue_ratios,
    CashFlowPeriod,
    CapitalFlowReport,
)


# ---------------------------------------------------------------------------
# extract_cash_flow_periods
# ---------------------------------------------------------------------------

_SAMPLE_CF_TEXT = """
Cash Flows

Year Ended December 31, 2023
Cash flows from operating activities:
  Net cash provided by operating activities $1,200,000
  Depreciation and amortization $150,000

Cash flows from investing activities:
  Purchase of property and equipment $(300,000)
  Capital expenditures $(300,000)
  Acquisitions, net $(50,000)

Cash flows from financing activities:
  Proceeds from debt $200,000
  Repayment of debt $(100,000)
  Dividends paid $(50,000)
  Share repurchases $(100,000)

Year Ended December 31, 2022
Cash flows from operating activities:
  Net cash provided by operating activities $1,000,000
  Depreciation and amortization $130,000

Cash flows from investing activities:
  Purchase of property and equipment $(250,000)
  Capital expenditures $(250,000)

Cash flows from financing activities:
  Proceeds from debt $150,000
  Repayment of debt $(80,000)
  Dividends paid $(40,000)
"""


def test_extract_periods_finds_two_periods():
    periods = extract_cash_flow_periods(_SAMPLE_CF_TEXT, ticker="TEST")
    assert len(periods) == 2
    assert periods[0].period_label == "FY2023"
    assert periods[1].period_label == "FY2022"


def test_extract_periods_operating_cash_flow():
    periods = extract_cash_flow_periods(_SAMPLE_CF_TEXT, ticker="TEST")
    assert periods[0].operating_cash_flow == 1200000.0
    assert periods[1].operating_cash_flow == 1000000.0


def test_extract_periods_capex():
    periods = extract_cash_flow_periods(_SAMPLE_CF_TEXT, ticker="TEST")
    assert periods[0].capital_expenditures == 300000.0
    assert periods[1].capital_expenditures == 250000.0


def test_extract_periods_debt():
    periods = extract_cash_flow_periods(_SAMPLE_CF_TEXT, ticker="TEST")
    assert periods[0].debt_issuance == 200000.0
    assert periods[0].debt_repayment == 100000.0


def test_extract_periods_dividends():
    periods = extract_cash_flow_periods(_SAMPLE_CF_TEXT, ticker="TEST")
    assert periods[0].dividends_paid == 50000.0


def test_extract_periods_share_repurchases():
    periods = extract_cash_flow_periods(_SAMPLE_CF_TEXT, ticker="TEST")
    assert periods[0].share_repurchases == 100000.0


def test_extract_periods_no_cf_section():
    """When no 'Cash Flows' section is found, it should fall back to full text."""
    text = "No cash flow section here."
    periods = extract_cash_flow_periods(text, ticker="TEST")
    assert len(periods) == 1
    assert periods[0].period_label == "Unknown"


def test_extract_periods_empty_text():
    periods = extract_cash_flow_periods("", ticker="TEST")
    assert len(periods) == 1


def test_extract_periods_depreciation():
    periods = extract_cash_flow_periods(_SAMPLE_CF_TEXT, ticker="TEST")
    assert periods[0].depreciation_amortization == 150000.0


# ---------------------------------------------------------------------------
# compute_capex_to_revenue_ratios
# ---------------------------------------------------------------------------

def test_capex_to_revenue_ratios():
    periods = [
        CashFlowPeriod(period_label="FY2023", capital_expenditures=300000),
        CashFlowPeriod(period_label="FY2022", capital_expenditures=250000),
    ]
    revenues = [3000000, 2500000]
    ratios = compute_capex_to_revenue_ratios(periods, revenues)
    assert len(ratios) == 2
    assert ratios[0]["ratio"] == 0.1
    assert ratios[1]["ratio"] == 0.1


def test_capex_to_revenue_ratios_zero_revenue():
    periods = [
        CashFlowPeriod(period_label="FY2023", capital_expenditures=300000),
    ]
    revenues = [0]
    ratios = compute_capex_to_revenue_ratios(periods, revenues)
    assert ratios[0]["ratio"] == 0.0


# ---------------------------------------------------------------------------
# analyze_capital_flows
# ---------------------------------------------------------------------------

def test_analyze_capital_flows():
    periods = [
        CashFlowPeriod(
            period_label="FY2023",
            operating_cash_flow=1200000,
            investing_cash_flow=-350000,
            financing_cash_flow=-50000,
            capital_expenditures=300000,
            debt_issuance=200000,
            debt_repayment=100000,
            dividends_paid=50000,
            share_repurchases=100000,
        ),
        CashFlowPeriod(
            period_label="FY2022",
            operating_cash_flow=1000000,
            investing_cash_flow=-300000,
            financing_cash_flow=-40000,
            capital_expenditures=250000,
            debt_issuance=150000,
            debt_repayment=80000,
            dividends_paid=40000,
            share_repurchases=80000,
        ),
    ]
    revenues = [3000000, 2500000]
    report = analyze_capital_flows(periods, revenues, ticker="TEST")
    assert report.ticker == "TEST"
    assert len(report.periods) == 2
    assert report.capex_to_revenue_ratios is not None
    assert len(report.capex_to_revenue_ratios) == 2
    assert report.debt_trend in ("increasing", "decreasing", "stable")
    assert report.dividend_trend in ("increasing", "decreasing", "stable")
    assert report.repurchase_trend in ("increasing", "decreasing", "stable")
    assert report.cash_flow_quality in ("healthy", "concerning", "stable", "insufficient data")
    assert report.summary


def test_analyze_capital_flows_single_period():
    periods = [
        CashFlowPeriod(
            period_label="FY2023",
            operating_cash_flow=1200000,
            investing_cash_flow=-350000,
            financing_cash_flow=-50000,
            capital_expenditures=300000,
        ),
    ]
    report = analyze_capital_flows(periods, ticker="TEST")
    assert report.cash_flow_quality == "insufficient data"


# ---------------------------------------------------------------------------
# analyze_capital_flow (one-shot)
# ---------------------------------------------------------------------------

def test_analyze_capital_flow_one_shot():
    report = analyze_capital_flow(_SAMPLE_CF_TEXT, ticker="TEST")
    assert report.ticker == "TEST"
    assert len(report.periods) == 2


# ---------------------------------------------------------------------------
# CashFlowPeriod dataclass
# ---------------------------------------------------------------------------

def test_cashflow_period_defaults():
    period = CashFlowPeriod(period_label="FY2023")
    assert period.operating_cash_flow == 0.0
    assert period.investing_cash_flow == 0.0
    assert period.financing_cash_flow == 0.0
    assert period.capital_expenditures == 0.0
    assert period.debt_issuance == 0.0
    assert period.debt_repayment == 0.0
    assert period.dividends_paid == 0.0
    assert period.share_repurchases == 0.0
    assert period.depreciation_amortization == 0.0
    assert period.net_change_in_cash == 0.0


# ---------------------------------------------------------------------------
# CapitalFlowReport dataclass
# ---------------------------------------------------------------------------

def test_capital_flow_report_defaults():
    report = CapitalFlowReport(ticker="TEST")
    assert report.periods == []
    assert report.capex_to_revenue_ratios == []
    assert report.debt_trend == "unknown"
    assert report.dividend_trend == "unknown"
    assert report.repurchase_trend == "unknown"
    assert report.cash_flow_quality == "insufficient data"
    assert report.summary == ""
