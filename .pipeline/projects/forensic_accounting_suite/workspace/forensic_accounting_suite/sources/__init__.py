"""Data source modules for forensic_accounting_suite."""

from forensic_accounting_suite.sources.base import DataSource
from forensic_accounting_suite.sources.corporate_registry import CorporateRegistrySource
from forensic_accounting_suite.sources.shipping_manifests import ShippingManifestSource
from forensic_accounting_suite.sources.procurement import ProcurementSource
from forensic_accounting_suite.sources.government_contracts import GovernmentContractSource
from forensic_accounting_suite.sources.sec_filings import SEC_FilingSource

__all__ = [
    "DataSource",
    "CorporateRegistrySource",
    "ShippingManifestSource",
    "ProcurementSource",
    "GovernmentContractSource",
    "SEC_FilingSource",
]
