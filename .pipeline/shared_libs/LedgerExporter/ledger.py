"""Ledger module for storing and exporting invoices."""

import csv
import os
from datetime import date
from typing import List, Optional

from invoice_processor.models import Invoice, Ledger, LineItem


class LedgerExporter:
    """Export and import ledger data to/from CSV."""

    CSV_COLUMNS = ['invoice_id', 'vendor', 'date', 'total', 'currency', 'source_file',
                   'invoice_number', 'line_item_description', 'line_item_quantity',
                   'line_item_unit_price', 'line_item_amount']

    def export_to_csv(self, ledger: Ledger, output_path: str) -> None:
        """Export all invoices in the ledger to a CSV file.

        Each invoice is written as one row. Line items are written as
        additional rows with the same invoice metadata.
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.CSV_COLUMNS)

            for invoice in ledger.invoices:
                if invoice.line_items:
                    for item in invoice.line_items:
                        writer.writerow([
                            invoice.invoice_id,
                            invoice.vendor,
                            invoice.invoice_date.isoformat() if isinstance(invoice.invoice_date, date) else str(invoice.invoice_date),
                            invoice.total,
                            invoice.currency,
                            invoice.source_file,
                            invoice.invoice_number,
                            item.description,
                            item.quantity,
                            item.unit_price,
                            item.amount,
                        ])
                else:
                    writer.writerow([
                        invoice.invoice_id,
                        invoice.vendor,
                        invoice.invoice_date.isoformat() if isinstance(invoice.invoice_date, date) else str(invoice.invoice_date),
                        invoice.total,
                        invoice.currency,
                        invoice.source_file,
                        invoice.invoice_number,
                        '', '', '', '',
                    ])

    def import_from_csv(self, csv_path: str) -> Ledger:
        """Import invoices from a CSV file back into a Ledger."""
        ledger = Ledger()

        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            current_invoice_id = None
            current_invoice = None

            for row in reader:
                inv_id = row.get('invoice_id', '')

                if current_invoice_id != inv_id:
                    # New invoice
                    if current_invoice:
                        ledger.add_invoice(current_invoice)

                    inv_date_str = row.get('date', '')
                    try:
                        inv_date = date.fromisoformat(inv_date_str)
                    except (ValueError, TypeError):
                        inv_date = date.today()

                    current_invoice = Invoice(
                        invoice_id=inv_id,
                        vendor=row.get('vendor', 'Unknown'),
                        invoice_date=inv_date,
                        total=float(row.get('total', 0)),
                        currency=row.get('currency', 'USD'),
                        source_file=row.get('source_file', ''),
                        invoice_number=row.get('invoice_number', ''),
                        line_items=[],
                    )
                    current_invoice_id = inv_id

                # Add line item if present
                desc = row.get('line_item_description', '').strip()
                if desc:
                    try:
                        qty = float(row.get('line_item_quantity', 0) or 0)
                        unit_price = float(row.get('line_item_unit_price', 0) or 0)
                        amount = float(row.get('line_item_amount', 0) or 0)
                    except (ValueError, TypeError):
                        qty = unit_price = amount = 0

                    current_invoice.line_items.append(
                        LineItem(
                            description=desc,
                            quantity=qty,
                            unit_price=unit_price,
                            amount=amount,
                            source_file=current_invoice.source_file,
                        )
                    )

            if current_invoice:
                ledger.add_invoice(current_invoice)

        return ledger
