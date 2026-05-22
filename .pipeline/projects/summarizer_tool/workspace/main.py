"""Main entry point for the summarizer tool CLI."""

import argparse
import sys
from summarizer_tool.sources.pdf_summarizer import PDFSummarizer
from summarizer_tool.sources.youtube_summarizer import YouTubeSummarizer
from summarizer_tool.sources.web_summarizer import WebSummarizer


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Summarizer Tool - Summarize PDFs, YouTube videos, and web pages."
    )
    
    parser.add_argument(
        "--source-type",
        type=str,
        required=True,
        choices=["pdf", "youtube", "web"],
        help="Type of source to summarize (pdf, youtube, web)"
    )
    
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Path to PDF file or URL for YouTube/web content"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (optional, prints to stdout if not specified)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    try:
        if args.source_type == "pdf":
            summarizer = PDFSummarizer()
            summary = summarizer.summarize(args.source)
        elif args.source_type == "youtube":
            summarizer = YouTubeSummarizer()
            summary = summarizer.summarize(args.source)
        elif args.source_type == "web":
            summarizer = WebSummarizer()
            summary = summarizer.summarize(args.source)
        else:
            print(f"Error: Unknown source type: {args.source_type}")
            sys.exit(1)
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"Summary written to {args.output}")
        else:
            print(summary)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
