"""Quantitative style analysis for the Scott Adams corpus.

Computes statistical metrics about the corpus:
- Token length distributions
- Vocabulary richness (type-token ratio)
- Part-of-speech distribution (via spaCy or NLTK)
- Sentiment distribution
- N-gram frequency analysis
"""

import json
import logging
import os
import re
import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    logger.warning("spaCy not installed. POS tagging will be skipped.")

try:
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    HAS_VADER = True
except ImportError:
    HAS_VADER = False
    logger.warning("NLTK not installed. Sentiment analysis will be skipped.")


def load_corpus(filepath: str) -> List[Dict]:
    """Load corpus from JSONL file."""
    samples = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    logger.info(f"Loaded {len(samples)} samples from {filepath}")
    return samples


def compute_token_stats(samples: List[Dict]) -> Dict:
    """Compute token length statistics.

    Args:
        samples: List of corpus samples.

    Returns:
        Dictionary with token length statistics.
    """
    lengths = []
    for sample in samples:
        text = sample.get("text", "")
        # Count words (tokens)
        words = re.findall(r"\w+", text.lower())
        lengths.append(len(words))

    if not lengths:
        return {}

    stats = {
        "count": len(lengths),
        "mean": statistics.mean(lengths),
        "median": statistics.median(lengths),
        "stdev": statistics.stdev(lengths) if len(lengths) > 1 else 0,
        "min": min(lengths),
        "max": max(lengths),
        "q1": statistics.quantiles(lengths, n=4)[0],
        "q3": statistics.quantiles(lengths, n=4)[2],
        "percentiles": {
            p: statistics.quantiles(lengths, n=100)[p - 1] for p in [10, 25, 50, 75, 90, 95, 99]
        },
    }

    logger.info(f"Token stats: mean={stats['mean']:.1f}, median={stats['median']:.1f}, stdev={stats['stdev']:.1f}")
    return stats


def compute_vocabulary_richness(samples: List[Dict]) -> Dict:
    """Compute vocabulary richness metrics.

    Args:
        samples: List of corpus samples.

    Returns:
        Dictionary with vocabulary richness metrics.
    """
    all_words = []
    source_vocab = defaultdict(set)

    for sample in samples:
        text = sample.get("text", "")
        words = re.findall(r"\w+", text.lower())
        all_words.extend(words)
        source = sample.get("source_type", "unknown")
        source_vocab[source].update(words)

    if not all_words:
        return {}

    total_tokens = len(all_words)
    unique_tokens = len(set(all_words))

    # Type-Token Ratio (TTR)
    ttr = unique_tokens / total_tokens if total_tokens > 0 else 0

    # Source-specific TTR
    source_ttr = {}
    for source, vocab in source_vocab.items():
        source_words = [w for s in samples if s.get("source_type") == source for w in re.findall(r"\w+", s.get("text", "").lower())]
        if source_words:
            source_ttr[source] = len(set(source_words)) / len(source_words)

    # Most common words
    word_freq = Counter(all_words)
    top_words = word_freq.most_common(20)

    # Zipf's law check (rank vs frequency)
    zipf_data = []
    for rank, (word, freq) in enumerate(word_freq.most_common(), 1):
        zipf_data.append({"rank": rank, "word": word, "frequency": freq})

    return {
        "total_tokens": total_tokens,
        "unique_tokens": unique_tokens,
        "ttr": ttr,
        "source_ttr": source_ttr,
        "top_words": top_words,
        "zipf_data": zipf_data[:50],  # Top 50 for Zipf's law
    }


def compute_pos_distribution(samples: List[Dict]) -> Dict:
    """Compute part-of-speech distribution using spaCy.

    Args:
        samples: List of corpus samples.

    Returns:
        Dictionary with POS distribution.
    """
    if not HAS_SPACY:
        logger.warning("spaCy not available. Skipping POS analysis.")
        return {}

    # Load spaCy model
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
        return {}

    pos_counts = Counter()
    pos_by_source = defaultdict(Counter)

    for sample in samples:
        text = sample.get("text", "")
        doc = nlp(text)
        source = sample.get("source_type", "unknown")

        for token in doc:
            pos_counts[token.pos_] += 1
            pos_by_source[source][token.pos_] += 1

    # Normalize to percentages
    total_pos = sum(pos_counts.values())
    pos_percentages = {pos: (count / total_pos * 100) for pos, count in pos_counts.most_common()}

    source_pos_percentages = {}
    for source, counts in pos_by_source.items():
        source_total = sum(counts.values())
        source_pos_percentages[source] = {
            pos: (count / source_total * 100) for pos, count in counts.most_common()
        }

    return {
        "total_tokens_tagged": total_pos,
        "pos_percentages": pos_percentages,
        "source_pos_percentages": source_pos_percentages,
    }


