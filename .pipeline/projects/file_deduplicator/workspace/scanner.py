"""Module for scanning directories and computing MD5 hashes of files."""

import hashlib
import os
from typing import Dict


def compute_md5(file_path: str) -> str:
    """Compute the MD5 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal MD5 hash string.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def scan_directory(path: str) -> Dict[str, str]:
    """Recursively scan a directory and compute MD5 hashes for all files.
    
    Args:
        path: Path to the directory to scan.
        
    Returns:
        A dictionary mapping absolute file paths to their MD5 hash strings.
        Only regular files are included; directories and symlinks are skipped.
    """
    hash_map = {}
    
    for root, dirs, files in os.walk(path):
        for filename in files:
            file_path = os.path.join(root, filename)
            
            # Skip symlinks and non-regular files
            if os.path.islink(file_path) or not os.path.isfile(file_path):
                continue
            
            try:
                abs_path = os.path.abspath(file_path)
                file_hash = compute_md5(abs_path)
                hash_map[abs_path] = file_hash
            except (IOError, OSError) as e:
                print(f"Warning: Could not process {file_path}: {e}")
                continue
    
    return hash_map
