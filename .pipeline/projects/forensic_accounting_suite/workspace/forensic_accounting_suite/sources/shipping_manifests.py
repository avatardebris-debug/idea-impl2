"""Shipping manifest data source with mock/sample data."""

from __future__ import annotations

from datetime import date
from typing import Optional

from forensic_accounting_suite.sources.base import DataSource
from forensic_accounting_suite.core.models import ShippingManifest


# ------------------------------------------------------------------
# Mock / sample shipping manifest data
# ------------------------------------------------------------------

_SAMPLE_MANIFESTS: list[dict] = [
    {
        "manifest_id": "SHM-20240001",
        "vessel_name": "MV Ocean Star",
        "vessel_imo": "IMO-9876543",
        "shipper": "Acme Global Trading Ltd",
        "consignee": "Pacific Shipping Co",
        "origin_port": "Port of London, UK",
        "destination_port": "Port of Singapore",
        "departure_date": date(2024, 1, 15),
        "arrival_date": date(2024, 2, 5),
        "cargo_description": "Industrial machinery parts",
        "weight_kg": 45000.0,
        "hs_code": "8479.89",
        "declared_value": 125000.0,
        "currency": "USD",
        "sender_address": "123 Harbor Blvd, Portside City, UK",
        "receiver_address": "789 Marina Way, Singapore 018956",
        "sender_company": "Acme Global Trading Ltd",
        "receiver_company": "Pacific Shipping Co",
        "source_db": "UN Comtrade",
    },
    {
        "manifest_id": "SHM-20240002",
        "vessel_name": "MV Pacific Voyager",
        "vessel_imo": "IMO-9876544",
        "shipper": "Titan Defense Systems",
        "consignee": "Meridian Logistics GmbH",
        "origin_port": "Port of Norfolk, USA",
        "destination_port": "Port of Hamburg, Germany",
        "departure_date": date(2024, 3, 10),
        "arrival_date": date(2024, 4, 1),
        "cargo_description": "Defense electronics components",
        "weight_kg": 12000.0,
        "hs_code": "8517.62",
        "declared_value": 890000.0,
        "currency": "USD",
        "sender_address": "321 Pentagon Row, Arlington, VA 22201, USA",
        "receiver_address": "555 Hafenstrasse, Hamburg, 20095 DE",
        "sender_company": "Titan Defense Systems",
        "receiver_company": "Meridian Logistics GmbH",
        "source_db": "EU ICS2",
    },
    {
        "manifest_id": "SHM-20240003",
        "vessel_name": "MV Ocean Star",
        "vessel_imo": "IMO-9876543",
        "shipper": "Acme Holdings Inc",
        "consignee": "Global Procurement Services LLC",
        "origin_port": "Port of New York, USA",
        "destination_port": "Port of London, UK",
        "departure_date": date(2024, 5, 20),
        "arrival_date": date(2024, 6, 10),
        "cargo_description": "Office equipment and supplies",
        "weight_kg": 8500.0,
        "hs_code": "8471.30",
        "declared_value": 34000.0,
        "currency": "USD",
        "sender_address": "456 Wall Street, New York, NY 10005, USA",
        "receiver_address": "123 Harbor Blvd, Portside City, UK",
        "sender_company": "Acme Holdings Inc",
        "receiver_company": "Global Procurement Services LLC",
        "source_db": "UN Comtrade",
    },
    {
        "manifest_id": "SHM-20240004",
        "vessel_name": "MV Atlantic Express",
        "vessel_imo": "IMO-9876545",
        "shipper": "Meridian Logistics GmbH",
        "consignee": "Acme Global Trading Ltd",
        "origin_port": "Port of Hamburg, Germany",
        "destination_port": "Port of Rotterdam, Netherlands",
        "departure_date": date(2024, 7, 5),
        "arrival_date": date(2024, 7, 12),
        "cargo_description": "Precision instruments",
        "weight_kg": 3200.0,
        "hs_code": "9031.80",
        "declared_value": 67000.0,
        "currency": "EUR",
        "sender_address": "555 Hafenstrasse, Hamburg, 20095 DE",
        "receiver_address": "123 Harbor Blvd, Portside City, UK",
        "sender_company": "Meridian Logistics GmbH",
        "receiver_company": "Acme Global Trading Ltd",
        "source_db": "EU ICS2",
    },
]


class ShippingManifestSource(DataSource[ShippingManifest]):
    """Mock shipping manifest data source."""

    def __init__(self, entries: Optional[list[dict]] = None):
        self._entries: list[ShippingManifest] = [
            ShippingManifest(**e) for e in (entries or _SAMPLE_MANIFESTS)
        ]

    def query(self, **kwargs) -> list[ShippingManifest]:
        """Filter manifests by keyword arguments.

        Supported filters:
            vessel_name (str) — case-insensitive partial match
            shipper (str) — case-insensitive partial match
            consignee (str) — case-insensitive partial match
            origin_port (str) — case-insensitive partial match
            destination_port (str) — case-insensitive partial match
            sender_company (str) — case-insensitive partial match
            receiver_company (str) — case-insensitive partial match
            departure_date_from (date) — inclusive start
            departure_date_to (date) — inclusive end
            keyword (str) — case-insensitive search across all text fields
        """
        results = list(self._entries)

        vessel_name = kwargs.get("vessel_name")
        if vessel_name:
            results = [
                e for e in results
                if vessel_name.lower() in (e.vessel_name or "").lower()
            ]

        shipper = kwargs.get("shipper")
        if shipper:
            results = [
                e for e in results
                if shipper.lower() in (e.shipper or "").lower()
            ]

        consignee = kwargs.get("consignee")
        if consignee:
            results = [
                e for e in results
                if consignee.lower() in (e.consignee or "").lower()
            ]

        origin_port = kwargs.get("origin_port")
        if origin_port:
            results = [
                e for e in results
                if origin_port.lower() in (e.origin_port or "").lower()
            ]

        destination_port = kwargs.get("destination_port")
        if destination_port:
            results = [
                e for e in results
                if destination_port.lower() in (e.destination_port or "").lower()
            ]

        sender_company = kwargs.get("sender_company")
        if sender_company:
            results = [
                e for e in results
                if sender_company.lower() in (e.sender_company or "").lower()
            ]

        receiver_company = kwargs.get("receiver_company")
        if receiver_company:
            results = [
                e for e in results
                if receiver_company.lower() in (e.receiver_company or "").lower()
            ]

        dep_from = kwargs.get("departure_date_from")
        if dep_from:
            results = [e for e in results if e.departure_date and e.departure_date >= dep_from]

        dep_to = kwargs.get("departure_date_to")
        if dep_to:
            results = [e for e in results if e.departure_date and e.departure_date <= dep_to]

        keyword = kwargs.get("keyword")
        if keyword:
            kw_lower = keyword.lower()
            def _match_keyword(e: ShippingManifest) -> bool:
                text_fields = [
                    e.manifest_id, e.vessel_name, e.shipper, e.consignee,
                    e.origin_port, e.destination_port, e.cargo_description,
                    e.sender_company, e.receiver_company,
                ]
                return any(kw_lower in (t or "").lower() for t in text_fields)
            results = [e for e in results if _match_keyword(e)]

        return results

    def fetch_all(self) -> list[ShippingManifest]:
        return list(self._entries)

    def get_by_id(self, record_id: str) -> ShippingManifest | None:
        for entry in self._entries:
            if entry.manifest_id == record_id:
                return entry
        return None
