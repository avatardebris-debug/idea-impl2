"""Main entry point for the Forensic Accounting Suite."""

import argparse
import json
import sys
from datetime import date

from forensic_accounting_suite.pipeline import ForensicPipeline
from forensic_accounting_suite.core.models import CorporateRegistryEntry, ShippingManifest, ProcurementRecord


def create_sample_data():
    """Create sample data for demonstration."""
    registry_entries = [
        CorporateRegistryEntry(
            registration_number="REG-001",
            company_name="Acme Corp",
            incorporation_date=date(2020, 1, 1),
            registered_address="123 Main St",
            directors=["John Doe", "Jane Smith"],
            officers=["Jane Smith"],
            naics_code="5415",
            share_capital=100000.0,
            status="active",
        ),
        CorporateRegistryEntry(
            registration_number="REG-002",
            company_name="Beta LLC",
            incorporation_date=date(2021, 6, 1),
            registered_address="123 Main St",
            directors=["John Doe", "Bob Wilson"],
            officers=["Bob Wilson"],
            naics_code="5416",
            share_capital=50000.0,
            status="active",
        ),
        CorporateRegistryEntry(
            registration_number="SHELL-001",
            company_name="Shell Corp",
            incorporation_date=date(2022, 1, 1),
            registered_address="",
            directors=["John Doe"],
            officers=[],
            naics_code="",
            share_capital=500.0,
            status="active",
        ),
    ]
    shipping_manifests = [
        ShippingManifest(
            manifest_id="MAN-001",
            vessel_name="MV Ocean",
            departure_port="Port A",
            arrival_port="Port B",
            departure_date=date(2023, 1, 1),
            arrival_date=date(2023, 1, 15),
            cargo_description="Electronics",
            shipper_name="Acme Corp",
            consignee_name="Delta Trading",
            total_value=50000.0,
            weight_kg=10000.0,
            hs_code="8517",
            origin_country="CN",
            destination_country="US",
        ),
    ]
    procurements = [
        ProcurementRecord(
            procurement_id="PROC-001",
            vendor_name="Acme Corp",
            vendor_address="123 Main St",
            vendor_registration_number="REG-001",
            description="IT consulting",
            total_value=250000.0,
            award_date=date(2023, 6, 1),
            contract_start_date=date(2023, 6, 1),
            contract_end_date=date(2024, 6, 1),
            naics_code="5415",
            funding_agency="Dept of Technology",
        ),
        ProcurementRecord(
            procurement_id="PROC-002",
            vendor_name="Shell Corp",
            vendor_address="789 Fake St",
            vendor_registration_number="SHELL-001",
            description="Consulting",
            total_value=500000.0,
            award_date=date(2023, 7, 1),
            contract_start_date=date(2023, 7, 1),
            contract_end_date=date(2024, 7, 1),
            naics_code="5415",
            funding_agency="Dept of Homeland Security",
        ),
    ]
    return registry_entries, shipping_manifests, procurements


def main():
    parser = argparse.ArgumentParser(description="Forensic Accounting Suite")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--sample", action="store_true", help="Use sample data")
    args = parser.parse_args()

    pipeline = ForensicPipeline()

    if args.sample:
        registry_entries, shipping_manifests, procurements = create_sample_data()
    else:
        # In production, load from files or databases
        registry_entries = []
        shipping_manifests = []
        procurements = []

    result = pipeline.run(
        registry_entries=registry_entries,
        shipping_manifests=shipping_manifests,
        procurements=procurements,
    )

    if args.format == "json":
        output = pipeline.generate_json_report(result)
    else:
        output = pipeline.generate_text_report(result)

    if args.output:
        with open(args.output, "w") as f:
            if args.format == "json":
                json.dump(output, f, indent=2)
            else:
                f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
