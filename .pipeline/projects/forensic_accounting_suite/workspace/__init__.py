"""Forensic Accounting Suite — OSINT for corporate tracking.

Core MVP: cross-correlation engine and anomaly detection over
corporate registry, shipping manifest, procurement, and government
contract data sources.
"""

from forensic_accounting_suite.core.models import (
    Company,
    CorporateRegistryEntry,
    ShippingManifest,
    ProcurementRecord,
    GovernmentContract,
    SEC_Filing,
)
from forensic_accounting_suite.engine.correlation import CorrelationEngine, CorrelationLink
from forensic_accounting_suite.engine.anomaly_detection import AnomalyDetector, Anomaly
from forensic_accounting_suite.engine.report_generation import ReportGenerator
from forensic_accounting_suite.sources.base import DataSource
from forensic_accounting_suite.sources.corporate_registry import CorporateRegistrySource
from forensic_accounting_suite.sources.shipping_manifests import ShippingManifestSource
from forensic_accounting_suite.sources.procurement import ProcurementSource
from forensic_accounting_suite.pipeline import ForensicPipeline

__all__ = [
    # Models
    "Company",
    "CorporateRegistryEntry",
    "ShippingManifest",
    "ProcurementRecord",
    "GovernmentContract",
    "SEC_Filing",
    # Engine
    "CorrelationEngine",
    "CorrelationLink",
    "AnomalyDetector",
    "Anomaly",
    "ReportGenerator",
    # Data sources
    "DataSource",
    "CorporateRegistrySource",
    "ShippingManifestSource",
    "ProcurementSource",
    # Pipeline
    "ForensicPipeline",
]

__version__ = "0.1.0"
