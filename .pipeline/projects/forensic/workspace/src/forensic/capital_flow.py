"""Capital flow analysis for SEC filings.

Extracts and analyzes cash flow statement data (operating, investing, financing)
and computes capital flow metrics such as CapEx-to-revenue ratios, debt patterns,
and dividend/repurchase trends.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("forensic.capital_flow")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CashFlowPeriod:
    """Cash flow data for a single reporting period."""
    period_label: str  # e.g. "FY2023", "Q1 2024"
    operating_cash_flow: float = 0.0
    investing_cash_flow: float = 0.0
    financing_cash_flow: float = 0.0
    net_change_in_cash: float = 0.0
    capital_expenditures: float = 0.0
    depreciation_amortization: float = 0.0
    debt_issuance: float = 0.0
    debt_repayment: float = 0.0
    dividends_paid: float = 0.0
    share_repurchases: float = 0.0
    free_cash_flow: float = 0.0

    def __post_init__(self):
        """Derive free cash flow if not explicitly set."""
        if self.free_cash_flow == 0.0:
            self.free_cash_flow = self.operating_cash_flow - self.capital_expenditures


@dataclass
class CapitalFlowReport:
    """Aggregated capital flow analysis report."""
    ticker: str
    periods: List[CashFlowPeriod] = field(default_factory=list)
    capex_to_revenue_ratios: List[Dict[str, object]] = field(default_factory=list)
    debt_trend: str = "unknown"
    dividend_trend: str = "unknown"
    repurchase_trend: str = "unknown"
    cash_flow_quality: str = "unknown"
    summary: str = ""


# ---------------------------------------------------------------------------
# Cash flow extraction helpers
# ---------------------------------------------------------------------------

# Common line-item aliases used across 10-K / 10-Q filings.
_CASH_FLOW_ALIASES = {
    "operating_cash_flow": [
        r"cash provided by operating activities",
        r"cash from operating activities",
        r"net cash from operating activities",
        r"net cash provided by operating activities",
        r"operating cash flow",
        r"cash flows from operating activities",
    ],
    "investing_cash_flow": [
        r"cash used in investing activities",
        r"cash from investing activities",
        r"net cash from investing activities",
        r"net cash used in investing activities",
        r"investing cash flow",
        r"cash flows from investing activities",
    ],
    "financing_cash_flow": [
        r"cash used in financing activities",
        r"cash from financing activities",
        r"net cash from financing activities",
        r"net cash used in financing activities",
        r"financing cash flow",
        r"cash flows from financing activities",
    ],
    "capital_expenditures": [
        r"purchase of property and equipment",
        r"capital expenditures",
        r"capex",
        r"purchases of property",
        r"acquisitions, net",
        r"capital spending",
    ],
    "depreciation_amortization": [
        r"depreciation and amortization",
        r"depreciation expense",
        r"amortization of intangible assets",
    ],
    "debt_issuance": [
        r"proceeds from debt",
        r"proceeds from borrowings",
        r"issuance of debt",
        r"borrowings under",
        r"proceeds from notes",
    ],
    "debt_repayment": [
        r"repayment of debt",
        r"repayments of borrowings",
        r"repayment of notes",
        r"principal payments on debt",
        r"debt repayments",
    ],
    "dividends_paid": [
        r"dividends paid",
        r"dividends payable",
        r"cash dividends",
        r"dividend payments",
    ],
    "share_repurchases": [
        r"share repurchases",
        r"stock repurchases",
        r"repurchase of common stock",
        r"buyback of shares",
        r"repurchased shares",
    ],
}

# Regex to pull a dollar amount (with optional commas and decimals)
_DOLLAR_RE = re.compile(r"\$?([\d,]+(?:\.\d+)?)")


def _extract_dollar_amount(text: str) -> Optional[float]:
    """Return the first dollar amount found in *text*, or None."""
    match = _DOLLAR_RE.search(text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def _find_section(text: str, section_name: str) -> str:
    """Return the text of the first section whose heading contains *section_name*."""
    # Try to split on common section headings like "1. ", "Item 1. ", "Cash Flows"
    patterns = [
        rf"(?:^|\n)\s*{re.escape(section_name)}\s*[:.\n]",
        rf"(?:^|\n)\s*\d+\.\s*{re.escape(section_name)}\s*[:.\n]",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            start = m.start()
            # Grab until the next section heading or end of text
            next_section = re.search(
                r"(?:^|\n)\s*(?:\d+\.\s+)?[A-Z][A-Za-z\s]+[:.\n]",
                text[start + 10:],
                re.MULTILINE,
            )
            if next_section:
                return text[start : start + 10 + next_section.start()]
            return text[start:]
    return ""


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def extract_cash_flow_periods(
    filing_text: str,
    ticker: str = "",
) -> List[CashFlowPeriod]:
    """Extract cash flow statement data from a filing text.

    Looks for the "Cash Flows" section (or equivalent) and parses line items
    for each reporting period (typically FY and quarters).

    Returns a list of *CashFlowPeriod* objects, one per period found.
    """
    # 1. Locate the cash flow section
    cf_section = _find_section(filing_text, "Cash Flows")
    if not cf_section:
        # Fallback: search the entire text
        cf_section = filing_text

    # 2. Split into periods – common delimiters are fiscal year labels
    period_labels = re.findall(
        r"(?:Fiscal\s+)?Year\s+(\d{4})|(?:FY|FYE|Fiscal\s+Year)\s+(\d{4})|(\d{4})",
        cf_section,
    )
    # Flatten and deduplicate
    raw_labels = [lbl for group in period_labels for lbl in group if lbl]
    seen: set[str] = set()
    period_labels = []
    for lbl in raw_labels:
        if lbl not in seen:
            period_labels.append(lbl)
            seen.add(lbl)

    # If no explicit year labels, try quarter labels
    if not period_labels:
        quarter_labels = re.findall(
            r"(?:Q[1-4]\s+)?(\d{4})",
            cf_section,
        )
        for lbl in quarter_labels:
            if lbl not in seen:
                period_labels.append(lbl)
                seen.add(lbl)

    # If still nothing, treat the whole section as one period
    if not period_labels:
        period_labels = ["Unknown"]

    periods: List[CashFlowPeriod] = []
    for label in period_labels:
        period = CashFlowPeriod(period_label=f"FY{label}" if label.isdigit() else label)
        # Extract each line item
        for key, aliases in _CASH_FLOW_ALIASES.items():
            for alias in aliases:
                # Search within the period's portion of the text
                # (simplified: search the whole cf_section for now)
                for m in re.finditer(alias, cf_section, re.IGNORECASE):
                    # Look at a window around the match
                    start = max(0, m.start() - 200)
                    end = min(len(cf_section), m.end() + 200)
                    window = cf_section[start:end]
                    val = _extract_dollar_amount(window)
                    if val is not None:
                        # Use absolute value for cash flow items (sign is context-dependent)
                        setattr(period, key, abs(val))
                        break  # first match wins

        # Derive net change in cash if not present
        period.net_change_in_cash = (
            period.operating_cash_flow
            + period.investing_cash_flow
            + period.financing_cash_flow
        )

        periods.append(period)

    logger.info(
        "Extracted %d cash flow periods for %s",
        len(periods),
        ticker,
    )
    return periods


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def compute_capex_to_revenue_ratios(
    periods: List[CashFlowPeriod],
    revenues: List[float],
) -> List[Dict[str, object]]:
    """Compute CapEx-to-revenue ratios for each period.

    Parameters
    ----------
    periods : list of CashFlowPeriod
    revenues : list of revenue figures (must be same length as *periods*)

    Returns
    -------
    list of dicts with keys "period", "capex", "revenue", "ratio"
    """
    ratios: List[Dict[str, object]] = []
    for i, period in enumerate(periods):
        rev = revenues[i] if i < len(revenues) else 0.0
        if rev > 0 and period.capital_expenditures > 0:
            ratio = period.capital_expenditures / rev
        else:
            ratio = 0.0
        ratios.append({
            "period": period.period_label,
            "capex": period.capital_expenditures,
            "revenue": rev,
            "ratio": ratio,
        })
    return ratios


def _trend(values: List[float]) -> str:
    """Return 'increasing', 'decreasing', or 'stable' based on a list of values."""
    if len(values) < 2:
        return "unknown"
    diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
    avg = sum(diffs) / len(diffs)
    if avg > 0.05 * abs(values[0]) if values[0] else 0:
        return "increasing"
    elif avg < -0.05 * abs(values[0]) if values[0] else 0:
        return "decreasing"
    return "stable"


def analyze_capital_flows(
    periods: List[CashFlowPeriod],
    revenues: Optional[List[float]] = None,
    ticker: str = "",
) -> CapitalFlowReport:
    """Run the full capital flow analysis.

    Parameters
    ----------
    periods : list of CashFlowPeriod
    revenues : optional list of revenue figures (same length as *periods*)
    ticker : ticker symbol for reporting

    Returns
    -------
    CapitalFlowReport
    """
    report = CapitalFlowReport(ticker=ticker)
    report.periods = periods

    # CapEx-to-revenue ratios
    if revenues and len(revenues) == len(periods):
        report.capex_to_revenue_ratios = compute_capex_to_revenue_ratios(periods, revenues)

    # Debt trend
    debt_values = [p.debt_issuance - p.debt_repayment for p in periods]
    report.debt_trend = _trend(debt_values)

    # Dividend trend
    div_values = [p.dividends_paid for p in periods]
    report.dividend_trend = _trend(div_values)

    # Repurchase trend
    rep_values = [p.share_repurchases for p in periods]
    report.repurchase_trend = _trend(rep_values)

    # Cash flow quality heuristic
    # If operating cash flow is consistently lower than net income (not available here),
    # or if investing cash flow is heavily negative while operating is weak, flag it.
    if len(periods) >= 2:
        op_flows = [p.operating_cash_flow for p in periods]
        inv_flows = [p.investing_cash_flow for p in periods]
        if all(f < 0 for f in inv_flows) and all(f > 0 for f in op_flows):
            report.cash_flow_quality = "healthy"
        elif any(f < 0 for f in op_flows):
            report.cash_flow_quality = "concerning"
        else:
            report.cash_flow_quality = "stable"
    else:
        report.cash_flow_quality = "insufficient data"

    # Build summary
    summary_parts: List[str] = []
    if report.capex_to_revenue_ratios:
        avg_ratio = sum(r["ratio"] for r in report.capex_to_revenue_ratios) / len(
            report.capex_to_revenue_ratios
        )
        summary_parts.append(f"Average CapEx/Revenue ratio: {avg_ratio:.2%}")
    summary_parts.append(f"Debt trend: {report.debt_trend}")
    summary_parts.append(f"Dividend trend: {report.dividend_trend}")
    summary_parts.append(f"Share repurchase trend: {report.repurchase_trend}")
    summary_parts.append(f"Cash flow quality: {report.cash_flow_quality}")
    report.summary = "; ".join(summary_parts)

    return report


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def analyze_capital_flow(
    filing_text: str,
    ticker: str = "",
    revenues: Optional[List[float]] = None,
) -> CapitalFlowReport:
    """One-shot: extract cash flow periods and run the full analysis."""
    periods = extract_cash_flow_periods(filing_text, ticker)
    return analyze_capital_flows(periods, revenues, ticker)


# ---------------------------------------------------------------------------
# Capital flow computation and anomaly detection
# ---------------------------------------------------------------------------

@dataclass
class CapitalFlow:
    """A single capital flow event."""
    flow_type: str  # e.g. "insider_purchase", "insider_sale", "institutional_change"
    amount: float
    date: str
    ticker: str = ""
    description: str = ""


def compute_capital_flows(data: Dict[str, object]) -> List[CapitalFlow]:
    """Compute capital flows from raw data.

    Parameters
    ----------
    data : dict
        Dictionary with keys like 'insider_purchases', 'insider_sales',
        'institutional_ownership_change', etc.

    Returns
    -------
    list of CapitalFlow
    """
    flows: List[CapitalFlow] = []
    now = "2023-01-01"  # Default date

    insider_purchases = data.get("insider_purchases", 0)
    if isinstance(insider_purchases, (int, float)) and insider_purchases > 0:
        flows.append(CapitalFlow(
            flow_type="insider_purchase",
            amount=float(insider_purchases),
            date=now,
        ))

    insider_sales = data.get("insider_sales", 0)
    if isinstance(insider_sales, (int, float)) and insider_sales > 0:
        flows.append(CapitalFlow(
            flow_type="insider_sale",
            amount=float(insider_sales),
            date=now,
        ))

    inst_change = data.get("institutional_ownership_change", 0)
    if isinstance(inst_change, (int, float)) and inst_change != 0:
        flows.append(CapitalFlow(
            flow_type="institutional_change",
            amount=float(inst_change),
            date=now,
        ))

    return flows


def detect_anomalies(flows: List[CapitalFlow], threshold: float = 1000000.0) -> List[CapitalFlow]:
    """Detect anomalous capital flows.

    Parameters
    ----------
    flows : list of CapitalFlow
        List of capital flow events.
    threshold : float
        Amount threshold for flagging as anomalous.

    Returns
    -------
    list of CapitalFlow
        Flows that exceed the threshold.
    """
    anomalies: List[CapitalFlow] = []
    for flow in flows:
        if abs(flow.amount) >= threshold:
            anomalies.append(flow)
    return anomalies
