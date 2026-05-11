"""CSV import pipeline for BudgetFlow Tracker."""

from __future__ import annotations

import csv
import io
import logging
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from src.core.database import Database

logger = logging.getLogger(__name__)


@dataclass
class BankFormat:
    """Detected bank statement format."""
    name: str
    date_column: str
    description_column: str
    amount_column: str
    date_format: str
    amount_negative_is_debit: bool = True


# Supported bank formats
BANK_FORMATS = {
    "chase": BankFormat(
        name="Chase",
        date_column="Date",
        description_column="Description",
        amount_column="Amount",
        date_format="%m/%d/%Y",
    ),
    "wells_fargo": BankFormat(
        name="Wells Fargo",
        date_column="Date",
        description_column="Description",
        amount_column="Amount",
        date_format="%m/%d/%Y",
    ),
    "bank_of_america": BankFormat(
        name="Bank of America",
        date_column="Date",
        description_column="Description",
        amount_column="Amount",
        date_format="%m/%d/%Y",
    ),
    "generic": BankFormat(
        name="Generic CSV",
        date_column="date",
        description_column="description",
        amount_column="amount",
        date_format="%Y-%m-%d",
    ),
}


@dataclass
class ParsedTransaction:
    """A transaction parsed from a bank statement."""
    date: date
    description: str
    amount: Decimal
    raw_row: dict[str, str]


class CSVParser:
    """Parse bank statement CSV files and detect formats."""

    def __init__(self, db: Database):
        self.db = db

    def detect_format(self, csv_content: str) -> BankFormat:
        """Detect the bank format from CSV content.

        Args:
            csv_content: Raw CSV string content.

        Returns:
            Detected BankFormat.
        """
        lines = csv_content.strip().split("\n")
        if not lines:
            return BANK_FORMATS["generic"]

        # Read header
        reader = csv.reader(io.StringIO(lines[0]))
        header = next(reader)
        header_lower = [h.strip().lower() for h in header]

        # Check for known formats by looking for specific column names
        for format_name, fmt in BANK_FORMATS.items():
            if format_name == "generic":
                continue
            if (
                fmt.date_column.lower() in header_lower
                and fmt.description_column.lower() in header_lower
                and fmt.amount_column.lower() in header_lower
            ):
                return fmt

        # Try to auto-detect by looking for common column patterns
        date_col = self._find_column(header_lower, ["date", "posting date", "transaction date"])
        desc_col = self._find_column(header_lower, ["description", "merchant", "payee", "details"])
        amount_col = self._find_column(header_lower, ["amount", "debit", "credit", "withdrawal", "deposit"])

        if date_col and desc_col and amount_col:
            # Determine date format from sample data
            sample_date = self._get_sample_value(lines, date_col)
            date_format = self._detect_date_format(sample_date)

            # Determine if negative amounts are debits
            sample_amount = self._get_sample_value(lines, amount_col)
            negative_is_debit = self._detect_amount_sign(lines, amount_col)

            return BankFormat(
                name="Auto-detected",
                date_column=header[date_col],
                description_column=header[desc_col],
                amount_column=header[amount_col],
                date_format=date_format,
                amount_negative_is_debit=negative_is_debit,
            )

        return BANK_FORMATS["generic"]

    def _find_column(self, header: list[str], candidates: list[str]) -> Optional[int]:
        """Find the index of a column matching any candidate name."""
        for i, col in enumerate(header):
            for candidate in candidates:
                if candidate in col:
                    return i
        return None

    def _get_sample_value(self, lines: list[str], col_index: int) -> str:
        """Get a sample value from a column."""
        reader = csv.reader(io.StringIO("\n".join(lines[1:3])))
        for row in reader:
            if col_index < len(row):
                return row[col_index].strip()
        return ""

    def _detect_date_format(self, sample_date: str) -> str:
        """Detect date format from a sample date string."""
        if not sample_date:
            return "%Y-%m-%d"

        # Try common formats
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%b %d, %Y", "%d/%m/%Y"]
        for fmt in formats:
            try:
                date.strptime(sample_date, fmt)
                return fmt
            except ValueError:
                continue
        return "%Y-%m-%d"

    def _detect_amount_sign(self, lines: list[str], col_index: int) -> bool:
        """Detect if negative amounts represent debits."""
        reader = csv.reader(io.StringIO("\n".join(lines[1:6])))
        for row in reader:
            if col_index < len(row):
                val = row[col_index].strip().replace(",", "").replace("$", "").replace(" ", "")
                if val:
                    try:
                        amt = float(val)
                        return amt < 0
                    except ValueError:
                        continue
        return True

    def parse(self, csv_content: str, bank_format: Optional[BankFormat] = None) -> list[ParsedTransaction]:
        """Parse CSV content into transactions.

        Args:
            csv_content: Raw CSV string content.
            bank_format: Optional detected format. If None, auto-detect.

        Returns:
            List of ParsedTransaction objects.
        """
        if bank_format is None:
            bank_format = self.detect_format(csv_content)

        lines = csv_content.strip().split("\n")
        if len(lines) < 2:
            return []

        # Find column indices
        reader = csv.reader(io.StringIO(lines[0]))
        header = next(reader)
        header_lower = [h.strip().lower() for h in header]

        date_idx = header_lower.index(bank_format.date_column.lower())
        desc_idx = header_lower.index(bank_format.description_column.lower())
        amount_idx = header_lower.index(bank_format.amount_column.lower())

        transactions = []
        reader = csv.reader(io.StringIO("\n".join(lines[1:])))
        for row in reader:
            if len(row) <= max(date_idx, desc_idx, amount_idx):
                continue

            # Parse date
            date_str = row[date_idx].strip()
            try:
                parsed_date = date.strptime(date_str, bank_format.date_format)
            except ValueError:
                # Try alternative formats
                parsed_date = self._try_parse_date(date_str)
                if parsed_date is None:
                    continue

            # Parse description
            description = row[desc_idx].strip()

            # Parse amount
            amount_str = row[amount_idx].strip().replace(",", "").replace("$", "").replace(" ", "")
            try:
                amount = Decimal(amount_str)
            except InvalidOperation:
                continue

            # Apply sign convention
            if bank_format.amount_negative_is_debit and amount > 0:
                amount = -amount

            transactions.append(ParsedTransaction(
                date=parsed_date,
                description=description,
                amount=amount,
                raw_row=dict(zip(header, row)),
            ))

        logger.info("Parsed %d transactions from CSV", len(transactions))
        return transactions

    def _try_parse_date(self, date_str: str) -> Optional[date]:
        """Try multiple date formats."""
        formats = self.db.get_config("import.date_formats", ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%b %d, %Y"])
        for fmt in formats:
            try:
                return date.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def validate_transactions(self, transactions: list[ParsedTransaction]) -> list[dict]:
        """Validate parsed transactions and return any issues.

        Args:
            transactions: List of parsed transactions.

        Returns:
            List of validation error dicts with 'row', 'field', and 'message'.
        """
        errors = []
        for i, txn in enumerate(transactions):
            if not txn.description:
                errors.append({"row": i + 2, "field": "description", "message": "Empty description"})
            if txn.amount == 0:
                errors.append({"row": i + 2, "field": "amount", "message": "Zero amount"})
            if txn.date > date.today():
                errors.append({"row": i + 2, "field": "date", "message": "Date in the future"})
        return errors
