"""json_schema_profiler — JSON Schema Profiler package."""

from json_schema_profiler.anomaly import detect_anomalies
from json_schema_profiler.inference import infer_schema

__version__ = "0.1.0"
__all__ = ["infer_schema", "detect_anomalies"]
