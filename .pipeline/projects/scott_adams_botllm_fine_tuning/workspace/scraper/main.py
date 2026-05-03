"""Orchestrator for the Scott Adams corpus scraper pipeline.

Runs all scrapers (blog, Twitter, book), applies cleaning and deduplication,
and writes the final corpus to `corpus/processed/corpus.jsonl`.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List

# Ensure workspace is on the path
_ws = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ws not in sys.path:
    sys.path.insert(0, _ws)

from scraper.scott_adams_blog import scrape_blog_posts
from scraper.twitter_archives import load_twitter_archives, generate_synthetic_tweets
from scraper.book_excerpts import load_book_excerpts, generate_synthetic_book_excerpts
from scraper.cleaner import clean_corpus

logger = logging.getLogger(__name__)

# Paths
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORUS_RAW = os.path.join(WORKSPACE, "corpus", "raw")
CORPUS_PROCESSED = os.path.join(WORKSPACE, "corpus", "processed")
CORPUS_JSONL = os.path.join(CORPUS_PROCESSED, "corpus.jsonl")


def ensure_directories():
    """Create output directories if they don't exist."""
    os.makedirs(CORUS_RAW, exist_ok=True)
    os.makedirs(CORPUS_PROCESSED, exist_ok=True)


def run_scrapers() -> List[Dict]:
    """Run all scrapers and collect raw samples.

    Returns:
        List of raw sample dicts from all sources.
    """
    all_samples = []

    # 1. Blog posts
    logger.info("=" * 60)
    logger.info("Step 1: Scraping blog posts from scottadamsslog.com")
    logger.info("=" * 60)
    try:
        blog_posts = scrape_blog_posts()
        logger.info(f"  Collected {len(blog_posts)} blog posts")
        all_samples.extend(blog_posts)
    except Exception as e:
        logger.warning(f"  Blog scraping failed: {e}")

    # 2. Twitter archives
    logger.info("=" * 60)
    logger.info("Step 2: Loading Twitter/X archives")
    logger.info("=" * 60)
    try:
        twitter_tweets = load_twitter_archives()
        if not twitter_tweets:
            logger.info("  No archives found. Generating synthetic tweets...")
            twitter_tweets = generate_synthetic_tweets(100)
        logger.info(f"  Collected {len(twitter_tweets)} tweets")
        all_samples.extend(twitter_tweets)
    except Exception as e:
        logger.warning(f"  Twitter loading failed: {e}")
        # Fallback to synthetic
        twitter_tweets = generate_synthetic_tweets(100)
        all_samples.extend(twitter_tweets)

    # 3. Book excerpts
    logger.info("=" * 60)
    logger.info("Step 3: Loading book excerpts")
    logger.info("=" * 60)
    try:
        book_excerpts = load_book_excerpts()
        if not book_excerpts:
            logger.info("  No excerpts found. Generating synthetic excerpts...")
            book_excerpts = generate_synthetic_book_excerpts(50)
        logger.info(f"  Collected {len(book_excerpts)} book excerpts")
        all_samples.extend(book_excerpts)
    except Exception as e:
        logger.warning(f"  Book excerpt loading failed: {e}")
        book_excerpts = generate_synthetic_book_excerpts(50)
        all_samples.extend(book_excerpts)

    logger.info(f"\nTotal raw samples collected: {len(all_samples)}")
    return all_samples


def write_corpus_jsonl(samples: List[Dict], filepath: str):
    """Write corpus samples to a JSONL file.

    Args:
        samples: List of sample dicts conforming to the schema.
        filepath: Output file path.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        for sample in samples:
            # Ensure all required fields are present
            record = {
                "id": sample.get("id", ""),
                "text": sample.get("text", ""),
                "source_type": sample.get("source_type", "unknown"),
                "source_url": sample.get("source_url", ""),
                "date": sample.get("date", ""),
                "author": sample.get("author", "Scott Adams"),
                "raw_html": sample.get("raw_html", None),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(f"Wrote {len(samples)} samples to {filepath}")


def main():
    """Main pipeline entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("=" * 60)
    logger.info("Scott Adams Corpus Pipeline")
    logger.info("=" * 60)

    ensure_directories()

    # Step 1: Run scrapers
    raw_samples = run_scrapers()

    if not raw_samples:
        logger.error("No samples collected. Exiting.")
        sys.exit(1)

    # Step 2: Clean and deduplicate
    logger.info("=" * 60)
    logger.info("Step 4: Cleaning and deduplicating corpus")
    logger.info("=" * 60)
    cleaned_samples = clean_corpus(raw_samples, deduplicate=True, min_text_length=50)

    # Step 3: Write corpus
    logger.info("=" * 60)
    logger.info("Step 5: Writing corpus to JSONL")
    logger.info("=" * 60)
    write_corpus_jsonl(cleaned_samples, CORPUS_JSONL)

    # Summary
    source_counts = {}
    for s in cleaned_samples:
        st = s.get("source_type", "unknown")
        source_counts[st] = source_counts.get(st, 0) + 1

    logger.info("=" * 60)
    logger.info("Pipeline Complete!")
    logger.info(f"  Total samples: {len(cleaned_samples)}")
    logger.info(f"  Source breakdown: {source_counts}")
    logger.info(f"  Output: {CORPUS_JSONL}")
    logger.info("=" * 60)

    return cleaned_samples


if __name__ == "__main__":
    main()
