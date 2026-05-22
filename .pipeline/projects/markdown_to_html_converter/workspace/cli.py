"""Command-line interface for the markdown to HTML converter."""

import argparse
import sys
from .parser import parse_markdown
from .template import generate_html


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Convert markdown files to HTML with embedded CSS styling."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input markdown file"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the output HTML file"
    )
    
    args = parser.parse_args()
    
    # Read input markdown file
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Parse markdown to HTML
    html_content = parse_markdown(markdown_content)
    
    # Generate complete HTML document
    html_document = generate_html(html_content)
    
    # Write output HTML file
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(html_document)
        print(f"Successfully converted '{args.input}' to '{args.output}'")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
