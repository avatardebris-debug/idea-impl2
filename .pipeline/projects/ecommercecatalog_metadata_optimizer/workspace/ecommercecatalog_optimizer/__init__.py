"""EcommerceCatalog Metadata Optimizer — Core MVP.

Merge autoSEO with CSV Analyzer to audit product catalogs,
optimize metadata, and export enriched spreadsheets.
"""

from ecommercecatalog_optimizer.catalog_analyzer import CatalogAnalyzer
from ecommercecatalog_optimizer.metadata_optimizer import MetadataOptimizer
from ecommercecatalog_optimizer.exporter import CatalogExporter

__all__ = [
    "CatalogAnalyzer",
    "MetadataOptimizer",
    "CatalogExporter",
]

__version__ = "0.1.0"
