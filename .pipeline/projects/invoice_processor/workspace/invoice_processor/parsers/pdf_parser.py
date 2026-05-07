"""PDF invoice parser using PyMuPDF for text extraction."""

import os
import re
from datetime import datetime
from typing import List, Optional, Union

import fitz  # PyMuPDF

from invoice_processor.exceptions import ParsingError
from invoice_processor.models import Invoice, LineItem
from invoice_processor.parsers.base import BaseParser


class PDFParser(BaseParser):
    """Parse invoice PDF files using PyMuPDF."""

    def supports_file(self, file_path: str) -> bool:
        return file_path.lower().endswith('.pdf')

    def parse(self, file_path: str) -> Optional[Invoice]:
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            raise ParsingError(file_path, f"Failed to read PDF: {e}")

        invoice = self._parse_text(text, file_path)
        return invoice

    def _parse_text(self, text: str, source_file: str) -> Optional[Invoice]:
        """Extract invoice fields from PDF text content."""
        vendor = self._extract_vendor(text)
        invoice_date = self._extract_date(text)
        total = self._extract_total(text)
        currency = self._extract_currency(text)
        line_items = self._extract_line_items(text, source_file)
        invoice_number = self._extract_invoice_number(text)

        # Need at least a total or vendor to be useful
        if not total and not vendor:
            return None

        return Invoice(
            vendor=vendor or "Unknown",
            invoice_date=invoice_date or datetime.now().date(),
            total=total or 0.0,
            currency=currency or "USD",
            line_items=line_items,
            source_file=source_file,
            invoice_number=invoice_number or "",
        )

    def _extract_vendor(self, text: str) -> str:
        """Extract vendor name from text."""
        patterns = [
            r'(?:from|vendor|company|bill\s*from)\s*[:\-]?\s*(.+?)(?:\n|$)',
            r'(?:issued\s*by|issuer)\s*[:\-]?\s*(.+?)(?:\n|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        # Try first non-empty line as fallback
        first_line = text.strip().split('\n')[0].strip()
        if first_line and len(first_line) < 100:
            return first_line
        return ""

    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract invoice date from text."""
        patterns = [
            r'(?:invoice\s*date|date\s*(?:of|on)|issue\s*date|dated?)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:date)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                for fmt in ('%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y',
                            '%Y-%m-%d', '%Y/%m/%d'):
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
        return None

    def _extract_total(self, text: str) -> float:
        """Extract total amount from text."""
        patterns = [
            r'(?:total|amount\s*due|grand\s*total|balance\s*due|net\s*total)\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)',
            r'(?:total)\s*[:\-]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
        return 0.0

    def _extract_currency(self, text: str) -> str:
        """Extract currency from text."""
        currency_patterns = [
            r'\b(USD|EUR|GBP|CAD|AUD|JPY|CHF|INR|CNY)\b',
        ]
        for pattern in currency_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return "USD"

    def _extract_line_items(self, text: str, source_file: str) -> list:
        """Extract line items from text."""
        items = []
        # Look for tabular data: lines with description, qty, price, amount
        # Pattern: description (text), number, number, number
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Try to match: text, number, number, number
            match = re.match(
                r'(.+?)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)',
                line
            )
            if match:
                desc = match.group(1).strip()
                # Skip header-like lines
                if desc.lower() in ('description', 'item', 'qty', 'quantity',
                                    'unit', 'price', 'amount', 'total',
                                    'rate', 'cost'):
                    continue
                try:
                    qty = float(match.group(2).replace(',', ''))
                    unit_price = float(match.group(3).replace(',', ''))
                    amount = float(match.group(4).replace(',', ''))
                    items.append(LineItem(
                        description=desc,
                        quantity=qty,
                        unit_price=unit_price,
                        amount=amount,
                        source_file=source_file,
                    ))
                except ValueError:
                    continue
        return items

    def _extract_invoice_number(self, text: str) -> str:
        """Extract invoice number from text."""
        patterns = [
            r'(?:invoice\s*(?:no|#)|inv\s*(?:no|#)|number)\s*[:\-]?\s*(\w+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""
