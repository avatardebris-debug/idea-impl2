"""Markdown parser for basic elements."""

import re


def parse_markdown(markdown_content: str) -> str:
    """
    Parse markdown content and convert to HTML.
    
    Handles the following markdown elements:
    - Headers: # to ######
    - Bold: **text**
    - Italic: *text*
    - Code blocks: ```code```
    - Links: [text](url)
    
    Args:
        markdown_content: The markdown text to parse
        
    Returns:
        HTML string with converted markdown elements
    """
    lines = markdown_content.split('\n')
    html_lines = []
    
    for line in lines:
        # Process code blocks first (```code```)
        line = process_code_blocks(line)
        
        # Process headers (# to ######)
        line = process_headers(line)
        
        # Process links ([text](url))
        line = process_links(line)
        
        # Process bold (**text**)
        line = process_bold(line)
        
        # Process italic (*text*)
        line = process_italic(line)
        
        # If line is not empty after processing, add it
        if line.strip():
            html_lines.append(line)
    
    return '\n'.join(html_lines)


def process_code_blocks(line: str) -> str:
    """Process inline code blocks: ```code```"""
    # Match inline code blocks: ```code```
    pattern = r'```(.*?)```'
    replacement = r'<code>\1</code>'
    return re.sub(pattern, replacement, line, flags=re.DOTALL)


def process_headers(line: str) -> str:
    """Process headers from # to ######"""
    # Match headers: # Header, ## Header, etc.
    pattern = r'^(#{1,6})\s+(.+)$'
    match = re.match(pattern, line)
    
    if match:
        level = len(match.group(1))
        text = match.group(2)
        return f'<h{level}>{text}</h{level}>'
    
    return line


def process_links(line: str) -> str:
    """Process links: [text](url)"""
    # Match links: [text](url)
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    replacement = r'<a href="\2">\1</a>'
    return re.sub(pattern, replacement, line)


def process_bold(line: str) -> str:
    """Process bold text: **text**"""
    # Match bold: **text**
    pattern = r'\*\*(.+?)\*\*'
    replacement = r'<strong>\1</strong>'
    return re.sub(pattern, replacement, line)


def process_italic(line: str) -> str:
    """Process italic text: *text*"""
    # Match italic: *text*
    pattern = r'\*(.+?)\*'
    replacement = r'<em>\1</em>'
    return re.sub(pattern, replacement, line)
