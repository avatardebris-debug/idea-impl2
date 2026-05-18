"""
finance_tracker — Personal finance tracker CLI.

Imports bank CSV transactions, categorizes by merchant pattern,
generates monthly budget reports, and alerts on spending anomalies.

Usage:
    python -m finance_tracker import transactions.csv
    python -m finance_tracker report --month 2024-01
    python -m finance_tracker report --all --output report.md
    python -m finance_tracker categorize transactions.csv --output categorized.csv
    python -m finance_tracker alerts transactions.csv
"""
__version__ = "0.1.0"
