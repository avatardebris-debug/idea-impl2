"""Cross-correlation engine for forensic accounting.

Identifies links between companies across multiple data sources by
matching on registration numbers, shared addresses, common directors,
ship names, and contract IDs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from forensic_accounting_suite.core.models import (
    CorporateRegistryEntry,
    ShippingManifest,
    ProcurementRecord,
    GovernmentContract,
    SEC_Filing,
)


# ------------------------------------------------------------------
# Correlation link model
# ------------------------------------------------------------------

@dataclass
class CorrelationLink:
    """A discovered link between two entities."""

    source_entity: str  # entity type + id/name
    target_entity: str  # entity type + id/name
    link_type: str  # e.g. "shared_director", "shared_address", "same_registration"
    confidence: float  # 0.0 – 1.0
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "link_type": self.link_type,
            "confidence": self.confidence,
            "details": self.details,
        }


# ------------------------------------------------------------------
# Correlation engine
# ------------------------------------------------------------------

class CorrelationEngine:
    """Cross-correlate entities across data sources.

    The engine builds a graph of links between companies by comparing
    registration numbers, addresses, directors, ship names, and
    contract/procurement IDs.
    """

    def __init__(
        self,
        registry_entries: list[CorporateRegistryEntry] | None = None,
        shipping_manifests: list[ShippingManifest] | None = None,
        procurements: list[ProcurementRecord] | None = None,
        gov_contracts: list[GovernmentContract] | None = None,
        sec_filings: list[SEC_Filing] | None = None,
    ):
        self.registry_entries = registry_entries or []
        self.shipping_manifests = shipping_manifests or []
        self.procurements = procurements or []
        self.gov_contracts = gov_contracts or []
        self.sec_filings = sec_filings or []

    # -- public API --

    def find_all_links(self) -> list[CorrelationLink]:
        """Run all correlation checks and return every discovered link."""
        links: list[CorrelationLink] = []
        links.extend(self._corporate_links())
        links.extend(self._shipping_links())
        links.extend(self._procurement_links())
        links.extend(self._cross_source_links())
        return links

    def find_links_for_company(
        self, company_name: str
    ) -> list[CorrelationLink]:
        """Return links involving a specific company (case-insensitive)."""
        all_links = self.find_all_links()
        name_lower = company_name.lower()
        return [
            l for l in all_links
            if name_lower in l.source_entity.lower()
            or name_lower in l.target_entity.lower()
        ]

    # -- internal correlation methods --

    def _corporate_links(self) -> list[CorrelationLink]:
        """Links within the corporate registry (shared directors, addresses)."""
        links: list[CorrelationLink] = []
        for i, a in enumerate(self.registry_entries):
            for b in self.registry_entries[i + 1:]:
                # Shared directors
                shared_dirs = set(a.directors) & set(b.directors)
                if shared_dirs:
                    links.append(CorrelationLink(
                        source_entity=f"Registry:{a.registration_number}",
                        target_entity=f"Registry:{b.registration_number}",
                        link_type="shared_director",
                        confidence=0.9,
                        details={"shared_directors": list(shared_dirs)},
                    ))
                # Shared registered address
                if a.registered_address and b.registered_address:
                    if a.registered_address == b.registered_address:
                        links.append(CorrelationLink(
                            source_entity=f"Registry:{a.registration_number}",
                            target_entity=f"Registry:{b.registration_number}",
                            link_type="shared_address",
                            confidence=0.85,
                            details={"address": a.registered_address},
                        ))
        return links

    def _shipping_links(self) -> list[CorrelationLink]:
        """Links within shipping manifests (shared vessels, parties)."""
        links: list[CorrelationLink] = []
        for i, a in enumerate(self.shipping_manifests):
            for b in self.shipping_manifests[i + 1:]:
                # Same vessel
                if a.vessel_name and b.vessel_name and a.vessel_name == b.vessel_name:
                    links.append(CorrelationLink(
                        source_entity=f"Manifest:{a.manifest_id}",
                        target_entity=f"Manifest:{b.manifest_id}",
                        link_type="same_vessel",
                        confidence=0.7,
                        details={"vessel": a.vessel_name},
                    ))
                # Same shipper
                if a.shipper and b.shipper and a.shipper == b.shipper:
                    links.append(CorrelationLink(
                        source_entity=f"Manifest:{a.manifest_id}",
                        target_entity=f"Manifest:{b.manifest_id}",
                        link_type="same_shipper",
                        confidence=0.6,
                        details={"shipper": a.shipper},
                    ))
                # Same consignee
                if a.consignee and b.consignee and a.consignee == b.consignee:
                    links.append(CorrelationLink(
                        source_entity=f"Manifest:{a.manifest_id}",
                        target_entity=f"Manifest:{b.manifest_id}",
                        link_type="same_consignee",
                        confidence=0.6,
                        details={"consignee": a.consignee},
                    ))
        return links

    def _procurement_links(self) -> list[CorrelationLink]:
        """Links within procurement records (shared vendors, entities)."""
        links: list[CorrelationLink] = []
        for i, a in enumerate(self.procurements):
            for b in self.procurements[i + 1:]:
                # Same vendor
                if a.vendor_name and b.vendor_name and a.vendor_name == b.vendor_name:
                    links.append(CorrelationLink(
                        source_entity=f"Procurement:{a.procurement_id}",
                        target_entity=f"Procurement:{b.procurement_id}",
                        link_type="same_vendor",
                        confidence=0.8,
                        details={"vendor": a.vendor_name},
                    ))
                # Same procuring entity
                if a.procuring_entity and b.procuring_entity and a.procuring_entity == b.procuring_entity:
                    links.append(CorrelationLink(
                        source_entity=f"Procurement:{a.procurement_id}",
                        target_entity=f"Procurement:{b.procurement_id}",
                        link_type="same_procuring_entity",
                        confidence=0.5,
                        details={"entity": a.procuring_entity},
                    ))
        return links

    def _cross_source_links(self) -> list[CorrelationLink]:
        """Links between different data sources."""
        links: list[CorrelationLink] = []

        # Build lookup maps
        reg_by_name: dict[str, CorporateRegistryEntry] = {}
        for entry in self.registry_entries:
            reg_by_name[entry.company_name.lower()] = entry

        # Registry <-> Shipping: shipper/receiver matches company name
        for manifest in self.shipping_manifests:
            sender_lower = (manifest.sender_company or "").lower()
            receiver_lower = (manifest.receiver_company or "").lower()
            for name, entry in reg_by_name.items():
                if sender_lower == name:
                    links.append(CorrelationLink(
                        source_entity=f"Registry:{entry.registration_number}",
                        target_entity=f"Manifest:{manifest.manifest_id}",
                        link_type="company_is_shipper",
                        confidence=0.75,
                        details={"company": entry.company_name, "manifest": manifest.manifest_id},
                    ))
                if receiver_lower == name:
                    links.append(CorrelationLink(
                        source_entity=f"Registry:{entry.registration_number}",
                        target_entity=f"Manifest:{manifest.manifest_id}",
                        link_type="company_is_receiver",
                        confidence=0.75,
                        details={"company": entry.company_name, "manifest": manifest.manifest_id},
                    ))

        # Registry <-> Procurement: vendor matches company name
        for proc in self.procurements:
            vendor_lower = proc.vendor_name.lower()
            for name, entry in reg_by_name.items():
                if vendor_lower == name:
                    links.append(CorrelationLink(
                        source_entity=f"Registry:{entry.registration_number}",
                        target_entity=f"Procurement:{proc.procurement_id}",
                        link_type="company_is_vendor",
                        confidence=0.85,
                        details={"company": entry.company_name, "procurement": proc.procurement_id},
                    ))

        # Registry <-> Gov Contract: contractor matches company name
        for contract in self.gov_contracts:
            contractor_lower = contract.contractor_name.lower()
            for name, entry in reg_by_name.items():
                if contractor_lower == name:
                    links.append(CorrelationLink(
                        source_entity=f"Registry:{entry.registration_number}",
                        target_entity=f"GovContract:{contract.contract_id}",
                        link_type="company_is_contractor",
                        confidence=0.85,
                        details={"company": entry.company_name, "contract": contract.contract_id},
                    ))

        # Registry <-> SEC Filing: company name matches
        for filing in self.sec_filings:
            filing_company_lower = filing.company_name.lower()
            for name, entry in reg_by_name.items():
                if filing_company_lower == name:
                    links.append(CorrelationLink(
                        source_entity=f"Registry:{entry.registration_number}",
                        target_entity=f"SEC:{filing.filing_id}",
                        link_type="company_is_filer",
                        confidence=0.8,
                        details={"company": entry.company_name, "filing": filing.filing_id},
                    ))

        # Shared addresses between registry entries and procurement/vendor addresses
        for entry in self.registry_entries:
            if not entry.registered_address:
                continue
            for proc in self.procurements:
                if proc.vendor_address and proc.vendor_address == entry.registered_address:
                    links.append(CorrelationLink(
                        source_entity=f"Registry:{entry.registration_number}",
                        target_entity=f"Procurement:{proc.procurement_id}",
                        link_type="shared_address",
                        confidence=0.7,
                        details={"address": entry.registered_address},
                    ))

        return links
