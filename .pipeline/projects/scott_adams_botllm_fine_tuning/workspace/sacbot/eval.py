"""Evaluation harness — automated metrics + human eval interface."""

from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import nltk
import pandas as pd
import textstat
from nltk.tokenize import word_tokenize
from rouge_score import rouge_scorer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# Ensure NLTK data is available
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)


# ------ Data classes ------

@dataclass
class SampleMetrics:
    """Metrics for a single generated sample."""
    sample_id: str
    topic: str
    content_type: str
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    type_token_ratio: float
    readability_grade: float
    sentiment_polarity: float
    sentiment_subjectivity: float
    has_rhetorical_question: bool
    has_direct_address: bool
    has_probability_language: bool
    paragraph_count: int
    avg_paragraph_length: float
    rouge_l: float
    style_match_score: float  # 0-1, higher is more like Scott Adams


@dataclass
class EvaluationReport:
    """Aggregated evaluation report."""
    total_samples: int
    avg_word_count: float
    avg_sentence_count: float
    avg_type_token_ratio: float
    avg_readability_grade: float
    avg_sentiment_polarity: float
    avg_sentiment_subjectivity: float
    pct_with_rhetorical_question: float
    pct_with_direct_address: float
    pct_with_probability_language: float
    avg_rouge_l: float
    avg_style_match_score: float
    per_topic: Dict[str, Dict[str, float]] = field(default_factory=dict)
    per_content_type: Dict[str, Dict[str, float]] = field(default_factory=dict)


# ------ Automated metrics ------

def compute_sample_metrics(
    sample: Dict[str, Any],
    ground_truth: Optional[str] = None,
) -> SampleMetrics:
    """Compute metrics for a single generated sample.

    Args:
        sample: Dict with keys "id", "topic", "content_type", "content".
        ground_truth: Optional ground truth text for ROUGE comparison.

    Returns:
        SampleMetrics object.
    """
    content = sample["content"]
    topic = sample["topic"]
    content_type = sample["content_type"]
    sample_id = sample.get("id", "unknown")

    # Basic metrics
    words = word_tokenize(content)
    word_count = len(words)
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    avg_sentence_length = word_count / max(sentence_count, 1)

    # Type-token ratio
    unique_words = set(w.lower() for w in words)
    type_token_ratio = len(unique_words) / max(word_count, 1)

    # Readability
    flesch_score = textstat.flesch_reading_ease(content)
    # Convert Flesch Reading Ease to approximate grade level
    # Flesch score: 120-130 = 5th grade, 0-10 = college graduate
    # Approximate: grade = (118 - flesch_score) / 2
    readability_grade = (118 - flesch_score) / 2

    # Sentiment
    analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = analyzer.polarity_scores(content)
    sentiment_polarity = sentiment_scores["compound"]
    # VADER polarity_scores returns compound, pos, neu, neg — compute subjectivity from pos+neg
    pos = sentiment_scores["pos"]
    neg = sentiment_scores["neg"]
    sentiment_subjectivity = pos + neg  # in [0, 1]

    # Rhetorical devices
    has_rhetorical_question = bool(re.search(r'\?', content))
    has_direct_address = bool(re.search(r'\b(you|your|yourself)\b', content, re.IGNORECASE))
    has_probability_language = bool(re.search(r'\b(probability|chances|likely|probably|maybe)\b', content, re.IGNORECASE))

    # Paragraph metrics
    paragraphs = re.split(r'\n\s*\n', content)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    paragraph_count = len(paragraphs)
    avg_paragraph_length = word_count / max(paragraph_count, 1)

    # ROUGE-L (if ground truth available)
    rouge_l = 0.0
    if ground_truth:
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        scores = scorer.score(ground_truth, content)
        rouge_l = scores["rougeL"].fmeasure

    # Style match score (simplified)
    style_match_score = _compute_style_match(content)

    return SampleMetrics(
        sample_id=sample_id,
        topic=topic,
        content_type=content_type,
        word_count=word_count,
        sentence_count=sentence_count,
        avg_sentence_length=avg_sentence_length,
        type_token_ratio=type_token_ratio,
        readability_grade=readability_grade,
        sentiment_polarity=sentiment_polarity,
        sentiment_subjectivity=sentiment_subjectivity,
        has_rhetorical_question=has_rhetorical_question,
        has_direct_address=has_direct_address,
        has_probability_language=has_probability_language,
        paragraph_count=paragraph_count,
        avg_paragraph_length=avg_paragraph_length,
        rouge_l=rouge_l,
        style_match_score=style_match_score,
    )


def _compute_style_match(content: str) -> float:
    """Compute style match score (0-1) based on Scott Adams' style markers.

    This is a simplified heuristic. A more sophisticated version would use
    a trained classifier or embedding similarity.
    """
    score = 0.0
    markers = [
        (r'\b(you|your)\b', 0.2),
        (r'\b(probability|chances|likely)\b', 0.2),
        (r'\b(habits|systems|processes)\b', 0.15),
        (r'\b(success|management|psychology)\b', 0.15),
        (r'\b(I|me|my)\b', 0.1),
        (r'\b(remember|stop|start)\b', 0.1),
        (r'\?', 0.1),
    ]

    for pattern, weight in markers:
        if re.search(pattern, content, re.IGNORECASE):
            score += weight

    # Normalize to 0-1
    return min(score, 1.0)


