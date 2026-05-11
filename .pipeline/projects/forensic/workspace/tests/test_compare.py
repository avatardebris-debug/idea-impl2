"""Tests for multi-company comparison module."""

import pytest
from forensic.compare import (
    ComparativeResult,
    compare_companies,
    generate_comparative_report,
    generate_comparative_json,
)


class TestCompareCompanies:
    def test_basic_comparison(self):
        tickers = ["AAPL", "GOOG"]
        ticker_data = {
            "AAPL": {
                "cik": "000001",
                "accession_no": "001",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $1,000,000\nNet income $200,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
            "GOOG": {
                "cik": "000002",
                "accession_no": "002",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $2,000,000\nNet income $300,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
        }
        result = compare_companies(tickers, ticker_data)
        assert len(result.companies) == 2
        assert len(result.rankings) == 2
        assert result.companies[0]["ticker"] in tickers
        assert result.rankings[0][0] in tickers

    def test_empty_tickers(self):
        result = compare_companies([], {})
        assert len(result.warnings) > 0
        assert len(result.companies) == 0

    def test_missing_ticker_data(self):
        tickers = ["AAPL", "MISSING"]
        ticker_data = {
            "AAPL": {
                "cik": "000001",
                "accession_no": "001",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $1,000,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
        }
        result = compare_companies(tickers, ticker_data)
        assert len(result.companies) == 2
        assert result.companies[1]["ticker"] == "MISSING"

    def test_with_earnings_data(self):
        tickers = ["AAPL"]
        ticker_data = {
            "AAPL": {
                "cik": "000001",
                "accession_no": "001",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $1,000,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
        }
        earnings_data = {
            "AAPL": [
                {"quarter": "2023-Q1", "eps": 1.5, "revenue": 100.0, "accession_no": "001", "filing_date": "2023-03-01"},
                {"quarter": "2023-Q2", "eps": 1.8, "revenue": 110.0, "accession_no": "002", "filing_date": "2023-06-01"},
                {"quarter": "2023-Q3", "eps": 2.0, "revenue": 120.0, "accession_no": "003", "filing_date": "2023-09-01"},
            ]
        }
        result = compare_companies(tickers, ticker_data, earnings_data=earnings_data)
        assert len(result.earnings_reports) == 1
        assert result.earnings_reports[0].ticker == "AAPL"

    def test_no_earnings_data_warning(self):
        tickers = ["AAPL"]
        ticker_data = {
            "AAPL": {
                "cik": "000001",
                "accession_no": "001",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $1,000,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
        }
        result = compare_companies(tickers, ticker_data)
        assert any("No earnings data" in w for w in result.warnings)

    def test_rankings_sorted_by_fraud_score(self):
        tickers = ["AAPL", "GOOG"]
        ticker_data = {
            "AAPL": {
                "cik": "000001",
                "accession_no": "001",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $1,000,000\nNet income $200,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
            "GOOG": {
                "cik": "000002",
                "accession_no": "002",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $2,000,000\nNet income $300,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
        }
        result = compare_companies(tickers, ticker_data)
        scores = [s for _, s in result.rankings]
        assert scores == sorted(scores, reverse=True)

    def test_to_dict(self):
        tickers = ["AAPL"]
        ticker_data = {
            "AAPL": {
                "cik": "000001",
                "accession_no": "001",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $1,000,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
        }
        result = compare_companies(tickers, ticker_data)
        d = result.to_dict()
        assert "companies" in d
        assert "rankings" in d
        assert "earnings_reports" in d
        assert "warnings" in d


class TestGenerateComparativeReport:
    def test_basic_report(self):
        tickers = ["AAPL"]
        ticker_data = {
            "AAPL": {
                "cik": "000001",
                "accession_no": "001",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $1,000,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
        }
        result = compare_companies(tickers, ticker_data)
        report = generate_comparative_report(result)
        assert "FORENSIC COMPARATIVE REPORT" in report
        assert "FRAUD RISK RANKINGS" in report
        assert "PER-COMPANY DETAILS" in report
        assert "AAPL" in report

    def test_report_with_earnings(self):
        tickers = ["AAPL"]
        ticker_data = {
            "AAPL": {
                "cik": "000001",
                "accession_no": "001",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $1,000,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
        }
        earnings_data = {
            "AAPL": [
                {"quarter": "2023-Q1", "eps": 1.5, "revenue": 100.0, "accession_no": "001", "filing_date": "2023-03-01"},
                {"quarter": "2023-Q2", "eps": 1.8, "revenue": 110.0, "accession_no": "002", "filing_date": "2023-06-01"},
                {"quarter": "2023-Q3", "eps": 2.0, "revenue": 120.0, "accession_no": "003", "filing_date": "2023-09-01"},
            ]
        }
        result = compare_companies(tickers, ticker_data, earnings_data=earnings_data)
        report = generate_comparative_report(result)
        assert "EARNINGS PREDICTIONS" in report

    def test_report_with_warnings(self):
        result = ComparativeResult()
        result.warnings.append("Test warning")
        report = generate_comparative_report(result)
        assert "WARNINGS" in report
        assert "Test warning" in report


class TestGenerateComparativeJson:
    def test_basic_json(self):
        tickers = ["AAPL"]
        ticker_data = {
            "AAPL": {
                "cik": "000001",
                "accession_no": "001",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $1,000,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
        }
        result = compare_companies(tickers, ticker_data)
        json_str = generate_comparative_json(result)
        import json
        d = json.loads(json_str)
        assert "companies" in d
        assert "rankings" in d
        assert "earnings_reports" in d
        assert "warnings" in d

    def test_json_with_earnings(self):
        tickers = ["AAPL"]
        ticker_data = {
            "AAPL": {
                "cik": "000001",
                "accession_no": "001",
                "filing_date": "2024-01-01",
                "text_parts": ["Revenue $1,000,000"],
                "financial_data": {},
                "cash_flow_data": {},
                "disclosure_text": "",
            },
        }
        earnings_data = {
            "AAPL": [
                {"quarter": "2023-Q1", "eps": 1.5, "revenue": 100.0, "accession_no": "001", "filing_date": "2023-03-01"},
                {"quarter": "2023-Q2", "eps": 1.8, "revenue": 110.0, "accession_no": "002", "filing_date": "2023-06-01"},
                {"quarter": "2023-Q3", "eps": 2.0, "revenue": 120.0, "accession_no": "003", "filing_date": "2023-09-01"},
            ]
        }
        result = compare_companies(tickers, ticker_data, earnings_data=earnings_data)
        json_str = generate_comparative_json(result)
        import json
        d = json.loads(json_str)
        assert len(d["earnings_reports"]) == 1
