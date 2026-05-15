"""sec_importer compatibility shim.

Provides the models and stubs that the forensic suite imports from the
sec_importer pipeline project, so the forensic project can run and test
independently.
"""

from sec_importer.models import (
    CompanyModel,
    FilingModel,
    FilingItemModel,
    XBRLFactModel,
    FilingSchemaConfig,
)
from sec_importer.database import SECDatabase

__all__ = [
    "CompanyModel",
    "FilingModel",
    "FilingItemModel",
    "XBRLFactModel",
    "FilingSchemaConfig",
    "SECDatabase",
]
