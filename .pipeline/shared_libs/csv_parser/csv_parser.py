"""CSV invoice parser."""

import csv
import os
import re
from datetime import date, datetime
from typing import List, Optional, Union

from invoice_processor.models import Invoice, LineItem
from invoice_processor.parsers.base import BaseParser


class CSVParser(BaseParser):
    """Parse invoice CSV files."""

    def supports_file(self, file_path: str) -> bool:
        return file_path.lower().endswith('.csv')

    def parse(self, file_path: str) -> Union[Invoice, List[Invoice]]:
        if not os.path.exists(file_path):
            return []

        with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
            content = f.read()

        # Try to detect if this is an invoice CSV
        lines = content.strip().split('\n')
        if not lines:
            return []

        # Parse header row
        reader = csv.reader(lines)
        rows = list(reader)
        if not rows:
            return []

        header = [h.strip().lower() for h in rows[0]]
        data_rows = rows[1:]

        # Detect column mappings
        vendor_col = self._find_column(header, ['vendor', 'company', 'supplier', 'from', 'seller', 'issuer'])
        date_col = self._find_column(header, ['date', 'invoice date', 'issue date', 'dated', 'invoice_date'])
        total_col = self._find_column(header, ['total', 'amount due', 'grand total', 'balance due', 'net total', 'total amount'])
        currency_col = self._find_column(header, ['currency', 'currency code', 'curr'])
        inv_num_col = self._find_column(header, ['invoice number', 'invoice no', 'inv no', 'invoice#', 'invoice_number'])
        inv_id_col = self._find_column(header, ['invoice id', 'invoice_id', 'inv_id', 'id'])

        # Group rows by invoice_id if available
        if inv_id_col is not None:
            groups: dict[str, list] = {}
            for row in data_rows:
                if not any(cell.strip() for cell in row):
                    continue
                inv_id = row[inv_id_col].strip() if len(row) > inv_id_col else ""
                if not inv_id:
                    inv_id = "__default__"
                if inv_id not in groups:
                    groups[inv_id] = []
                groups[inv_id].append(row)
            
            invoices = []
            for inv_id, group_rows in groups.items():
                invoice = self._build_invoice_from_rows(header, group_rows, vendor_col, date_col, total_col, currency_col, inv_num_col, file_path)
                if invoice:
                    invoices.append(invoice)
            # Return single Invoice if only one, otherwise return list
            if len(invoices) == 1:
                return invoices[0]
            return invoices if invoices else []
        else:
            # Single invoice file
            invoice = self._build_invoice_from_rows(header, data_rows, vendor_col, date_col, total_col, currency_col, inv_num_col, file_path)
            return invoice if invoice else []

    def _build_invoice_from_rows(self, header: list, data_rows: list, vendor_col: Optional[int], date_col: Optional[int], total_col: Optional[int], currency_col: Optional[int], inv_num_col: Optional[int], file_path: str) -> Optional[Invoice]:
        """Build an Invoice from a group of data rows."""
        # Extract vendor
        vendor = ""
        if vendor_col is not None:
            for row in data_rows:
                if len(row) > vendor_col:
                    val = row[vendor_col].strip()
                    if val:
                        vendor = val
                        break

        # Extract date
        invoice_date = None
        if date_col is not None:
            for row in data_rows:
                if len(row) > date_col:
                    val = row[date_col].strip()
                    if val:
                        invoice_date = self._parse_date(val)
                        break

        # Extract total (sum of all rows if no explicit total column)
        total = 0.0
        if total_col is not None:
            for row in data_rows:
                if len(row) > total_col:
                    val = row[total_col].strip()
                    if val:
                        total = self._parse_number(val)
                        break
        else:
            # Sum line item amounts
            qty_col = self._find_column(header, ['qty', 'quantity', 'count', 'units'])
            price_col = self._find_column(header, ['price', 'unit price', 'rate', 'cost', 'unit_price'])
            amount_col = self._find_column(header, ['amount', 'total', 'line total', 'subtotal'])
            for row in data_rows:
                if not any(cell.strip() for cell in row):
                    continue
                amount = 0.0
                if amount_col is not None and len(row) > amount_col:
                    amount = self._parse_number(row[amount_col])
                elif qty_col is not None and price_col is not None:
                    if len(row) > qty_col and len(row) > price_col:
                        qty = self._parse_number(row[qty_col])
                        price = self._parse_number(row[price_col])
                        amount = qty * price
                total += amount

        # Extract currency
        currency = "USD"
        if currency_col is not None:
            for row in data_rows:
                if len(row) > currency_col:
                    val = row[currency_col].strip()
                    if val:
                        currency = val
                        break

        # Extract invoice number
        invoice_number = ""
        if inv_num_col is not None:
            for row in data_rows:
                if len(row) > inv_num_col:
                    val = row[inv_num_col].strip()
                    if val:
                        invoice_number = val
                        break

        # Extract line items from remaining columns
        line_items = self._extract_line_items_from_csv(header, data_rows, file_path)

        if not total and not vendor:
            return None

        return Invoice(
            vendor=vendor or "Unknown",
            invoice_date=invoice_date or date(1970, 1, 1),
            total=total,
            currency=currency,
            line_items=line_items,
            source_file=file_path,
            invoice_number=invoice_number,
        )

    def _find_column(self, header: list, candidates: list) -> Optional[int]:
        """Find the index of a column matching any candidate name."""
        for i, col in enumerate(header):
            for candidate in candidates:
                if candidate in col:
                    return i
        return None

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse a date string into a date object."""
        for fmt in ('%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y',
                    '%Y-%m-%d', '%Y/%m/%d', '%B %d, %Y', '%b %d, %Y'):
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None

    def _parse_number(self, num_str: str) -> float:
        """Parse a number string, handling currency symbols and commas."""
        cleaned = re.sub(r'[^\d.\-]', '', num_str)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _extract_line_items_from_csv(self, header: list, data_rows: list, file_path: str = "") -> list:
        """Extract line items from CSV data rows."""
        items = []
        # Find columns that look like they contain line item data
        qty_col = self._find_column(header, ['qty', 'quantity', 'count', 'units'])
        price_col = self._find_column(header, ['price', 'unit price', 'rate', 'cost', 'unit_price'])
        amount_col = self._find_column(header, ['amount', 'total', 'line total', 'subtotal'])
        desc_col = self._find_column(header, ['description', 'item', 'desc', 'details', 'item description'])

        for row in data_rows:
            if not any(cell.strip() for cell in row):
                continue

            desc = ""
            if desc_col is not None and len(row) > desc_col:
                desc = row[desc_col].strip()

            qty = 0.0
            if qty_col is not None and len(row) > qty_col:
                qty = self._parse_number(row[qty_col])

            unit_price = 0.0
            if price_col is not None and len(row) > price_col:
                unit_price = self._parse_number(row[price_col])

            amount = 0.0
            if amount_col is not None and len(row) > amount_col:
                amount = self._parse_number(row[amount_col])
            elif qty > 0 and unit_price > 0:
                amount = qty * unit_price

            if desc or qty > 0 or unit_price > 0 or amount > 0:
                items.append(LineItem(
                    description=desc or "Item",
                    quantity=qty,
                    unit_price=unit_price,
                    amount=amount,
                    source_file=file_path,
                ))

        return items
