"""
csv_data_pipeline_builder
Visual pipeline builder that chains CSV transformations (filter, join, pivot,
aggregate) between multiple CSV files with export to SQL or JSON.
Extends csv_analyzer with a DAG-based transform engine.
"""

__version__ = "0.1.0"
