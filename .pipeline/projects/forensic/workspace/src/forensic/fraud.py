"""Fraud analysis module — wraps red-flag detection and scoring."""

from typing import Dict, List, Tuple

from forensic.models import RedFlag, RedFlagSeverity
from forensic.red_flags import run_all_checks
from forensic.scoring import compute_fraud_score, get_risk_level


class FraudAnalyzer:
    """Analyzes text and financial data for fraud indicators."""

    def analyze(
        self,
        text: str = "",
        financial_data: Dict = None,
        cash_flow_data: Dict = None,
        disclosure_text: str = "",
    ) -> Tuple[float, List[RedFlag]]:
        """Run fraud analysis on the given data.

        Returns (fraud_score, red_flags).
        """
        financial_data = financial_data or {}
        cash_flow_data = cash_flow_data or {}

        # Build mock items for red-flag checks
        class MockItem:
            def __init__(self, content: str):
                self.item_content = content

        items = [
            MockItem(text),
            MockItem(disclosure_text),
        ]

        # Add financial data as mock items for pattern matching
        for key, val in financial_data.items():
            items.append(MockItem(f"{key}: {val}"))
        for key, val in cash_flow_data.items():
            items.append(MockItem(f"{key}: {val}"))

        flags = run_all_checks(items)
        score = compute_fraud_score(flags)
        return score, flags
