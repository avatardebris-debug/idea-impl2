"""
csv_data_pipeline_builder
Visual pipeline builder that chains CSV transformations (filter, join, pivot,
aggregate) between multiple CSV files with export to SQL or JSON.
Extends csv_analyzer with a DAG-based transform engine.
"""

__version__ = "0.1.0"

from .nodes import (
    TransformNode,
    FilterNode,
    SelectNode,
    AggregateNode,
    JoinNode,
    PivotNode,
    CsvSource,
    CsvSink,
    JsonSink,
    SqliteSink,
)
from .pipeline import Pipeline, ExecutionReport
from .loader import PipelineLoader
from .cli import main
from .tui import (
    PipelineBuilder,
    PipelineDiff,
    SchemaDrift,
    DataDrift,
    compare_runs,
    format_report,
    format_execution_summary,
    save_report_last,
    load_last_report,
)

__all__ = [
    "TransformNode",
    "FilterNode",
    "SelectNode",
    "AggregateNode",
    "JoinNode",
    "PivotNode",
    "CsvSource",
    "CsvSink",
    "JsonSink",
    "SqliteSink",
    "Pipeline",
    "ExecutionReport",
    "PipelineLoader",
    "main",
    "PipelineBuilder",
    "PipelineDiff",
    "SchemaDrift",
    "DataDrift",
    "compare_runs",
    "format_report",
    "format_execution_summary",
    "save_report_last",
    "load_last_report",
]
