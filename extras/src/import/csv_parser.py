"""CSV parser for bank statement imports in BudgetFlow Tracker."""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.core.database import Database

logger = logging.getLogger(__name__)


@dataclass
class BankStatementFormat:
    """Detected bank statement format."""
    name: str
    date_column: str
    description_column: str
    amount_column: str
    separator: str = ","


@dataclass
class ParsedTransaction:
    """A parsed transaction from a bank statement."""
    date: date
    description: str
    amount: float
    category: Optional[str] = None


# Supported bank formats
BANK_FORMATS = {
    "generic_csv": BankStatementFormat(
        name="Generic CSV",
        date_column="Date",
        description_column="Description",
        amount_column="Amount",
        separator=",",
    ),
    "chase": BankStatementFormat(
        name="Chase Bank",
        date_column="Date",
        description_column="Description",
        amount_column="Amount",
        separator=",",
    ),
    "wells_fargo": BankStatementFormat(
        name="Wells Fargo",
        date_column="Date",
        description_column="Description",
        amount_column="Amount",
        separator=",",
    ),
    "bank_of_america": BankStatementFormat(
        name="Bank of America",
        date_column="Date",
        description_column="Description",
        amount_column="Amount",
        separator=",",
    ),
    "paypal": BankStatementFormat(
        name="PayPal",
        date_column="Date",
        description_column="Description",
        amount_column="Amount",
        separator=",",
    ),
}


class CSVParser:
    """Parse CSV bank statements."""

    def __init__(self, db: Database):
        self.db = db

    def detect_format(self, csv_content: str) -> BankStatementFormat:
        """Detect the bank statement format from CSV headers.

        Args:
            csv_content: Raw CSV content string.

        Returns:
            Detected BankStatementFormat.
        """
        reader = csv.reader(io.StringIO(csv_content))
        headers = next(reader)
        headers_lower = [h.strip().lower() for h in headers]

        # Check for common date columns
        date_col = None
        for col in ["date", "transaction date", "post date", "posting date"]:
            if col in headers_lower:
                date_col = headers_lower.index(col)
                break

        if date_col is None:
            raise ValueError("Could not detect date column in CSV")

        # Check for common description columns
        desc_col = None
        for col in ["description", "memo", "narrative", "details"]:
            if col in headers_lower:
                desc_col = headers_lower.index(col)
                break

        if desc_col is None:
            raise ValueError("Could not detect description column in CSV")

        # Check for common amount columns
        amount_col = None
        for col in ["amount", "debit", "credit", "transaction amount"]:
            if col in headers_lower:
                amount_col = headers_lower.index(col)
                break

        if amount_col is None:
            raise ValueError("Could not detect amount column in CSV")

        # Detect separator
        first_line = csv_content.split("\n")[0]
        if "\t" in first_line:
            separator = "\t"
        elif ";" in first_line:
            separator = ";"
        else:
            separator = ","

        # Determine specific format
        format_name = "generic_csv"
        for key, fmt in BANK_FORMATS.items():
            if key != "generic_csv":
                if fmt.name.lower() in csv_content[:500].lower():
                    format_name = key
                    break

        return BankStatementFormat(
            name=BANK_FORMATS[format_name].name,
            date_column=headers[date_col],
            description_column=headers[desc_col],
            amount_column=headers[amount_col],
            separator=separator,
        )

    def parse(self, csv_content: str, format: Optional[BankStatementFormat] = None) -> list[ParsedTransaction]:
        """Parse CSV content into transactions.

        Args:
            csv_content: Raw CSV content string.
            format: Optional format specification. If None, auto-detect.

        Returns:
            List of ParsedTransaction objects.
        """
        if format is None:
            format = self.detect_format(csv_content)

        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=format.separator)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1-indexed, header is row 1)
            try:
                # Parse date
                date_str = row.get(format.date_column, "").strip()
                if not date_str:
                    continue

                # Try multiple date formats
                parsed_date = None
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y"]:
                    try:
                        parsed_date = date.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue

                if parsed_date is None:
                    logger.warning("Could not parse date '%s' in row %d", date_str, row_num)
                    continue

                # Parse description
                description = row.get(format.description_column, "").strip()
                if not description:
                    description = "Unknown transaction"

                # Parse amount
                amount_str = row.get(format.amount_column, "").strip()
                if not amount_str:
                    continue

                # Remove currency symbols and commas
                amount_str = amount_str.replace("$", "").replace(",", "").strip()

                # Handle negative amounts (expenses)
                if amount_str.startswith("(") and amount_str.endswith(")"):
                    amount_str = "-" + amount_str[1:-1]
                elif amount_str.startswith("-"):
                    pass  # Already negative
                elif amount_str.startswith("+"):
                    amount_str = amount_str[1:]

                amount = float(amount_str)

                # Determine transaction type
                transaction_type = "expense" if amount < 0 else "income"

                transactions.append(ParsedTransaction(
                    date=parsed_date,
                    description=description,
                    amount=amount,
                ))

            except (ValueError, KeyError) as e:
                logger.warning("Error parsing row %d: %s", row_num, str(e))
                continue

        logger.info("Parsed %d transactions", len(transactions))
        return transactions

    def import_transactions(
        self,
        csv_content: str,
        auto_categorize: bool = True,
    ) -> dict:
        """Parse and import transactions into the database.

        Args:
            csv_content: Raw CSV content string.
            auto_categorize: Whether to auto-categorize transactions.

        Returns:
            Dict with import statistics.
        """
        transactions = self.parse(csv_content)

        if auto_categorize:
            from src.categorize.rule_engine import Categorizer
            categorizer = Categorizer(self.db)
            for transaction in transactions:
                result = categorizer.categorize(transaction.description, transaction.amount)
                transaction.category = result.category_name

        imported = 0
        errors = 0

        for transaction in transactions:
            try:
                self.db.execute(
                    """INSERT INTO transactions
                       (date, description, amount, transaction_type, category_name)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        transaction.date.isoformat(),
                        transaction.description,
                        transaction.amount,
                        "expense" if transaction.amount < 0 else "income",
                        transaction.category,
                    ),
                )
                imported += 1
            except Exception as e:
                logger.error("Error importing transaction: %s", str(e))
                errors += 1

        return {
            "total": len(transactions),
            "imported": imported,
            "errors": errors,
        }
