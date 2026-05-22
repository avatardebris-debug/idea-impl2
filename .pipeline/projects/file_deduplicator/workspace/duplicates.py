"""Module for detecting and grouping duplicate files by hash."""

from typing import Dict, List


def find_duplicates(hash_map: Dict[str, str]) -> Dict[str, List[str]]:
    """Find duplicate files by grouping files with matching hashes.
    
    Args:
        hash_map: A dictionary mapping file paths to their MD5 hash strings.
        
    Returns:
        A dictionary mapping hash values to lists of file paths that share that hash.
        Only hashes with 2 or more files (actual duplicates) are included.
    """
    hash_groups: Dict[str, List[str]] = {}
    
    # Group files by hash
    for file_path, file_hash in hash_map.items():
        if file_hash not in hash_groups:
            hash_groups[file_hash] = []
        hash_groups[file_hash].append(file_path)
    
    # Filter to only include groups with 2+ files (duplicates)
    duplicates = {
        file_hash: files
        for file_hash, files in hash_groups.items()
        if len(files) >= 2
    }
    
    return duplicates
