"""Procurement data source with mock/sample data."""

from __future__ import annotations

from datetime import date
from typing import Optional

from forensic_accounting_suite.sources.base import DataSource
from forensic_accounting_suite.core.models import ProcurementRecord


# ------------------------------------------------------------------
# Mock / sample procurement data
# ------------------------------------------------------------------

_SAMPLE_PROCUREMENTS: list[dict] = [
    {
        "procurement_id": "PROC-20240001",
        "contract_number": "CN-2024-001",
        "vendor_name": "Acme Global Trading Ltd",
        "vendor_registration_number": "REG-10001",
        "vendor_address": "123 Harbor Blvd, Portside City, UK",
        "vendor_directors": ["John Smith", "Maria Garcia"],
        "item_description": "Industrial machinery parts",
        "quantity": 50,
        "unit_price": 2500.0,
        "total_value": 125000.0,
        "currency": "USD",
        "award_date": date(2024, 2, 1),
        "delivery_date": date(2024, 3, 15),
        "procuring_entity": "Ministry of Defense",
        "procuring_entity_address": "Whitehall, London, UK",
        "source_db": "UK Government Contracts",
    },
    {
        "procurement_id": "PROC-20240002",
        "contract_number": "CN-2024-002",
        "vendor_name": "Titan Defense Systems",
        "vendor_registration_number": "REG-10005",
        "vendor_address": "321 Pentagon Row, Arlington, VA 22201, USA",
        "vendor_directors": ["Robert Chen", "Patricia Adams"],
        "item_description": "Defense electronics components",
        "quantity": 100,
        "unit_price": 8900.0,
        "total_value": 890000.0,
        "currency": "USD",
        "award_date": date(2024, 4, 15),
        "delivery_date": date(2024, 6, 1),
        "procuring_entity": "Department of Defense",
        "procuring_entity_address": "Pentagon, Arlington, VA, USA",
        "source_db": "USASpending.gov",
    },
    {
        "procurement_id": "PROC-20240003",
        "contract_number": "CN-2024-003",
        "vendor_name": "Global Procurement Services LLC",
        "vendor_registration_number": "REG-10004",
        "vendor_address": "123 Harbor Blvd, Portside City, UK",
        "vendor_directors": ["John Smith", "Wei Zhang"],
        "item_description": "Office equipment and supplies",
        "quantity": 200,
        "unit_price": 170.0,
        "total_value": 34000.0,
        "currency": "USD",
        "award_date": date(2024, 6, 10),
        "delivery_date": date(2024, 7, 1),
        "procuring_entity": "Ministry of Finance",
        "procuring_entity_address": "Treasury Building, London, UK",
        "source_db": "UK Government Contracts",
    },
    {
        "procurement_id": "PROC-20240004",
        "contract_number": "CN-2024-004",
        "vendor_name": "Meridian Logistics GmbH",
        "vendor_registration_number": "REG-10006",
        "vendor_address": "555 Hafenstrasse, Hamburg, 20095 DE",
        "vendor_directors": ["Hans Mueller", "Patricia Adams"],
        "item_description": "Precision instruments",
        "quantity": 25,
        "unit_price": 2680.0,
        "total_value": 67000.0,
        "currency": "EUR",
        "award_date": date(2024, 8, 1),
        "delivery_date": date(2024, 9, 15),
        "procuring_entity": "Bundesministerium der Verteidigung",
        "procuring_entity_address": "Bonngasse 17, Bonn, Germany",
        "source_db": "German Federal Procurement",
    },
    {
        "procurement_id": "PROC-20240005",
        "contract_number": "CN-2024-005",
        "vendor_name": "Acme Holdings Inc",
        "vendor_registration_number": "REG-10002",
        "vendor_address": "456 Wall Street, New York, NY 10005, USA",
        "vendor_directors": ["John Smith", "Robert Chen"],
        "item_description": "Consulting services",
        "quantity": 1,
        "unit_price": 500000.0,
        "total_value": 500000.0,
        "currency": "USD",
        "award_date": date(2024, 9, 1),
        "delivery_date": date(2024, 12, 31),
        "procuring_entity": "Department of Commerce",
        "procuring_entity_address": "1401 Constitution Ave, Washington, DC, USA",
        "source_db": "USASpending.gov",
    },
]


class ProcurementSource(DataSource[ProcurementRecord]):
    """Mock procurement data source."""

    def __init__(self, entries: Optional[list[dict]] = None):
        self._entries: list[ProcurementRecord] = [
            ProcurementRecord(**e) for e in (entries or _SAMPLE_PROCUREMENTS)
        ]

    def query(self, **kwargs) -> list[ProcurementRecord]:
        """Filter procurement records by keyword arguments.

        Supported filters:
            vendor_name (str) — case-insensitive partial match
            vendor_registration_number (str) — exact match
            procuring_entity (str) — case-insensitive partial match
            award_date_from (date) — inclusive start
            award_date_to (date) — inclusive end
            min_value (float) — minimum total_value
            max_value (float) — maximum total_value
            keyword (str) — case-insensitive search across all text fields
        """
        results = list(self._entries)

        vendor_name = kwargs.get("vendor_name")
        if vendor_name:
            results = [
                e for e in results
                if vendor_name.lower() in e.vendor_name.lower()
            ]

        vendor_reg = kwargs.get("vendor_registration_number")
        if vendor_reg:
            results = [e for e in results if e.vendor_registration_number == vendor_reg]

        procuring_entity = kwargs.get("procuring_entity")
        if procuring_entity:
            results = [
                e for e in results
                if procuring_entity.lower() in (e.procuring_entity or "").lower()
            ]

        award_from = kwargs.get("award_date_from")
        if award_from:
            results = [e for e in results if e.award_date and e.award_date >= award_from]

        award_to = kwargs.get("award_date_to")
        if award_to:
            results = [e for e in results if e.award_date and e.award_date <= award_to]

        min_value = kwargs.get("min_value")
        if min_value is not None:
            results = [e for e in results if e.total_value >= min_value]

        max_value = kwargs.get("max_value")
        if max_value is not None:
            results = [e for e in results if e.total_value <= max_value]

        keyword = kwargs.get("keyword")
        if keyword:
            kw_lower = keyword.lower()
            def _match_keyword(e: ProcurementRecord) -> bool:
                text_fields = [
                    e.procurement_id, e.contract_number, e.vendor_name,
                    e.vendor_registration_number, e.vendor_address,
                    e.item_description, e.procuring_entity,
                ]
                return any(kw_lower in (t or "").lower() for t in text_fields)
            results = [e for e in results if _match_keyword(e)]

        return results

    def fetch_all(self) -> list[ProcurementRecord]:
        return list(self._entries)

    def get_by_id(self, record_id: str) -> ProcurementRecord | None:
        for entry in self._entries:
            if entry.procurement_id == record_id:
                return entry
        return None
