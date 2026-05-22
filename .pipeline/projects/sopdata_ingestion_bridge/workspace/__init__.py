"""SOPData Ingestion Bridge — converts CSV outputs into structured SOP inputs."""

from sopdata_ingestion_bridge.bridge import SOPBridge, ingest
from sopdata_ingestion_bridge.core import DEFAULT_MAPPING, get_default_mapping, merge_mappings
from sopdata_ingestion_bridge.models import SOPInputRow

__all__ = [
    "SOPBridge",
    "ingest",
    "SOPInputRow",
    "DEFAULT_MAPPING",
    "get_default_mapping",
    "merge_mappings",
]
__version__ = "0.1.0"