def compute_aggregate_metrics(
    samples: List[Dict[str, Any]],
    ground_truths: Optional[Dict[str, str]] = None,
) -> EvaluationReport:
    """Compute aggregate metrics across all samples.

    Args:
        samples: List of sample dicts.
        ground_truths: Optional dict mapping sample_id to ground truth text.

    Returns:
        EvaluationReport object.
    """
    if ground_truths is None:
        ground_truths = {}

    metrics_list = []
    for sample in samples:
        gt = ground_truths.get(sample.get("id", "unknown"))
        metrics = compute_sample_metrics(sample, gt)
        metrics_list.append(metrics)

    if not metrics_list:
        return EvaluationReport(
            total_samples=0,
            avg_word_count=0,
            avg_sentence_count=0,
            avg_type_token_ratio=0,
            avg_readability_grade=0,
            avg_sentiment_polarity=0,
            avg_sentiment_subjectivity=0,
            pct_with_rhetorical_question=0,
            pct_with_direct_address=0,
            pct_with_probability_language=0,
            avg_rouge_l=0,
            avg_style_match_score=0,
        )

    # Compute aggregates
    total = len(metrics_list)
    avg_word_count = statistics.mean([m.word_count for m in metrics_list])
    avg_sentence_count = statistics.mean([m.sentence_count for m in metrics_list])
    avg_type_token_ratio = statistics.mean([m.type_token_ratio for m in metrics_list])
    avg_readability_grade = statistics.mean([m.readability_grade for m in metrics_list])
    avg_sentiment_polarity = statistics.mean([m.sentiment_polarity for m in metrics_list])
    avg_sentiment_subjectivity = statistics.mean([m.sentiment_subjectivity for m in metrics_list])
    pct_rhetorical = sum(1 for m in metrics_list if m.has_rhetorical_question) / total * 100
    pct_direct = sum(1 for m in metrics_list if m.has_direct_address) / total * 100
    pct_probability = sum(1 for m in metrics_list if m.has_probability_language) / total * 100
    avg_rouge_l = statistics.mean([m.rouge_l for m in metrics_list])
    avg_style_match = statistics.mean([m.style_match_score for m in metrics_list])

    # Per-topic and per-content-type aggregates
    per_topic: Dict[str, List[SampleMetrics]] = {}
    per_content_type: Dict[str, List[SampleMetrics]] = {}

    for m in metrics_list:
        per_topic.setdefault(m.topic, []).append(m)
        per_content_type.setdefault(m.content_type, []).append(m)

    def _avg_dict(metrics: List[SampleMetrics]) -> Dict[str, float]:
        if not metrics:
            return {}
        return {
            "avg_word_count": statistics.mean([m.word_count for m in metrics]),
            "avg_sentence_count": statistics.mean([m.sentence_count for m in metrics]),
            "avg_type_token_ratio": statistics.mean([m.type_token_ratio for m in metrics]),
            "avg_readability_grade": statistics.mean([m.readability_grade for m in metrics]),
            "avg_sentiment_polarity": statistics.mean([m.sentiment_polarity for m in metrics]),
            "avg_style_match_score": statistics.mean([m.style_match_score for m in metrics]),
        }

    return EvaluationReport(
        total_samples=total,
        avg_word_count=avg_word_count,
        avg_sentence_count=avg_sentence_count,
        avg_type_token_ratio=avg_type_token_ratio,
        avg_readability_grade=avg_readability_grade,
        avg_sentiment_polarity=avg_sentiment_polarity,
        avg_sentiment_subjectivity=avg_sentiment_subjectivity,
        pct_with_rhetorical_question=pct_rhetorical,
        pct_with_direct_address=pct_direct,
        pct_with_probability_language=pct_probability,
        avg_rouge_l=avg_rouge_l,
        avg_style_match_score=avg_style_match,
        per_topic={k: _avg_dict(v) for k, v in per_topic.items()},
        per_content_type={k: _avg_dict(v) for k, v in per_content_type.items()},
    )


# ------ Human eval interface ------

def generate_human_eval_prompts(
    samples: List[Dict[str, Any]],
    output_path: str = "human_eval_prompts.json",
) -> None:
    """Generate prompts for human evaluation.

    Creates a JSON file with samples to be rated by humans on:
    - Style match (1-5)
    - Usefulness (1-5)
    - Readability (1-5)
    - Overall quality (1-5)

    Args:
        samples: List of sample dicts.
        output_path: Path to output JSON file.
    """
    prompts = []
    for sample in samples:
        prompts.append({
            "id": sample.get("id", "unknown"),
            "topic": sample["topic"],
            "content_type": sample["content_type"],
            "content": sample["content"],
            "rating_style_match": None,
            "rating_usefulness": None,
            "rating_readability": None,
            "rating_overall": None,
            "comments": "",
        })

    Path(output_path).write_text(json.dumps(prompts, indent=2), encoding="utf-8")
    print(f"Human eval prompts written to {output_path}")


def load_human_eval_results(
    input_path: str,
) -> List[Dict[str, Any]]:
    """Load human evaluation results from JSON file.

    Args:
        input_path: Path to human eval results JSON file.

    Returns:
        List of dicts with ratings.
    """
    return json.loads(Path(input_path).read_text(encoding="utf-8"))


def compute_human_eval_aggregate(
    results: List[Dict[str, Any]],
) -> Dict[str, float]:
    """Compute aggregate metrics from human evaluation results.

    Args:
        results: List of human eval result dicts.

    Returns:
        Dict with average ratings.
    """
    ratings = ["rating_style_match", "rating_usefulness", "rating_readability", "rating_overall"]
    aggregates = {}
    for rating in ratings:
        values = [r[rating] for r in results if r.get(rating) is not None]
        if values:
            aggregates[rating] = statistics.mean(values)
        else:
            aggregates[rating] = 0.0
    return aggregates
