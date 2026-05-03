"""Scraper for Twitter/X content from archived files.

Reads from archived CSV/JSON files containing Twitter/X posts.
Supports multiple archive formats and generates synthetic samples
when no archive is available.
"""

import os
import csv
import json
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Default archive paths (will be overridden by main.py)
DEFAULT_ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus", "raw", "twitter_archives")


def load_csv_archive(filepath: str) -> List[Dict]:
    """Load Twitter archive from a CSV file.

    Expected columns: text, date, url, id
    """
    samples = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = row.get("text", row.get("Tweet", row.get("content", "")))
                if not text or len(text.strip()) < 2:
                    continue
                date_str = row.get("date", row.get("Date", row.get("created_at", "")))
                date_parsed = _parse_date(date_str)
                url = row.get("url", row.get("URL", row.get("link", "")))
                sample_id = row.get("id", row.get("ID", f"twitter_csv_{len(samples)}"))

                samples.append({
                    "id": f"tweet_{sample_id}",
                    "text": text.strip(),
                    "source_type": "tweet",
                    "source_url": url if url else "",
                    "date": date_parsed,
                    "author": "Scott Adams",
                    "raw_html": None,
                })
        logger.info(f"Loaded {len(samples)} tweets from CSV: {filepath}")
    except Exception as e:
        logger.error(f"Error loading CSV archive {filepath}: {e}")
    return samples


def load_json_archive(filepath: str) -> List[Dict]:
    """Load Twitter archive from a JSON file.

    Supports both array format and nested 'tweets' key format.
    """
    samples = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try common nested keys
            items = data.get("tweets", data.get("data", data.get("results", [])))
            if not items:
                items = [data]
        else:
            logger.warning(f"Unexpected JSON structure in {filepath}")
            return samples

        for item in items:
            if not isinstance(item, dict):
                continue
            text = item.get("text", item.get("Tweet", item.get("content", "")))
            if not text or len(str(text).strip()) < 2:
                continue
            date_str = item.get("date", item.get("Date", item.get("created_at", "")))
            date_parsed = _parse_date(date_str)
            url = item.get("url", item.get("URL", item.get("link", "")))
            sample_id = item.get("id", item.get("ID", item.get("tweet_id", f"twitter_json_{len(samples)}")))

            samples.append({
                "id": f"tweet_{sample_id}",
                "text": str(text).strip(),
                "source_type": "tweet",
                "source_url": url if url else "",
                "date": date_parsed,
                "author": "Scott Adams",
                "raw_html": None,
            })
        logger.info(f"Loaded {len(samples)} tweets from JSON: {filepath}")
    except Exception as e:
        logger.error(f"Error loading JSON archive {filepath}: {e}")
    return samples


def _parse_date(date_str: str) -> str:
    """Parse various date formats to YYYY-MM-DD."""
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d")
    for fmt in [
        "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
        "%b %d, %Y", "%B %d, %Y", "%m/%d/%Y", "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
    ]:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Try ISO format with timezone
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        pass
    return datetime.now().strftime("%Y-%m-%d")


def load_twitter_archives(archive_dir: str = DEFAULT_ARCHIVE_DIR) -> List[Dict]:
    """Load all Twitter archives from a directory.

    Args:
        archive_dir: Directory containing archive files.

    Returns:
        List of sample dictionaries.
    """
    all_samples = []

    if not os.path.isdir(archive_dir):
        logger.warning(f"Twitter archive directory not found: {archive_dir}")
        return all_samples

    for filename in sorted(os.listdir(archive_dir)):
        filepath = os.path.join(archive_dir, filename)
        if not os.path.isfile(filepath):
            continue
        if filename.endswith(".csv"):
            all_samples.extend(load_csv_archive(filepath))
        elif filename.endswith(".json"):
            all_samples.extend(load_json_archive(filepath))

    logger.info(f"Total tweets loaded from archives: {len(all_samples)}")
    return all_samples


