"""Unit tests for CSV parser (parse_csv) and PDF parser (parse_pdf)."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from financial_document_analyzer.parsers import parse_csv, parse_pdf


# ─────────────────────────────────────────────────────────────────────────────
# parse_csv tests
# ─────────────────────────────────────────────────────────────────────────────

class TestParseCSV:
    """Tests for the parse_csv function."""

    def _write_csv(self, content: str) -> str:
        """Helper to write CSV content to a temp file and return its path."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_standard_format_csv(self):
        """Test parsing a standard financial CSV."""
        csv_content = """Line Item,2024,2023
Revenue,50000000,45000000
Cost of Goods Sold,30000000,28000000
Gross Profit,20000000,17000000
Operating Income,8000000,6500000
Net Income,5500000,4200000"""
        path = self._write_csv(csv_content)
        try:
            result = parse_csv(path)
            assert result["filename"] == os.path.basename(path)
            assert result["metrics"]["revenue"] == 50000000
            assert result["metrics"]["cogs"] == 30000000
            assert result["metrics"]["gross_profit"] == 20000000
            assert result["metrics"]["operating_income"] == 8000000
            assert result["metrics"]["net_income"] == 5500000
            assert result["raw_rows"] > 0
        finally:
            os.unlink(path)

    def test_transposed_csv(self):
        """Test parsing a transposed CSV (metrics as columns)."""
        csv_content = """Item,Revenue,Cost of Goods Sold,Gross Profit,Operating Income,Net Income
2024,50000000,30000000,20000000,8000000,5500000
2023,45000000,28000000,17000000,6500000,4200000"""
        path = self._write_csv(csv_content)
        try:
            result = parse_csv(path)
            assert result["metrics"]["revenue"] == 50000000
            assert result["metrics"]["cogs"] == 30000000
            assert result["metrics"]["gross_profit"] == 20000000
            assert result["metrics"]["operating_income"] == 8000000
            assert result["metrics"]["net_income"] == 5500000
        finally:
            os.unlink(path)

    def test_missing_gross_profit_uses_fallback(self):
        """Test that missing gross profit is computed from revenue - cogs."""
        csv_content = """Line Item,2024,2023
Revenue,50000000,45000000
Cost of Goods Sold,30000000,28000000
Operating Income,8000000,6500000
Net Income,5500000,4200000"""
        path = self._write_csv(csv_content)
        try:
            result = parse_csv(path)
            assert result["metrics"]["gross_profit"] == 20000000  # 50M - 30M
        finally:
            os.unlink(path)

    def test_missing_columns_returns_zero(self):
        """Test that missing columns return 0.0."""
        csv_content = """Line Item,2024,2023
Revenue,50000000,45000000"""
        path = self._write_csv(csv_content)
        try:
            result = parse_csv(path)
            assert result["metrics"]["revenue"] == 50000000
            assert result["metrics"]["cogs"] == 0.0
            assert result["metrics"]["gross_profit"] == 0.0
        finally:
            os.unlink(path)

    def test_nonexistent_file_raises_error(self):
        """Test that a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_csv("/nonexistent/file.csv")

    def test_csv_with_currency_symbols(self):
        """Test parsing CSV values with currency symbols and commas."""
        # Values with commas must be quoted in CSV
        csv_content = """Line Item,2024,2023
Revenue,"$1,234,567","$1,100,000"
Cost of Goods Sold,"$600,000","$550,000"
Gross Profit,"$634,567","$550,000"
Operating Income,"$200,000","$180,000"
Net Income,"$150,000","$130,000"
"""
        path = self._write_csv(csv_content)
        try:
            result = parse_csv(path)
            assert result["metrics"]["revenue"] == 1234567
            assert result["metrics"]["cogs"] == 600000
            assert result["metrics"]["gross_profit"] == 634567
            assert result["metrics"]["operating_income"] == 200000
            assert result["metrics"]["net_income"] == 150000
        finally:
            os.unlink(path)

    def test_csv_with_parenthetical_negatives(self):
        """Test parsing CSV values with parenthetical negatives."""
        csv_content = """Line Item,2024,2023
