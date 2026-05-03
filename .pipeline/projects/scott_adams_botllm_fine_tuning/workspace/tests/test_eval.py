"""Tests for sacbot.eval module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sacbot.eval import (
    compute_sample_metrics,
    compute_aggregate_metrics,
    generate_human_eval_prompts,
    load_human_eval_results,
    compute_human_eval_aggregate,
    SampleMetrics,
    EvaluationReport,
)


class TestComputeSampleMetrics:
    """Tests for compute_sample_metrics function."""

    def test_basic_metrics(self):
        """compute_sample_metrics should compute basic metrics."""
        sample = {
            "id": "test_001",
            "topic": "success habits",
            "content_type": "blog",
            "content": "Success is about building habits. You need to be consistent.",
        }
        metrics = compute_sample_metrics(sample)
        assert metrics.sample_id == "test_001"
        assert metrics.topic == "success habits"
        assert metrics.content_type == "blog"
        assert metrics.word_count > 0
        assert metrics.sentence_count > 0
        assert metrics.avg_sentence_length > 0
        assert metrics.type_token_ratio > 0
        assert metrics.readability_grade > 0
        assert metrics.sentiment_polarity >= -1
        assert metrics.sentiment_polarity <= 1
        assert metrics.sentiment_subjectivity >= 0
        assert metrics.sentiment_subjectivity <= 1

    def test_rhetorical_question(self):
        """compute_sample_metrics should detect rhetorical questions."""
        sample = {
            "id": "test_002",
            "topic": "test",
            "content_type": "blog",
            "content": "Why do most people fail? Because they don't build systems.",
        }
        metrics = compute_sample_metrics(sample)
        assert metrics.has_rhetorical_question is True

    def test_direct_address(self):
        """compute_sample_metrics should detect direct address."""
        sample = {
            "id": "test_003",
            "topic": "test",
            "content_type": "blog",
            "content": "You need to build systems to succeed.",
        }
        metrics = compute_sample_metrics(sample)
        assert metrics.has_direct_address is True

    def test_probability_language(self):
        """compute_sample_metrics should detect probability language."""
        sample = {
            "id": "test_004",
            "topic": "test",
            "content_type": "blog",
            "content": "The probability of success is high if you try.",
        }
        metrics = compute_sample_metrics(sample)
        assert metrics.has_probability_language is True

    def test_rouge_score(self):
        """compute_sample_metrics should compute ROUGE-L score."""
        sample = {
            "id": "test_005",
            "topic": "test",
            "content_type": "blog",
            "content": "Success is about building habits.",
        }
        ground_truth = "Success is about building habits. You need to be consistent."
        metrics = compute_sample_metrics(sample, ground_truth=ground_truth)
        assert metrics.rouge_l >= 0
        assert metrics.rouge_l <= 1


class TestComputeAggregateMetrics:
    """Tests for compute_aggregate_metrics function."""

    def test_aggregate_metrics(self):
        """compute_aggregate_metrics should compute aggregate metrics."""
        samples = [
            {
                "id": "test_001",
                "topic": "success habits",
                "content_type": "blog",
                "content": "Success is about building habits.",
            },
            {
                "id": "test_002",
                "topic": "management",
                "content_type": "tweet",
                "content": "Management is hard.",
            },
        ]
        metrics = compute_aggregate_metrics(samples)
        assert isinstance(metrics, EvaluationReport)
        assert metrics.total_samples == 2
        assert metrics.avg_word_count > 0
        assert metrics.avg_sentence_count > 0
        assert metrics.avg_readability_grade > 0
        assert metrics.avg_sentiment_polarity >= -1
        assert metrics.avg_sentiment_polarity <= 1
        assert metrics.avg_sentiment_subjectivity >= 0
        assert metrics.avg_sentiment_subjectivity <= 1
        assert metrics.avg_type_token_ratio > 0
        assert metrics.avg_rouge_l >= 0
        assert metrics.avg_rouge_l <= 1
        assert metrics.pct_with_rhetorical_question >= 0
        assert metrics.pct_with_rhetorical_question <= 100
        assert metrics.pct_with_direct_address >= 0
        assert metrics.pct_with_direct_address <= 100
        assert metrics.pct_with_probability_language >= 0
        assert metrics.pct_with_probability_language <= 100


class TestGenerateHumanEvalPrompts:
    """Tests for generate_human_eval_prompts function."""

    def test_generate_prompts(self, tmp_path):
        """generate_human_eval_prompts should generate prompts file."""
        samples = [
            {
                "id": "test_001",
                "topic": "success habits",
                "content_type": "blog",
                "content": "Success is about building habits.",
            },
        ]
        output_path = str(tmp_path / "prompts.json")
        generate_human_eval_prompts(samples, output_path=output_path)
        # File should exist
        assert Path(output_path).exists()
        # Should contain the sample
        data = json.loads(Path(output_path).read_text())
        assert len(data) == 1
        assert data[0]["id"] == "test_001"
        assert "Success is about building habits" in data[0]["content"]


class TestLoadHumanEvalResults:
    """Tests for load_human_eval_results function."""

    def test_load_results(self, tmp_path):
        """load_human_eval_results should load results from JSON file."""
        results_file = tmp_path / "results.json"
        results_file.write_text(
            '[{"sample_id": "test_001", "rating_style_match": 8, "rating_usefulness": 7, "rating_readability": 9, "rating_overall": 8}]',
            encoding="utf-8",
        )
        results = load_human_eval_results(str(results_file))
        assert len(results) == 1
        assert results[0]["rating_style_match"] == 8
        assert results[0]["rating_usefulness"] == 7
        assert results[0]["rating_readability"] == 9
        assert results[0]["rating_overall"] == 8

    def test_load_empty_file(self, tmp_path):
        """load_human_eval_results should return empty list for empty file."""
        results_file = tmp_path / "results.json"
        results_file.write_text("[]", encoding="utf-8")
        results = load_human_eval_results(str(results_file))
        assert len(results) == 0


class TestComputeHumanEvalAggregate:
    """Tests for compute_human_eval_aggregate function."""

    def test_compute_aggregate(self):
        """compute_human_eval_aggregate should compute aggregate metrics."""
        results = [
            {"rating_style_match": 8, "rating_usefulness": 7, "rating_readability": 9, "rating_overall": 8},
            {"rating_style_match": 7, "rating_usefulness": 8, "rating_readability": 8, "rating_overall": 7},
        ]
        metrics = compute_human_eval_aggregate(results)
        assert metrics["rating_style_match"] == 7.5
        assert metrics["rating_usefulness"] == 7.5
        assert metrics["rating_readability"] == 8.5
        assert metrics["rating_overall"] == 7.5

    def test_compute_aggregate_with_missing_ratings(self):
        """compute_human_eval_aggregate should handle missing ratings."""
        results = [
            {"rating_style_match": 8, "rating_usefulness": None, "rating_readability": 9, "rating_overall": 8},
            {"rating_style_match": 7, "rating_usefulness": 8, "rating_readability": None, "rating_overall": 7},
        ]
        metrics = compute_human_eval_aggregate(results)
        assert metrics["rating_style_match"] == 7.5
        assert metrics["rating_usefulness"] == 8.0
        assert metrics["rating_readability"] == 9.0
        assert metrics["rating_overall"] == 7.5