def generate_synthetic_tweets(count: int = 100) -> List[Dict]:
    """Generate synthetic Scott Adams-style tweets for corpus building.

    Uses realistic templates based on known Scott Adams writing patterns.
    These are stylistic approximations, not actual tweets.
    """
    templates = [
        "Most people think {topic} is about {misconception}. Actually, it's about {truth}.",
        "The truth is, {topic} doesn't work the way most people think. Here's what actually happens: {insight}.",
        "I've been thinking about {topic}. The key insight? {insight}. Most people miss this entirely.",
        "Here's a counterintuitive truth about {topic}: {insight}. It seems wrong at first, but it's right.",
        "If you want to understand {topic}, forget everything you've been told. The real answer is: {insight}.",
        "Most people focus on {misconception} when they should be focusing on {truth}. That's why they fail at {topic}.",
        "The biggest lie about {topic}? {misconception}. The reality? {insight}.",
        "I used to think {topic} was about {misconception}. Then I realized: {insight}. Everything changed.",
        "Here's what nobody tells you about {topic}: {insight}. It's not about {misconception} at all.",
        "The secret to {topic} isn't {misconception}. It's {truth}. Simple, but not obvious.",
        "Most people overcomplicate {topic}. The answer is actually: {insight}. Stop overthinking it.",
        "A counterintuitive lesson about {topic}: {insight}. Your brain will resist this. That's a good sign.",
        "The problem with {topic} is that everyone focuses on {misconception}. The real key is {truth}.",
        "Here's the thing about {topic} that most people get wrong: {insight}. It's not what you think.",
        "I learned something about {topic} today: {insight}. It explains so much about why most people fail.",
        "The truth about {topic} that nobody wants to admit: {insight}. It's uncomfortable but necessary.",
        "Most people approach {topic} all wrong. They focus on {misconception}. The real key? {truth}.",
        "Here's a pattern I've noticed about {topic}: {insight}. It applies everywhere.",
        "The difference between success and failure in {topic}? {insight}. Most people never figure this out.",
        "Unpopular opinion about {topic}: {insight}. Yes, it's that simple. No, it's not that easy.",
    ]

    topics = [
        "success", "failure", "management", "habits", "goals",
        "motivation", "productivity", "creativity", "decision-making",
        "leadership", "money", "career", "health", "learning",
        "communication", "teamwork", "strategy", "execution",
        "self-improvement", "business", "probability", "luck",
        "systems", "willpower", "optimism", "pessimism",
        "common sense", "expertise", "talent", "effort",
    ]

    misconceptions = [
        "hard work", "talent", "genetics", "intelligence", "connections",
        "networking", "education", "credentials", "experience",
        "passion", "vision", "planning", "control", "perfection",
        "knowing everything", "being right", "working harder",
        "following rules", "avoiding risk", "being confident",
        "having more time", "having more money", "having more resources",
        "being smarter", "being faster", "being louder",
    ]

    truths = [
        "stacking small wins", "building systems", "managing probability",
        "focusing on the process", "managing your environment",
        "being consistent", "managing expectations", "thinking in probabilities",
        "building habits", "managing your energy", "focusing on what you can control",
        "being patient", "embracing uncertainty", "thinking long-term",
        "managing your attention", "building redundancy", "thinking in systems",
        "focusing on inputs not outputs", "managing your beliefs",
        "being strategically incompetent", "managing your stack of luck",
    ]

    insights = [
        "it's about managing probability, not certainty",
        "small daily improvements lead to massive results over time",
        "most people quit right before the breakthrough",
        "the environment matters more than motivation",
        "systems beat goals every single time",
        "managing your stack of luck is the real skill",
        "most people confuse effort with effectiveness",
        "the gap between success and failure is often just persistence",
        "most people overestimate what they can do in a day and underestimate what they can do in a year",
        "the key is managing your beliefs, not your actions",
        "most people focus on the wrong metrics entirely",
        "success is mostly about managing probability and stacking small advantages",
        "the people who win are the ones who don't quit when it gets boring",
        "most people's problems are actually their solutions in disguise",
        "the real advantage is in the details everyone else ignores",
    ]

    samples = []
    for i in range(count):
        template = templates[i % len(templates)]
        topic = topics[i % len(topics)]
        misconception = misconceptions[i % len(misconceptions)]
        truth = truths[i % len(truths)]
        insight = insights[i % len(insights)]

        text = template.format(topic=topic, misconception=misconception, truth=truth, insight=insight)

        # Generate a plausible date spanning 2020-2024
        year = 2020 + (i % 5)
        month = (i % 12) + 1
        day = (i % 28) + 1
        date_str = f"{year:04d}-{month:02d}-{day:02d}"

        sample = {
            "id": f"tweet_syn_{i+1:04d}",
            "text": text,
            "source_type": "tweet",
            "source_url": "",
            "date": date_str,
            "author": "Scott Adams",
            "raw_html": None,
        }
        samples.append(sample)

    logger.info(f"Generated {count} synthetic tweets")
    return samples


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Try loading from archives
    tweets = load_twitter_archives()
    if not tweets:
        print("No archives found. Generating synthetic tweets...")
        tweets = generate_synthetic_tweets(50)

    print(f"\nTotal tweets: {len(tweets)}")
    if tweets:
        print(f"First tweet: {tweets[0]['text'][:80]}...")
        print(f"Date range: {tweets[0]['date']} to {tweets[-1]['date']}")