def compute_sentiment_distribution(samples: List[Dict]) -> Dict:
    """Compute sentiment distribution using VADER.

    Args:
        samples: List of corpus samples.

    Returns:
        Dictionary with sentiment statistics.
    """
    if not HAS_VADER:
        logger.warning("NLTK VADER not available. Skipping sentiment analysis.")
        return {}

    sia = SentimentIntensityAnalyzer()
    sentiments = []
    sentiments_by_source = defaultdict(list)

    for sample in samples:
        text = sample.get("text", "")
        scores = sia.polarity_scores(text)
        sentiments.append(scores)
        source = sample.get("source_type", "unknown")
        sentiments_by_source[source].append(scores)

    if not sentiments:
        return {}

    # Aggregate statistics
    compound_scores = [s["compound"] for s in sentiments]
    pos_scores = [s["pos"] for s in sentiments]
    neg_scores = [s["neg"] for s in sentiments]
    neu_scores = [s["neu"] for s in sentiments]

    # Classify sentiments
    positive_count = sum(1 for s in compound_scores if s > 0.05)
    negative_count = sum(1 for s in compound_scores if s < -0.05)
    neutral_count = sum(1 for s in compound_scores if -0.05 <= s <= 0.05)

    # Source-specific sentiment
    source_sentiment = {}
    for source, source_scores in sentiments_by_source.items():
        source_compound = [s["compound"] for s in source_scores]
        source_positive = sum(1 for s in source_compound if s > 0.05)
        source_negative = sum(1 for s in source_compound if s < -0.05)
        source_neutral = sum(1 for s in source_compound if -0.05 <= s <= 0.05)
        source_sentiment[source] = {
            "mean_compound": statistics.mean(source_compound),
            "positive_pct": source_positive / len(source_compound) * 100,
            "negative_pct": source_negative / len(source_compound) * 100,
            "neutral_pct": source_neutral / len(source_compound) * 100,
        }

    return {
        "total_analyzed": len(sentiments),
        "mean_compound": statistics.mean(compound_scores),
        "mean_pos": statistics.mean(pos_scores),
        "mean_neg": statistics.mean(neg_scores),
        "mean_neu": statistics.mean(neu_scores),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "positive_pct": positive_count / len(sentiments) * 100,
        "negative_pct": negative_count / len(sentiments) * 100,
        "neutral_pct": neutral_count / len(sentiments) * 100,
        "source_sentiment": source_sentiment,
    }


def compute_ngram_frequency(samples: List[Dict], n: int = 3) -> Dict:
    """Compute n-gram frequency analysis.

    Args:
        samples: List of corpus samples.
        n: N-gram size.

    Returns:
        Dictionary with n-gram frequencies.
    """
    ngram_counts = Counter()

    for sample in samples:
        text = sample.get("text", "")
        words = re.findall(r"\w+", text.lower())
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i:i + n])
            ngram_counts[ngram] += 1

    top_ngrams = ngram_counts.most_common(50)

    return {
        "ngram_size": n,
        "total_ngrams": sum(ngram_counts.values()),
        "unique_ngrams": len(ngram_counts),
        "top_ngrams": top_ngrams,
    }


def run_quantitative_analysis(corpus_path: str) -> Dict:
    """Run all quantitative analyses on the corpus.

    Args:
        corpus_path: Path to corpus.jsonl file.

    Returns:
        Dictionary with all quantitative analysis results.
    """
    logger.info("Starting quantitative analysis...")

    samples = load_corpus(corpus_path)

    results = {
        "token_stats": compute_token_stats(samples),
        "vocabulary_richness": compute_vocabulary_richness(samples),
        "pos_distribution": compute_pos_distribution(samples),
        "sentiment_distribution": compute_sentiment_distribution(samples),
        "ngram_frequency": compute_ngram_frequency(samples, n=3),
    }

    logger.info("Quantitative analysis complete.")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    corpus_path = os.path.join(os.path.dirname(__file__), "..", "corpus", "processed", "corpus.jsonl")
    if not os.path.exists(corpus_path):
        logger.error(f"Corpus file not found: {corpus_path}")
        logger.info("Run scraper/main.py first to generate the corpus.")
        exit(1)

    results = run_quantitative_analysis(corpus_path)

    # Print summary
    print("\n" + "=" * 60)
    print("QUANTITATIVE ANALYSIS SUMMARY")
    print("=" * 60)

    if results["token_stats"]:
        ts = results["token_stats"]
        print(f"\nToken Statistics:")
        print(f"  Count: {ts['count']}")
        print(f"  Mean length: {ts['mean']:.1f} tokens")
        print(f"  Median length: {ts['median']:.1f} tokens")
        print(f"  Std dev: {ts['stdev']:.1f}")

    if results["vocabulary_richness"]:
        vr = results["vocabulary_richness"]
        print(f"\nVocabulary Richness:")
        print(f"  Total tokens: {vr['total_tokens']}")
        print(f"  Unique tokens: {vr['unique_tokens']}")
        print(f"  TTR: {vr['ttr']:.4f}")
        print(f"  Top 5 words: {vr['top_words'][:5]}")

    if results["sentiment_distribution"]:
        sd = results["sentiment_distribution"]
        print(f"\nSentiment Distribution:")
        print(f"  Mean compound: {sd['mean_compound']:.4f}")
        print(f"  Positive: {sd['positive_pct']:.1f}%")
        print(f"  Negative: {sd['negative_pct']:.1f}%")
        print(f"  Neutral: {sd['neutral_pct']:.1f}%")

    if results["ngram_frequency"]:
        ng = results["ngram_frequency"]
        print(f"\nTop 5 {ng['ngram_size']}-grams:")
        for ngram, count in ng["top_ngrams"][:5]:
            print(f"  '{ngram}': {count}")

    print("\n" + "=" * 60)
