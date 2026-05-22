"""Module for generating formatted reports of duplicate files."""

from typing import Dict, List


def generate_report(duplicates: Dict[str, List[str]]) -> None:
    """Generate and display a formatted report of duplicate files.
    
    Args:
        duplicates: A dictionary mapping hash values to lists of file paths
                   that share that hash. Only includes hashes with 2+ files.
    """
    print("\n" + "=" * 60)
    print("DUPLICATE FILES REPORT")
    print("=" * 60)
    
    total_duplicate_files = 0
    total_groups = len(duplicates)
    
    for hash_value, files in duplicates.items():
        print(f"\nHash: {hash_value}")
        print("-" * 40)
        
        for i, file_path in enumerate(files):
            # Mark the first file as the one being kept
            if i == 0:
                print(f"  [KEEP] {file_path}")
            else:
                print(f"  [DUP]  {file_path}")
                total_duplicate_files += 1
        
        print(f"  ({len(files)} files with same content)")
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: {total_groups} group(s) of duplicates found")
    print(f"         {total_duplicate_files} duplicate file(s) that could be removed")
    print("=" * 60 + "\n")
