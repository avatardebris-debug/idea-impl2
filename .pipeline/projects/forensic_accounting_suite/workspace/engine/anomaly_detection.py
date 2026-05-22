"""Anomaly detection for forensic accounting.

Detects suspicious patterns:
- Unusual transaction values (statistical outliers)
- Shell company indicators (no physical address, minimal directors)
- Circular transaction patterns
- Rapid company formation followed by large contracts
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
# Anomaly model
# ------------------------------------------------------------------

@dataclass
class Anomaly:
    """A detected anomaly."""

    entity_type: str  # e.g. "company", "procurement", "manifest"
    entity_id: str  # identifier of the entity
    anomaly_type: str  # e.g. "shell_company", "outlier_value"
    severity: str  # "low", "medium", "high", "critical"
    description: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "description": self.description,
            "details": self.details,
        }


# ------------------------------------------------------------------
# Anomaly detector
# ------------------------------------------------------------------

class AnomalyDetector:
    """Detect anomalies in forensic accounting data."""

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

    def detect_all(self) -> list[Anomaly]:
        """Run all anomaly detection checks."""
        anomalies: list[Anomaly] = []
        anomalies.extend(self._detect_shell_companies())
        anomalies.extend(self._detect_value_outliers())
        anomalies.extend(self._detect_rapid_formation())
        anomalies.extend(self._detect_circular_patterns())
        anomalies.extend(self._detect_minimal_disclosure())
        return anomalies

    def _detect_shell_companies(self) -> list[Anomaly]:
        """Detect potential shell companies."""
        anomalies: list[Anomaly] = []
        for entry in self.registry_entries:
            indicators = []
            # No physical address
            if not entry.registered_address or entry.registered_address.strip() == "":
                indicators.append("no_registered_address")
            # Minimal directors
            if len(entry.directors) <= 1:
                indicators.append("minimal_directors")
            # No officers
            if not entry.officers or len(entry.officers) == 0:
                indicators.append("no_officers")
            # Very low share capital
            if entry.share_capital and entry.share_capital < 1000:
                indicators.append("low_share_capital")

            if len(indicators) >= 2:
                anomalies.append(Anomaly(
                    entity_type="company",
                    entity_id=entry.registration_number,
                    anomaly_type="shell_company_indicator",
                    severity="high" if len(indicators) >= 3 else "medium",
                    description=f"Potential shell company: {', '.join(indicators)}",
                    details={"indicators": indicators, "company": entry.company_name},
                ))
        return anomalies

    def _detect_value_outliers(self) -> list[Anomaly]:
        """Detect statistical outliers in transaction values."""
        anomalies: list[Anomaly] = []

        # Check procurement values
        if self.procurements:
            values = [p.total_value for p in self.procurements if p.total_value]
            if len(values) >= 3:
                mean_val = sum(values) / len(values)
                std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5
                if std_val > 0:
                    for proc in self.procurements:
                        if proc.total_value:
                            z_score = abs(proc.total_value - mean_val) / std_val
                            if z_score > 2.0:
                                anomalies.append(Anomaly(
                                    entity_type="procurement",
                                    entity_id=proc.procurement_id,
                                    anomaly_type="value_outlier",
                                    severity="high" if z_score > 3.0 else "medium",
                                    description=f"Unusual transaction value: ${proc.total_value:,.2f} (z-score: {z_score:.2f})",
                                    details={
                                        "value": proc.total_value,
                                        "mean": mean_val,
                                        "std_dev": std_val,
                                        "z_score": z_score,
                                        "vendor": proc.vendor_name,
                                    },
                                ))

        # Check government contract values
        if self.gov_contracts:
            values = [c.total_value for c in self.gov_contracts if c.total_value]
            if len(values) >= 3:
                mean_val = sum(values) / len(values)
                std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5
                if std_val > 0:
                    for contract in self.gov_contracts:
                        if contract.total_value:
                            z_score = abs(contract.total_value - mean_val) / std_val
                            if z_score > 2.0:
                                anomalies.append(Anomaly(
                                    entity_type="government_contract",
                                    entity_id=contract.contract_id,
                                    anomaly_type="value_outlier",
                                    severity="high" if z_score > 3.0 else "medium",
                                    description=f"Unusual contract value: ${contract.total_value:,.2f} (z-score: {z_score:.2f})",
                                    details={
                                        "value": contract.total_value,
                                        "mean": mean_val,
                                        "std_dev": std_val,
                                        "z_score": z_score,
                                        "contractor": contract.contractor_name,
                                    },
                                ))

        return anomalies

    def _detect_rapid_formation(self) -> list[Anomaly]:
        """Detect companies formed shortly before large contracts."""
        anomalies: list[Anomaly] = []
        from datetime import timedelta

        for entry in self.registry_entries:
            if not entry.incorporation_date:
                continue
            # Check if company received large procurement shortly after formation
            for proc in self.procurements:
                if proc.vendor_name.lower() == entry.company_name.lower():
                    if proc.award_date and entry.incorporation_date:
                        days_diff = (proc.award_date - entry.incorporation_date).days
                        if 0 < days_diff < 90 and proc.total_value and proc.total_value > 100000:
                            anomalies.append(Anomaly(
                                entity_type="company",
                                entity_id=entry.registration_number,
                                anomaly_type="rapid_formation_contract",
                                severity="high",
                                description=f"Company formed {days_diff} days before receiving ${proc.total_value:,.2f} contract",
                                details={
                                    "incorporation_date": str(entry.incorporation_date),
                                    "contract_award_date": str(proc.award_date),
                                    "days_diff": days_diff,
                                    "contract_value": proc.total_value,
                                    "procurement_id": proc.procurement_id,
                                },
                            ))
        return anomalies

    def _detect_circular_patterns(self) -> list[Anomaly]:
        """Detect circular transaction patterns."""
        anomalies: list[Anomaly] = []
        # Build a graph of company relationships
        company_links: dict[str, set[str]] = {}

        for entry in self.registry_entries:
            name = entry.company_name.lower()
            if name not in company_links:
                company_links[name] = set()
            # Link via shared directors
            for director in entry.directors:
                for other in self.registry_entries:
                    if other.company_name.lower() != name and director in other.directors:
                        company_links[name].add(other.company_name.lower())

        # Check for circular patterns (A->B->C->A)
        for a in company_links:
            for b in company_links.get(a, set()):
                for c in company_links.get(b, set()):
                    if a in company_links.get(c, set()):
                        anomalies.append(Anomaly(
                            entity_type="network",
                            entity_id=f"{a}->{b}->{c}->{a}",
                            anomaly_type="circular_director_pattern",
                            severity="medium",
                            description=f"Circular director pattern detected: {a} -> {b} -> {c} -> {a}",
                            details={"cycle": [a, b, c, a]},
                        ))
        return anomalies

    def _detect_minimal_disclosure(self) -> list[Anomaly]:
        """Detect entities with minimal public disclosure."""
        anomalies: list[Anomaly] = []

        for entry in self.registry_entries:
            disclosure_score = 0
            if entry.directors:
                disclosure_score += 1
            if entry.officers:
                disclosure_score += 1
            if entry.registered_address:
                disclosure_score += 1
            if entry.share_capital:
                disclosure_score += 1
            if entry.naics_code:
                disclosure_score += 1

            if disclosure_score <= 2:
                anomalies.append(Anomaly(
                    entity_type="company",
                    entity_id=entry.registration_number,
                    anomaly_type="minimal_disclosure",
                    severity="medium",
                    description=f"Minimal public disclosure score: {disclosure_score}/5",
                    details={"disclosure_score": disclosure_score, "company": entry.company_name},
                ))

        return anomalies
