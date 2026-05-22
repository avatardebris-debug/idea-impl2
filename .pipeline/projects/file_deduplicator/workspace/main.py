#!/usr/bin/env python3
"""Main entry point for the file deduplicator CLI."""

import argparse
import sys
from file_deduplicator.scanner import scan_directory
from file_deduplicator.duplicates import find_duplicates
from file_deduplicator.report import generate_report


def main():
    """Main function to run the file deduplicator."""
    parser = argparse.ArgumentParser(
        description="Find and manage duplicate files in a directory."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to the directory to scan for duplicates"
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete duplicate files (keep the first occurrence)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )

    args = parser.parse_args()

    # Scan the directory for files and compute hashes
    print(f"Scanning directory: {args.path}")
    hash_map = scan_directory(args.path)

    if not hash_map:
        print("No files found in the specified directory.")
        return

    print(f"Found {len(hash_map)} files.")

    # Find duplicates
    duplicates = find_duplicates(hash_map)

    if not duplicates:
        print("No duplicate files found.")
        return

    # Generate report
    generate_report(duplicates)

    # Handle deletion logic
    if args.delete:
        if args.dry_run:
            print("\n--- DRY RUN MODE ---")
            print("Files that would be deleted:")
            for hash_value, files in duplicates.items():
                for file_path in files[1:]:  # Skip the first file (kept)
                    print(f"  {file_path}")
        else:
            print("\n--- DELETING DUPLICATES ---")
            deleted_count = 0
            for hash_value, files in duplicates.items():
                for file_path in files[1:]:  # Skip the first file (kept)
                    try:
                        import os
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                        deleted_count += 1
                    except OSError as e:
                        print(f"Error deleting {file_path}: {e}")
            print(f"\nTotal files deleted: {deleted_count}")


if __name__ == "__main__":
    main()
