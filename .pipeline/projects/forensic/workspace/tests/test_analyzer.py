"""Tests for forensic analyzer."""

import pytest
from forensic.analyzer import FraudAnalyzer, TextPatternAnalyzer, FinancialRatioAnalyzer
from forensic.models import RedFlagSeverity


class TestTextPatternAnalyzer:
    def test_fraud_mention(self):
        analyzer = TextPatternAnalyzer()
        flags = analyzer.analyze("The company admitted to fraud in the financial statements.")
        assert len(flags) > 0
        assert any(f.category == "text_pattern" for f in flags)

    def test_restatement_mention(self):
        analyzer = TextPatternAnalyzer()
        flags = analyzer.analyze("The company restated its financial results.")
        assert len(flags) > 0

    def test_no_suspicious_patterns(self):
        analyzer = TextPatternAnalyzer()
        flags = analyzer.analyze("The company reported strong revenue growth.")
        assert len(flags) == 0


class TestFinancialRatioAnalyzer:
    def test_high_expense_ratio(self):
        analyzer = FinancialRatioAnalyzer()
        financial_data = {
            "revenue": 1000,
            "expenses": 960,
        }
        flags = analyzer.analyze(financial_data)
        assert len(flags) > 0
        assert any("Expense ratio" in f.description for f in flags)

    def test_normal_expense_ratio(self):
        analyzer = FinancialRatioAnalyzer()
        financial_data = {
            "revenue": 1000,
            "expenses": 500,
        }
        flags = analyzer.analyze(financial_data)
        assert len(flags) == 0


class TestFraudAnalyzer:
    def test_analyze_with_text(self):
        analyzer = FraudAnalyzer()
        score, flags = analyzer.analyze(text="The company committed fraud.")
        assert score > 0
        assert len(flags) > 0

    def test_analyze_with_no_issues(self):
        analyzer = FraudAnalyzer()
        score, flags = analyzer.analyze(text="The company reported strong results.")
        assert score == 0
        assert len(flags) == 0

    def test_analyze_with_financial_data(self):
        analyzer = FraudAnalyzer()
        score, flags = analyzer.analyze(
            financial_data={
                "revenue": 1000,
                "expenses": 960,
            }
        )
        assert score > 0

    def test_analyze_with_all_data(self):
        analyzer = FraudAnalyzer()
        score, flags = analyzer.analyze(
            text="The company committed fraud and restated results.",
            financial_data={
                "revenue": 1000,
                "expenses": 960,
            },
            cash_flow_data={
                "net_income": 100,
                "operating_cash_flow": -50,
            },
            disclosure_text="Risk factors are important.",
        )
        assert score > 0
        assert len(flags) > 0