Revenue,1000000,900000
Cost of Goods Sold,(500000),450000
Gross Profit,500000,450000
Operating Income,(100000),80000
Net Income,(150000),60000
"""
        path = self._write_csv(csv_content)
        try:
            result = parse_csv(path)
            assert result["metrics"]["revenue"] == 1000000
            assert result["metrics"]["cogs"] == -500000
            assert result["metrics"]["operating_income"] == -100000
            assert result["metrics"]["net_income"] == -150000
        finally:
            os.unlink(path)

    def test_empty_csv_file(self):
        """Test parsing an empty CSV file."""
        path = self._write_csv("")
        try:
            result = parse_csv(path)
            assert result["metrics"]["revenue"] == 0.0
            assert result["metrics"]["cogs"] == 0.0
        finally:
            os.unlink(path)

    def test_csv_header_only(self):
        """Test parsing a CSV with only headers."""
        csv_content = """Line Item,2024,2023"""
        path = self._write_csv(csv_content)
        try:
            result = parse_csv(path)
            assert result["metrics"]["revenue"] == 0.0
        finally:
            os.unlink(path)

    def test_margins_are_computed(self):
        """Test that margins are correctly computed."""
        csv_content = """Line Item,2024,2023
Revenue,1000000,900000
Cost of Goods Sold,600000,540000
Gross Profit,400000,360000
Operating Income,200000,180000
Net Income,100000,90000"""
        path = self._write_csv(csv_content)
        try:
            result = parse_csv(path)
            assert result["margins"]["gross_margin"] == 40.0
            assert result["margins"]["operating_margin"] == 20.0
            assert result["margins"]["net_margin"] == 10.0
        finally:
            os.unlink(path)


# ─────────────────────────────────────────────────────────────────────────────
# parse_pdf tests
# ─────────────────────────────────────────────────────────────────────────────

class TestParsePDF:
    """Tests for the parse_pdf function."""

    def _write_pdf(self, content: str) -> str:
        """Helper to write a minimal PDF to a temp file and return its path."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_pdf_with_financial_table(self):
        """Test parsing a PDF with a financial table."""
        pdf_content = "%PDF-1.4\nfake pdf content"
        path = self._write_pdf(pdf_content)
        try:
            mock_table = [
                ["Line Item", "2024", "2023"],
                ["Revenue", "50000000", "45000000"],
                ["Cost of Goods Sold", "30000000", "28000000"],
                ["Gross Profit", "20000000", "17000000"],
                ["Operating Income", "8000000", "6500000"],
                ["Net Income", "5500000", "4200000"],
            ]
            mock_page = MagicMock()
            mock_page.extract_tables.return_value = [mock_table]
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]

            with patch("financial_document_analyzer.parsers.pdfplumber") as mock_plumber:
                mock_plumber.open.return_value.__enter__.return_value = mock_pdf
                result = parse_pdf(path)
                assert result["metrics"]["revenue"] == 50000000
                assert result["metrics"]["cogs"] == 30000000
                assert result["metrics"]["gross_profit"] == 20000000
                assert result["metrics"]["operating_income"] == 8000000
                assert result["metrics"]["net_income"] == 5500000
        finally:
            os.unlink(path)

    def test_pdf_with_currency_symbols(self):
        """Test parsing a PDF with currency symbols."""
        pdf_content = "%PDF-1.4\nfake pdf content"
        path = self._write_pdf(pdf_content)
        try:
            mock_table = [
                ["Line Item", "2024", "2023"],
                ["Revenue", "$1,234,567", "$1,100,000"],
                ["Cost of Goods Sold", "$600,000", "$550,000"],
                ["Gross Profit", "$634,567", "$550,000"],
                ["Operating Income", "$200,000", "$180,000"],
                ["Net Income", "$150,000", "$130,000"],
            ]
            mock_page = MagicMock()
            mock_page.extract_tables.return_value = [mock_table]
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]

            with patch("financial_document_analyzer.parsers.pdfplumber") as mock_plumber:
                mock_plumber.open.return_value.__enter__.return_value = mock_pdf
                result = parse_pdf(path)
                assert result["metrics"]["revenue"] == 1234567
                assert result["metrics"]["cogs"] == 600000
        finally:
            os.unlink(path)

    def test_pdf_with_parenthetical_negatives(self):
        """Test parsing a PDF with parenthetical negatives."""
        pdf_content = "%PDF-1.4\nfake pdf content"
        path = self._write_pdf(pdf_content)
        try:
            mock_table = [
                ["Line Item", "2024", "2023"],
                ["Revenue", "1000000", "900000"],
                ["Cost of Goods Sold", "(500000)", "450000"],
                ["Gross Profit", "500000", "450000"],
                ["Operating Income", "(100000)", "80000"],
                ["Net Income", "(150000)", "60000"],
            ]
            mock_page = MagicMock()
            mock_page.extract_tables.return_value = [mock_table]
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]

            with patch("financial_document_analyzer.parsers.pdfplumber") as mock_plumber:
                mock_plumber.open.return_value.__enter__.return_value = mock_pdf
                result = parse_pdf(path)
                assert result["metrics"]["revenue"] == 1000000
                assert result["metrics"]["cogs"] == -500000
                assert result["metrics"]["operating_income"] == -100000
                assert result["metrics"]["net_income"] == -150000
        finally:
            os.unlink(path)

    def test_pdf_with_transposed_table(self):
        """Test parsing a PDF with a transposed table."""
        pdf_content = "%PDF-1.4\nfake pdf content"
        path = self._write_pdf(pdf_content)
        try:
            mock_table = [
                ["Item", "Revenue", "Cost of Goods Sold", "Gross Profit", "Operating Income", "Net Income"],
                ["2024", "50000000", "30000000", "20000000", "8000000", "5500000"],
                ["2023", "45000000", "28000000", "17000000", "6500000", "4200000"],
            ]
            mock_page = MagicMock()
            mock_page.extract_tables.return_value = [mock_table]
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]

            with patch("financial_document_analyzer.parsers.pdfplumber") as mock_plumber:
                mock_plumber.open.return_value.__enter__.return_value = mock_pdf
                result = parse_pdf(path)
                assert result["metrics"]["revenue"] == 50000000
                assert result["metrics"]["cogs"] == 30000000
        finally:
            os.unlink(path)

    def test_pdf_with_no_tables(self):
        """Test parsing a PDF with no tables raises ValueError."""
        pdf_content = "%PDF-1.4\nfake pdf content"
        path = self._write_pdf(pdf_content)
        try:
            mock_page = MagicMock()
            mock_page.extract_tables.return_value = []
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]

            with patch("financial_document_analyzer.parsers.pdfplumber") as mock_plumber:
                mock_plumber.open.return_value.__enter__.return_value = mock_pdf
                with pytest.raises(ValueError, match="No tables found"):
                    parse_pdf(path)
        finally:
            os.unlink(path)

    def test_pdf_with_empty_table(self):
        """Test parsing a PDF with an empty table raises ValueError."""
        pdf_content = "%PDF-1.4\nfake pdf content"
        path = self._write_pdf(pdf_content)
        try:
            mock_table = [
                ["Line Item", "2024", "2023"],
                ["", "", ""],
                ["", "", ""],
            ]
            mock_page = MagicMock()
            mock_page.extract_tables.return_value = [mock_table]
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]

            with patch("financial_document_analyzer.parsers.pdfplumber") as mock_plumber:
                mock_plumber.open.return_value.__enter__.return_value = mock_pdf
                with pytest.raises(ValueError, match="No tables found"):
                    parse_pdf(path)
        finally:
            os.unlink(path)

    def test_pdf_with_mixed_numeric_and_text(self):
        """Test parsing a PDF with mixed numeric and text values."""
        pdf_content = "%PDF-1.4\nfake pdf content"
        path = self._write_pdf(pdf_content)
        try:
            mock_table = [
                ["Line Item", "2024", "2023"],
                ["Revenue", "50,000,000", "45,000,000"],
                ["Cost of Goods Sold", "30,000,000", "28,000,000"],
                ["Gross Profit", "20,000,000", "17,000,000"],
                ["Operating Income", "8,000,000", "6,500,000"],
                ["Net Income", "5,500,000", "4,200,000"],
            ]
            mock_page = MagicMock()
            mock_page.extract_tables.return_value = [mock_table]
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]

            with patch("financial_document_analyzer.parsers.pdfplumber") as mock_plumber:
                mock_plumber.open.return_value.__enter__.return_value = mock_pdf
                result = parse_pdf(path)
                assert result["metrics"]["revenue"] == 50000000
                assert result["metrics"]["cogs"] == 30000000
        finally:
            os.unlink(path)

    def test_pdf_filename_extraction(self):
        """Test that the filename is correctly extracted from the path."""
        pdf_content = "%PDF-1.4\nfake pdf content"
        path = self._write_pdf(pdf_content)
        try:
            mock_table = [
                ["Line Item", "2024"],
                ["Revenue", "50000000"],
            ]
            mock_page = MagicMock()
            mock_page.extract_tables.return_value = [mock_table]
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]

            with patch("financial_document_analyzer.parsers.pdfplumber") as mock_plumber:
                mock_plumber.open.return_value.__enter__.return_value = mock_pdf
                result = parse_pdf(path)
                assert result["filename"] == os.path.basename(path)
        finally:
            os.unlink(path)
