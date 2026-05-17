# Phase 1 Tasks

- [x] Fix blocking syntax error: unterminated string literal in tests/test_models.py:363
- [ ] Task 1: Create project structure and package scaffolding
  - What: Set up the Python package layout with __init__.py, core modules, and data source modules. Create a pyproject.toml for package configuration.
  - Files: forensic_accounting_suite/__init__.py, forensic_accounting_suite/core/__init__.py, forensic_accounting_suite/core/models.py, forensic_accounting_suite/sources/__init__.py, forensic_accounting_suite/sources/base.py, pyproject.toml, setup.cfg
  - Done when: Package is importable (`import forensic_accounting_suite` succeeds), pyproject.toml defines the package metadata, and the directory structure matches a standard Python package layout.

- [ ] Task 2: Implement core data models
  - What: Define dataclasses/Pydantic models for the key entities: Company, CorporateRegistryEntry, ShippingManifest, ProcurementRecord, GovernmentContract, SEC_Filing. Include fields relevant to cross-correlation (e.g., registration numbers, addresses, directors, ship names, contract IDs).
  - Files: forensic_accounting_suite/core/models.py
  - Done when: All six entity models are defined with appropriate fields, can be instantiated and serialized to/from dicts, and are exported from forensic_accounting_suite.core.

- [ ] Task 3: Implement base data source interface and corporate registry source
  - What: Create an abstract base class for data sources with a standard fetch/query interface. Implement a concrete CorporateRegistrySource that queries a sample/mock corporate registry (using hardcoded sample data for MVP).
  - Files: forensic_accounting_suite/sources/base.py, forensic_accounting_suite/sources/corporate_registry.py
  - Done when: CorporateRegistrySource can be instantiated, query by company name or registration number, and return CorporateRegistryEntry objects. Base source defines a clear interface (query, fetch_all).

- [ ] Task 4: Implement shipping manifest and procurement data sources
  - What: Create concrete data source modules for ShippingManifestSource and ProcurementSource, each with mock/sample data and a query interface matching the base source contract.
  - Files: forensic_accounting_suite/sources/shipping_manifests.py, forensic_accounting_suite/sources/procurement.py
  - Done when: Both sources can be instantiated, return ShippingManifest and ProcurementRecord objects respectively, and support basic filtering (e.g., by date range or keyword).

- [ ] Task 5: Implement the cross-correlation engine
  - What: Build a CorrelationEngine class that takes records from multiple data sources and identifies links between companies — matching on registration numbers, shared addresses, common directors, ship names, and contract IDs.
  - Files: forensic_accounting_suite/core/correlation.py
  - Done when: CorrelationEngine can ingest records from at least two sources, produce a list of correlation links with confidence scores, and output results as structured dicts. Links are discoverable via a correlate() method.

- [ ] Task 6: Implement basic anomaly detection
  - What: Build an AnomalyDetector that flags suspicious patterns: companies with unusually high procurement values, shipping manifests with mismatched addresses, or entities appearing in multiple government contract databases.
  - Files: forensic_accounting_suite/core/anomaly.py
  - Done when: AnomalyDetector can scan records from the data sources, produce anomaly alerts with severity levels and descriptions, and be invoked via a detect() method. At least two anomaly types are implemented.

- [ ] Task 7: Wire up the top-level API and verify importability
  - What: Update forensic_accounting_suite/__init__.py to expose the main public API (CorrelationEngine, AnomalyDetector, data models, and source classes) at the package root. Add a simple example usage in a README or example script.
  - Files: forensic_accounting_suite/__init__.py, README.md
  - Done when: All core classes and models are accessible via `from forensic_accounting_suite import ...`, a quick smoke test script runs end-to-end (create sources → correlate → detect anomalies), and the README describes how to use the package.