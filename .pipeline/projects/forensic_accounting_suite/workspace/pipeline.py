"""Pipeline orchestrator for the forensic accounting workflow.

Coordinates data ingestion, correlation, anomaly detection, and
report generation in a single pipeline.
"""

from __future__ import annotations

from typing import Any

from forensic_accounting_suite.core.models import (
    CorporateRegistryEntry,
    ShippingManifest,
    ProcurementRecord,
    GovernmentContract,
    SEC_Filing,
)
from forensic_accounting_suite.sources.base import DataSource
from forensic_accounting_suite.sources.corporate_registry import CorporateRegistrySource
from forensic_accounting_suite.sources.shipping_manifests import ShippingManifestSource
from forensic_accounting_suite.sources.procurement import ProcurementSource
from forensic_accounting_suite.engine.correlation import CorrelationEngine, CorrelationLink
from forensic_accounting_suite.engine.anomaly_detection import AnomalyDetector, Anomaly
from forensic_accounting_suite.engine.report_generation import ReportGenerator


class ForensicPipeline:
    """End-to-end forensic accounting analysis pipeline.

    Usage:
        pipeline = ForensicPipeline()
        pipeline.run()
        report = pipeline.get_text_report()
    """

    def __init__(
        self,
        registry_source: CorporateRegistrySource | None = None,
        shipping_source: ShippingManifestSource | None = None,
        procurement_source: ProcurementSource | None = None,
    ):
        self.registry_source = registry_source or CorporateRegistrySource()
        self.shipping_source = shipping_source or ShippingManifestSource()
        self.procurement_source = procurement_source or ProcurementSource()

        # Results (populated after run())
        self.registry_entries: list[CorporateRegistryEntry] = []
        self.shipping_manifests: list[ShippingManifest] = []
        self.procurements: list[ProcurementRecord] = []
        self.gov_contracts: list[GovernmentContract] = []
        self.sec_filings: list[SEC_Filing] = []
        self.correlation_links: list[CorrelationLink] = []
        self.anomalies: list[Anomaly] = []
        self.report_text: str = ""
        self.report_json: dict = {}

    def run(self) -> "ForensicPipeline":
        """Execute the full pipeline."""
        self._ingest_data()
        self._run_correlation()
        self._run_anomaly_detection()
        self._generate_reports()
        return self

    # -- pipeline stages --

    def _ingest_data(self) -> None:
        """Stage 1: Ingest data from all sources."""
        self.registry_entries = self.registry_source.fetch_all()
        self.shipping_manifests = self.shipping_source.fetch_all()
        self.procurements = self.procurement_source.fetch_all()
        # Gov contracts and SEC filings are empty in the MVP
        self.gov_contracts = []
        self.sec_filings = []

    def _run_correlation(self) -> None:
        """Stage 2: Run cross-correlation engine."""
        engine = CorrelationEngine(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
            gov_contracts=self.gov_contracts,
            sec_filings=self.sec_filings,
        )
        self.correlation_links = engine.find_all_links()

    def _run_anomaly_detection(self) -> None:
        """Stage 3: Run anomaly detection."""
        detector = AnomalyDetector(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
            gov_contracts=self.gov_contracts,
            sec_filings=self.sec_filings,
        )
        self.anomalies = detector.detect_all()

    def _generate_reports(self) -> None:
        """Stage 4: Generate reports."""
        generator = ReportGenerator(
            links=self.correlation_links,
            anomalies=self.anomalies,
        )
        self.report_text = generator.generate_text_report()
        self.report_json = generator.generate_json_report()

    # -- convenience accessors --

    def get_text_report(self) -> str:
        return self.report_text

    def get_json_report(self) -> dict:
        return self.report_json

    def get_anomalies(self) -> list[Anomaly]:
        return self.anomalies

    def get_correlation_links(self) -> list[CorrelationLink]:
        return self.correlation_links

    def get_findings_for_company(self, company_name: str) -> list[CorrelationLink]:
        """Get all correlation links for a specific company."""
        engine = CorrelationEngine(
            registry_entries=self.registry_entries,
            shipping_manifests=self.shipping_manifests,
            procurements=self.procurements,
            gov_contracts=self.gov_contracts,
            sec_filings=self.sec_filings,
        )
        return engine.find_links_for_company(company_name)
