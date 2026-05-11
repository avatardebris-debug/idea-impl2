"""Utility tools for forensic analysis."""

import re
from typing import List, Dict, Optional


def extract_text_from_html(html_content: str) -> str:
    """Extract plain text from HTML content."""
    # Remove script and style elements
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def clean_text(text: str) -> str:
    """Clean and normalize text for analysis."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep alphanumeric and spaces
    text = re.sub(r'[^a-zA-Z0-9\s.,;:!?()\-]', ' ', text)
    return text.strip()


def extract_numbers_from_text(text: str) -> List[float]:
    """Extract numeric values from text."""
    # Match numbers with optional commas and decimals
    pattern = r'[\$]?[\d,]+(?:\.\d+)?'
    matches = re.findall(pattern, text)
    numbers = []
    for match in matches:
        try:
            # Remove commas and convert to float
            clean_num = match.replace(',', '')
            numbers.append(float(clean_num))
        except ValueError:
            continue
    return numbers


def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values."""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def format_percentage(value: float) -> str:
    """Format a decimal value as a percentage string."""
    return f"{value:.2%}"


def extract_section_content(text: str, section_pattern: str) -> str:
    """Extract content of a specific section from text."""
    pattern = rf'{section_pattern}\s*[:\-]?\s*(.*?)(?=\n\s*\d+\.\s|\Z)'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def validate_filing_type(filing_type: str) -> bool:
    """Validate if the filing type is supported."""
    supported_types = ['10-K', '10-Q', '8-K', '20-F', '40-F']
    return filing_type in supported_types


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe storage."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename
