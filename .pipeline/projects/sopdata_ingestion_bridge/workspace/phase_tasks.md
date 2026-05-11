# Phase 1 Tasks

- [x] Task 1: Project scaffolding and package setup
  - What: Create the Python package structure with __init__.py, pyproject.toml (or setup.py), and a top-level package directory for the bridge API.
  - Files: sopdata_ingestion_bridge/__init__.py, sopdata_ingestion_bridge/core.py, pyproject.toml
  - Done when: The package can be imported with `import sopdata_ingestion_bridge` and exposes a public API entry point.

- [x] Task 2: CSV ingestion and parsing module
  - What: Build the CSV reader that accepts a CSV file path (or file-like object) and parses it into a list of row dictionaries. Handles basic CSV quirks (headers, quoting, encoding).
  - Files: sopdata_ingestion_bridge/ingest.py
  - Done when: Given a valid CSV file, the module returns a list of dicts (one per row) with header keys. Invalid CSV raises a clear ValueError.

- [x] Task 3: SOP data model definition
  - What: Define the structured SOP input data model using Python dataclasses or TypedDicts. Maps CSV columns to SOP fields (e.g., task_name, description, steps, assignee, deadline, priority).
  - Files: sopdata_ingestion_bridge/models.py
  - Done when: The data model classes are defined with type hints and can be instantiated from a dict of CSV row data.

- [x] Task 4: CSV-to-SOP transformation logic
  - What: Implement the core bridge function that takes parsed CSV rows and transforms them into structured SOP input objects using the data model. Supports configurable column mappings.
  - Files: sopdata_ingestion_bridge/transform.py
  - Done when: Given CSV row dicts and a column mapping config, the transform function returns a list of SOP data model instances.

- [x] Task 5: Bridge API entry point and public interface
  - What: Wire everything together into a clean public API. Provide a main function or class (e.g., `SOPBridge`) with a single `ingest(csv_path, mapping=None)` method that orchestrates ingestion, parsing, and transformation.
  - Files: sopdata_ingestion_bridge/bridge.py, sopdata_ingestion_bridge/__init__.py
  - Done when: A user can call `SOPBridge().ingest("data.csv")` and get back structured SOP input objects.
