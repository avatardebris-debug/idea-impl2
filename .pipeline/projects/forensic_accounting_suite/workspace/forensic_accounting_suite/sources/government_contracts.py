"""Government contract data source with mock/sample data."""

from __future__ import annotations

from datetime import date
from typing import Optional

from forensic_accounting_suite.sources.base import DataSource
from forensic_accounting_suite.core.models import GovernmentContract


# ------------------------------------------------------------------
# Mock / sample government contract data
# ------------------------------------------------------------------

_SAMPLE_CONTRACTS: list[dict] = [
    {
        "contract_id": "GC-20240001",
        "contract_number": "GCN-2024-001",
        "agency": "Ministry of Defense",
        "agency_address": "Whitehall, London, UK",
        "contractor_name": "Acme Global Trading Ltd",
        "contractor_registration_number": "REG-10001",
        "contractor_address": "123 Harbor Blvd, Portside City, UK",
        "contractor_directors": ["John Smith", "Maria Garcia"],
        "contract_value": 2500000.0,
        "currency": "USD",
        "award_date": date(2024, 1, 15),
        "end_date": date(2025, 1, 14),
        "description": "Supply of specialized defense equipment",
        "contract_type": "Fixed-price",
        "source_db": "UK Government Contracts",
    },
    {
        "contract_id": "GC-20240002",
        "contract_number": "GCN-2024-002",
        "agency": "Department of Defense",
        "agency_address": "Pentagon, Arlington, VA, USA",
        "contractor_name": "Titan Defense Systems",
        "contractor_registration_number": "REG-10005",
        "contractor_address": "321 Pentagon Row, Arlington, VA 22201, USA",
        "contractor_directors": ["Robert Chen", "Patricia Adams"],
        "contract_value": 15000000.0,
        "currency": "USD",
        "award_date": date(2024, 3, 1),
        "end_date": date(2026, 2, 28),
        "description": "Development and deployment of advanced radar systems",
        "contract_type": "Cost-plus",
        "source_db": "USASpending.gov",
    },
    {
        "contract_id": "GC-20240003",
        "contract_number": "GCN-2024-003",
        "agency": "Department of Commerce",
        "agency_address": "1401 Constitution Ave, Washington, DC, USA",
        "contractor_name": "Acme Holdings Inc",
        "contractor_registration_number": "REG-10002",
        "contractor_address": "456 Wall Street, New York, NY 10005, USA",
        "contractor_directors": ["John Smith", "Robert Chen"],
        "contract_value": 750000.0,
        "currency": "USD",
        "award_date": date(2024, 5, 20),
        "end_date": date(2024, 11, 30),
        "description": "Economic analysis and consulting services",
        "contract_type": "Fixed-price",
        "source_db": "USASpending.gov",
    },
    {
        "contract_id": "GC-20240004",
        "contract_number": "GCN-2024-004",
        "agency": "Bundesministerium der Verteidigung",
        "agency_address": "Bonngasse 17, Bonn, Germany",
        "contractor_name": "Meridian Logistics GmbH",
        "contractor_registration_number": "REG-10006",
        "contractor_address": "555 Hafenstrasse, Hamburg, 20095 DE",
        "contractor_directors": ["Hans Mueller", "Patricia Adams"],
        "contract_value": 3200000.0,
        "currency": "EUR",
        "award_date": date(2024, 7, 1),
        "end_date": date(2025, 6, 30),
        "description": "Logistics support for military operations",
        "contract_type": "Indefinite delivery",
        "source_db": "German Federal Procurement",
    },
    {
        "contract_id": "GC-20240005",
        "contract_number": "GCN-2024-005",
        "agency": "Ministry of Finance",
        "agency_address": "Treasury Building, London, UK",
        "contractor_name": "Global Procurement Services LLC",
        "contractor_registration_number": "REG-10004",
        "contractor_address": "123 Harbor Blvd, Portside City, UK",
        "contractor_directors": ["John Smith", "Wei Zhang"],
        "contract_value": 450000.0,
        "currency": "USD",
        "award_date": date(2024, 9, 10),
        "end_date": date(2025, 3, 9),
        "description": "Financial audit and compliance services",
        "contract_type": "Time-and-materials",
        "source_db": "UK Government Contracts",
    },
]


class GovernmentContractSource(DataSource[GovernmentContract]):
    """Mock government contract data source."""

    def __init__(self, entries: Optional[list[dict]] = None):
        self._entries: list[GovernmentContract] = [
            GovernmentContract(**e) for e in (entries or _SAMPLE_CONTRACTS)
        ]

    def query(self, **kwargs) -> list[GovernmentContract]:
        """Filter government contracts by keyword arguments.

        Supported filters:
            contractor_name (str) — case-insensitive partial match
            contractor_registration_number (str) — exact match
            agency (str) — case-insensitive partial match
            contract_type (str) — case-insensitive partial match
            award_date_from (date) — inclusive start
            award_date_to (date) — inclusive end
            min_value (float) — minimum contract_value
            max_value (float) — maximum contract_value
            keyword (str) — case-insensitive search across all text fields
        """
        results = list(self._entries)

        contractor_name = kwargs.get("contractor_name")
        if contractor_name:
            results = [
                e for e in results
                if contractor_name.lower() in e.contractor_name.lower()
            ]

        contractor_reg = kwargs.get("contractor_registration_number")
        if contractor_reg:
            results = [
                e for e in results
                if e.contractor_registration_number == contractor_reg
            ]

        agency = kwargs.get("agency")
        if agency:
            results = [
                e for e in results
                if agency.lower() in (e.agency or "").lower()
            ]

        contract_type = kwargs.get("contract_type")
        if contract_type:
            results = [
                e for e in results
                if contract_type.lower() in (e.contract_type or "").lower()
            ]

        award_from = kwargs.get("award_date_from")
        if award_from:
            results = [
                e for e in results
                if e.award_date and e.award_date >= award_from
            ]

        award_to = kwargs.get("award_date_to")
        if award_to:
            results = [
                e for e in results
                if e.award_date and e.award_date <= award_to
            ]

        min_value = kwargs.get("min_value")
        if min_value is not None:
            results = [e for e in results if e.contract_value >= min_value]

        max_value = kwargs.get("max_value")
        if max_value is not None:
            results = [e for e in results if e.contract_value <= max_value]

        keyword = kwargs.get("keyword")
        if keyword:
            kw_lower = keyword.lower()

            def _match_keyword(e: GovernmentContract) -> bool:
                text_fields = [
                    e.contract_id, e.contract_number, e.agency,
                    e.agency_address, e.contractor_name,
                    e.contractor_registration_number, e.contractor_address,
                    e.description, e.contract_type,
                ]
                return any(kw_lower in (t or "").lower() for t in text_fields)

            results = [e for e in results if _match_keyword(e)]

        return results

    def fetch_all(self) -> list[GovernmentContract]:
        return list(self._entries)

    def get_by_id(self, record_id: str) -> GovernmentContract | None:
        for entry in self._entries:
            if entry.contract_id == record_id:
                return entry
        return None
