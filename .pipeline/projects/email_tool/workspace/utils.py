"""
Utility functions for email processing.

This module provides helper functions for common operations like
path manipulation, string sanitization, and file operations.
"""

import os
import re
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Sanitize a filename to be filesystem-safe.
    
    Args:
        filename: The filename to sanitize.
        replacement: Character to replace invalid characters with.
    
    Returns:
        Sanitized filename.
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', replacement, filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(" .")
    # Limit length (most filesystems have 255 char limit)
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    return sanitized


def sanitize_path_component(component: str, replacement: str = "_") -> str:
    """
    Sanitize a path component for use in directory names.
    
    Args:
        component: The path component to sanitize.
        replacement: Character to replace invalid characters with.
    
    Returns:
        Sanitized path component.
    """
    return sanitize_filename(component, replacement)


def generate_unique_filename(
    base_name: str,
    extension: str = ".eml",
    existing_files: Optional[List[str]] = None
) -> str:
    """
    Generate a unique filename by appending a counter.
    
    Args:
        base_name: The base name for the file.
        extension: File extension.
        existing_files: List of existing filenames to check against.
    
    Returns:
        A unique filename.
    """
    if existing_files is None:
        existing_files = []
    
    counter = 1
    base_with_ext = f"{base_name}{extension}"
    
    while base_with_ext in existing_files:
        base_with_ext = f"{base_name}_{counter}{extension}"
        counter += 1
    
    return base_with_ext


def generate_file_hash(content: str, length: int = 8) -> str:
    """
    Generate a hash of file content.
    
    Args:
        content: The file content to hash.
        length: Length of the hash to return.
    
    Returns:
        Hexadecimal hash string.
    """
    return hashlib.sha256(content.encode()).hexdigest()[:length]


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes.
    
    Returns:
        Formatted size string.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"


def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    Parse various date string formats.
    
    Args:
        date_str: Date string to parse.
    
    Returns:
        Parsed datetime or None if parsing fails.
    """
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%b %d, %Y %H:%M:%S",
        "%d %b %Y %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def build_path_template(
    template: str,
    email_data: Dict[str, Any]
) -> str:
    """
    Build a file path from a template and email data.
    
    Args:
        template: Path template with placeholders.
        email_data: Dictionary with email data.
    
    Returns:
        Constructed file path.
    """
    # Replace placeholders with actual values
    path = template
    
    # Common placeholders
    replacements = {
        "{{year}}": str(email_data.get("year", datetime.now().year)),
        "{{month}}": str(email_data.get("month", datetime.now().month).zfill(2)),
        "{{day}}": str(email_data.get("day", datetime.now().day).zfill(2)),
        "{{from_domain}}": sanitize_path_component(
            email_data.get("from_domain", "unknown")
        ),
        "{{from_name}}": sanitize_path_component(
            email_data.get("from_name", "unknown")
        ),
        "{{subject}}": sanitize_path_component(
            email_data.get("subject", "untitled")
        ),
        "{{subject_sanitized}}": sanitize_path_component(
            email_data.get("subject", "untitled")
        ),
        "{{date}}": str(email_data.get("date", datetime.now().date())),
        "{{timestamp}}": str(email_data.get("timestamp", datetime.now().timestamp())),
    }
    
    for placeholder, value in replacements.items():
        path = path.replace(placeholder, str(value))
    
    return path


def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure.
    
    Returns:
        True if directory exists or was created, False on error.
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError) as e:
        return False


def get_collision_handler(strategy: str):
    """
    Get a collision handler function based on strategy.
    
    Args:
        strategy: Collision handling strategy ('rename', 'overwrite', 'skip').
    
    Returns:
        A function that handles filename collisions.
    """
    def handle_rename(base_name: str, extension: str, existing: List[str]) -> str:
        """Rename file with counter."""
        return generate_unique_filename(base_name, extension, existing)
    
    def handle_overwrite(base_name: str, extension: str, existing: List[str]) -> str:
        """Allow overwrite (return as-is)."""
        return f"{base_name}{extension}"
    
    def handle_skip(base_name: str, extension: str, existing: List[str]) -> Optional[str]:
        """Skip if file exists."""
        if f"{base_name}{extension}" in existing:
            return None
        return f"{base_name}{extension}"
    
    handlers = {
        "rename": handle_rename,
        "overwrite": handle_overwrite,
        "skip": handle_skip,
    }
    
    return handlers.get(strategy, handle_rename)


def validate_email_address(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email: Email address to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def extract_domain(email: str) -> Optional[str]:
    """
    Extract domain from email address.
    
    Args:
        email: Email address.
    
    Returns:
        Domain name or None if invalid.
    """
    if '@' in email:
        return email.split('@')[-1]
    return None


def normalize_path(path: str) -> str:
    """
    Normalize a file path.
    
    Args:
        path: Path to normalize.
    
    Returns:
        Normalized path.
    """
    return os.path.normpath(os.path.expanduser(path))


def join_paths(*parts: str) -> str:
    """
    Join path parts safely.
    
    Args:
        *parts: Path components to join.
    
    Returns:
        Joined path.
    """
    return os.path.join(*parts)


def get_file_extension(filename: str) -> str:
    """
    Get file extension.
    
    Args:
        filename: Filename.
    
    Returns:
        File extension including the dot.
    """
    return os.path.splitext(filename)[1].lower()


def remove_file_extension(filename: str) -> str:
    """
    Remove file extension.
    
    Args:
        filename: Filename.
    
    Returns:
        Filename without extension.
    """
    return os.path.splitext(filename)[0]


def is_allowed_extension(filename: str, allowed: List[str]) -> bool:
    """
    Check if file extension is allowed.
    
    Args:
        filename: Filename to check.
        allowed: List of allowed extensions.
    
    Returns:
        True if allowed, False otherwise.
    """
    ext = get_file_extension(filename)
    return ext in allowed


def calculate_file_hash(filepath: str, algorithm: str = "sha256") -> Optional[str]:
    """
    Calculate hash of a file.
    
    Args:
        filepath: Path to file.
        algorithm: Hash algorithm to use.
    
    Returns:
        Hexadecimal hash string or None on error.
    """
    import hashlib
    
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except (IOError, OSError):
        return None


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds.
    
    Returns:
        Formatted duration string.
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def safe_read_file(filepath: str, encoding: str = "utf-8") -> Optional[str]:
    """
    Safely read a file's contents.
    
    Args:
        filepath: Path to file.
        encoding: File encoding.
    
    Returns:
        File contents or None on error.
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except (IOError, UnicodeDecodeError):
        return None


def safe_write_file(
    filepath: str,
    content: str,
    encoding: str = "utf-8"
) -> bool:
    """
    Safely write content to a file.
    
    Args:
        filepath: Path to file.
        content: Content to write.
        encoding: File encoding.
    
    Returns:
        True on success, False on error.
    """
    try:
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except (IOError, OSError):
        return False
