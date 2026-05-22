"""Corporate registry data source with mock/sample data."""

from __future__ import annotations

from datetime import date
from typing import Optional

from forensic_accounting_suite.sources.base import DataSource
from forensic_accounting_suite.core.models import CorporateRegistryEntry


# ------------------------------------------------------------------
# Mock / sample corporate registry data
# ------------------------------------------------------------------

_SAMPLE_ENTRIES: list[dict] = [
    {
        "company_name": "Acme Global Trading Ltd",
        "registration_number": "REG-10001",
        "incorporation_date": date(2015, 3, 15),
        "registered_address": "123 Harbor Blvd, Portside City, UK",
        "directors": ["John Smith", "Maria Garcia"],
        "officers": ["Jane Doe (Secretary)"],
        "company_type": "Private Limited",
        "status": "active",
        "jurisdiction": "United Kingdom",
        "share_capital": 500000.0,
        "naics_code": "4238",
        "source_db": "UK Companies House",
    },
    {
        "company_name": "Acme Holdings Inc",
        "registration_number": "REG-10002",
        "incorporation_date": date(2012, 7, 1),
        "registered_address": "456 Wall Street, New York, NY 10005, USA",
        "directors": ["John Smith", "Robert Chen"],
        "officers": ["Alice Wong (CFO)"],
        "company_type": "Corporation",
        "status": "active",
        "jurisdiction": "Delaware, USA",
        "share_capital": 2000000.0,
        "naics_code": "5511",
        "source_db": "Delaware Division of Corporations",
    },
    {
        "company_name": "Pacific Shipping Co",
        "registration_number": "REG-10003",
        "incorporation_date": date(2018, 11, 20),
        "registered_address": "789 Marina Way, Singapore 018956",
        "directors": ["Wei Zhang", "Maria Garcia"],
        "officers": ["Li Wei (Director)"],
        "company_type": "Limited",
        "status": "active",
        "jurisdiction": "Singapore",
        "share_capital": 1000000.0,
        "naics_code": "4883",
        "source_db": "ACRA Singapore",
    },
    {
        "company_name": "Global Procurement Services LLC",
        "registration_number": "REG-10004",
        "incorporation_date": date(2019, 1, 10),
        "registered_address": "123 Harbor Blvd, Portside City, UK",
        "directors": ["John Smith", "Wei Zhang"],
        "officers": ["Tom Brown (Manager)"],
        "company_type": "Limited Liability Company",
        "status": "active",
        "jurisdiction": "United Kingdom",
        "share_capital": 250000.0,
        "naics_code": "5416",
        "source_db": "UK Companies House",
    },
    {
        "company_name": "Titan Defense Systems",
        "registration_number": "REG-10005",
        "incorporation_date": date(2005, 6, 30),
        "registered_address": "321 Pentagon Row, Arlington, VA 22201, USA",
        "directors": ["Robert Chen", "Patricia Adams"],
        "officers": ["David Kim (CEO)"],
        "company_type": "Corporation",
        "status": "active",
        "jurisdiction": "Virginia, USA",
        "share_capital": 10000000.0,
        "naics_code": "3364",
        "source_db": "Virginia SCC",
    },
    {
        "company_name": "Meridian Logistics GmbH",
        "registration_number": "REG-10006",
        "incorporation_date": date(2010, 9, 12),
        "registered_address": "555 Hafenstrasse, Hamburg, 20095 DE",
        "directors": ["Hans Mueller", "Patricia Adams"],
        "officers": ["Anna Schmidt (CFO)"],
        "company_type": "GmbH",
        "status": "active",
        "jurisdiction": "Germany",
        "share_capital": 750000.0,
        "naics_code": "4931",
        "source_db": "German Commercial Register",
    },
]


class CorporateRegistrySource(DataSource[CorporateRegistryEntry]):
    """Mock corporate registry data source.

    Uses hardcoded sample data for the MVP.  In production this would
    query real registry APIs or databases.
    """

    def __init__(self, entries: Optional[list[dict]] = None):
        self._entries: list[CorporateRegistryEntry] = [
            CorporateRegistryEntry(**e) for e in (entries or _SAMPLE_ENTRIES)
        ]

    # -- DataSource contract ----------------------------------------

    def query(self, **kwargs) -> list[CorporateRegistryEntry]:
        """Filter entries by keyword arguments.

        Supported filters:
            company_name (str) — case-insensitive partial match
            registration_number (str) — exact match
            jurisdiction (str) — case-insensitive partial match
            status (str) — exact match
            director (str) — case-insensitive partial match on any director
        """
        results = list(self._entries)

        company_name = kwargs.get("company_name")
        if company_name:
            results = [
                e for e in results
                if company_name.lower() in e.company_name.lower()
            ]

        reg_num = kwargs.get("registration_number")
        if reg_num:
            results = [e for e in results if e.registration_number == reg_num]

        jurisdiction = kwargs.get("jurisdiction")
        if jurisdiction:
            results = [
                e for e in results
                if jurisdiction.lower() in (e.jurisdiction or "").lower()
            ]

        status = kwargs.get("status")
        if status:
            results = [e for e in results if e.status == status]

        director = kwargs.get("director")
        if director:
            results = [
                e for e in results
                if any(director.lower() in d.lower() for d in e.directors)
            ]

        return results

    def fetch_all(self) -> list[CorporateRegistryEntry]:
        return list(self._entries)

    def get_by_id(self, record_id: str) -> CorporateRegistryEntry | None:
        for entry in self._entries:
            if entry.registration_number == record_id:
                return entry
        return None
