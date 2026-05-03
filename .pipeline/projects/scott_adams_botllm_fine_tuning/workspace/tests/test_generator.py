"""Tests for sacbot.generator module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from sacbot.generator import (
    FewShotSample,
    GenerationResult,
    select_few_shot,
    _load_corpus,
    _topic_overlap,
    _length_similarity,
    build_prompt,
    call_llm,
    generate,
    SYSTEM_PROMPT,
)
from sacbot.types import ContentType


class TestFewShotSample:
    """Tests for FewShotSample dataclass."""

    def test_creation(self):
        """FewShotSample should be creatable with required fields."""
        sample = FewShotSample(
            text="Hello world",
            source_type="blog",
            topic="test",
        )
        assert sample.text == "Hello world"
        assert sample.source_type == "blog"
        assert sample.topic == "test"
        assert sample.length == 2  # "Hello world" has 2 words

    def test_explicit_length(self):
        """FewShotSample should allow explicit length."""
        sample = FewShotSample(
            text="Hello world",
            source_type="blog",
            topic="test",
            length=10,
        )
        assert sample.length == 10


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_creation(self):
        """GenerationResult should be creatable with all fields."""
        result = GenerationResult(
            content="Test content",
            model="gpt-4o",
            tokens_used=100,
            latency_seconds=1.5,
            prompt_tokens=50,
            few_shot_count=3,
            content_type="blog",
            topic="test",
        )
        assert result.content == "Test content"
        assert result.model == "gpt-4o"
        assert result.tokens_used == 100
        assert result.latency_seconds == 1.5
        assert result.prompt_tokens == 50
        assert result.few_shot_count == 3
        assert result.content_type == "blog"
        assert result.topic == "test"


class TestTopicOverlap:
    """Tests for _topic_overlap function."""

    def test_exact_match(self):
        """Exact topic match should return 1.0."""
        assert _topic_overlap("success habits", "success habits") == 1.0

    def test_partial_match(self):
        """Partial topic match should return value between 0 and 1."""
        overlap = _topic_overlap("success habits", "success probability")
        assert 0 < overlap < 1

    def test_no_match(self):
        """No topic overlap should return 0."""
        assert _topic_overlap("success habits", "management") == 0.0

    def test_empty_topic(self):
        """Empty topic should return 0."""
        assert _topic_overlap("", "success habits") == 0.0
        assert _topic_overlap("success habits", "") == 0.0


class TestLengthSimilarity:
    """Tests for _length_similarity function."""

    def test_exact_match(self):
        """Exact length match should return 1.0."""
        assert _length_similarity(100, 100) == 1.0

    def test_close_lengths(self):
        """Close lengths should return high similarity."""
        similarity = _length_similarity(100, 110)
        assert similarity > 0.9

    def test_different_lengths(self):
        """Different lengths should return lower similarity."""
        similarity = _length_similarity(100, 200)
        assert similarity < 0.9

    def test_very_different_lengths(self):
        """Very different lengths should return low similarity."""
        similarity = _length_similarity(100, 1000)
        assert similarity < 0.5


class TestLoadCorpus:
    """Tests for _load_corpus function."""

    def test_load_from_file(self, tmp_path):
        """_load_corpus should load samples from a JSONL file."""
        corpus_file = tmp_path / "corpus.jsonl"
        corpus_file.write_text(
            '{"text": "Hello", "source_type": "blog", "topic": "test"}\n'
            '{"text": "World", "source_type": "tweet", "topic": "test"}\n',
            encoding="utf-8",
        )
        samples = _load_corpus(str(corpus_file))
        assert len(samples) == 2
        assert samples[0].text == "Hello"
        assert samples[1].text == "World"

    def test_load_empty_file(self, tmp_path):
        """_load_corpus should return empty list for empty file."""
        corpus_file = tmp_path / "corpus.jsonl"
        corpus_file.write_text("", encoding="utf-8")
        samples = _load_corpus(str(corpus_file))
        assert len(samples) == 0

    def test_load_invalid_json(self, tmp_path):
        """_load_corpus should skip invalid JSON lines."""
        corpus_file = tmp_path / "corpus.jsonl"
        corpus_file.write_text(
            '{"text": "Hello"}\n'
            'invalid json\n'
            '{"text": "World"}\n',
            encoding="utf-8",
        )
        samples = _load_corpus(str(corpus_file))
        assert len(samples) == 2
        assert samples[0].text == "Hello"
        assert samples[1].text == "World"


class TestSelectFewShot:
    """Tests for select_few_shot function."""

    def test_select_few_shot(self, tmp_path):
        """select_few_shot should select relevant samples."""
        corpus_file = tmp_path / "corpus.jsonl"
        corpus_file.write_text(
            '{"text": "Success is about habits.", "source_type": "blog", "topic": "success habits"}\n'
            '{"text": "Management is hard.", "source_type": "blog", "topic": "management"}\n'
            '{"text": "Probability matters.", "source_type": "tweet", "topic": "probability"}\n',
            encoding="utf-8",
        )
        samples = select_few_shot(
            corpus_path=str(corpus_file),
            topic="success habits",
            content_type="blog",
            n=2,
        )
        assert len(samples) == 2
        assert samples[0].text == "Success is about habits."

    def test_select_few_shot_empty_corpus(self, tmp_path):
        """select_few_shot should return empty list for empty corpus."""
        corpus_file = tmp_path / "corpus.jsonl"
        corpus_file.write_text("", encoding="utf-8")
        samples = select_few_shot(
            corpus_path=str(corpus_file),
            topic="success habits",
            content_type="blog",
            n=2,
        )
        assert len(samples) == 0


class TestBuildPrompt:
    """Tests for build_prompt function."""

    def test_build_prompt(self):
        """build_prompt should create a valid prompt."""
        few_shot = [
            FewShotSample(text="Example 1", source_type="blog", topic="test"),
            FewShotSample(text="Example 2", source_type="blog", topic="test"),
        ]
        prompt = build_prompt(
            few_shot=few_shot,
            topic="success habits",
            content_type="blog",
            output_format="blog",
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "success habits" in prompt
        assert "blog" in prompt
        assert "100" in prompt

    def test_build_prompt_no_few_shot(self):
        """build_prompt should work with no few-shot examples."""
        prompt = build_prompt(
            few_shot=[],
            topic="success habits",
            content_type="blog",
            output_format="blog",
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestCallLLM:
    """Tests for call_llm function."""

    @patch("sacbot.generator.OpenAI")
    def test_call_llm(self, mock_openai_class):
        """call_llm should call the LLM and return result."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test content"))]
        mock_response.usage = MagicMock(prompt_tokens=10, total_tokens=20)
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = call_llm("Test prompt")
        assert result.content == "Test content"
        assert result.tokens_used == 20
        assert result.prompt_tokens == 10
        mock_client.chat.completions.create.assert_called_once()

    @patch("sacbot.generator.OpenAI")
    def test_call_llm_error(self, mock_openai_class):
        """call_llm should handle errors gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        result = call_llm("Test prompt")
        assert result.content is None
        assert result.error == "API Error"


class TestGenerate:
    """Tests for generate function."""

    @patch("sacbot.generator.select_few_shot")
    @patch("sacbot.generator.build_prompt")
    @patch("sacbot.generator.call_llm")
    def test_generate(self, mock_call_llm, mock_build_prompt, mock_select_few_shot):
        """generate should orchestrate the generation process."""
        mock_select_few_shot.return_value = [
            FewShotSample(text="Example", source_type="blog", topic="test")
        ]
        mock_build_prompt.return_value = "Test prompt"
        mock_call_llm.return_value = GenerationResult(
            content="Test content",
            model="gpt-4o",
            tokens_used=100,
            latency_seconds=1.5,
            prompt_tokens=50,
            few_shot_count=1,
            content_type="blog",
            topic="test",
        )

        result = generate(
            topic="success habits",
            content_type="blog",
            corpus_path="corpus.jsonl",
        )
        assert result.content == "Test content"
        assert result.model == "gpt-4o"
        assert result.tokens_used == 100
        assert result.latency_seconds == 1.5
        assert result.prompt_tokens == 50
        assert result.few_shot_count == 1
        assert result.content_type == "blog"
        assert result.topic == "success habits"

    @patch("sacbot.generator.select_few_shot")
    @patch("sacbot.generator.build_prompt")
    @patch("sacbot.generator.call_llm")
    def test_generate_error(self, mock_call_llm, mock_build_prompt, mock_select_few_shot):
        """generate should handle errors gracefully."""
        mock_select_few_shot.return_value = []
        mock_build_prompt.return_value = "Test prompt"
        mock_call_llm.return_value = GenerationResult(
            content=None,
            model="gpt-4o",
            tokens_used=0,
            latency_seconds=0,
            prompt_tokens=0,
            few_shot_count=0,
            content_type="blog",
            topic="test",
            error="API Error",
        )

        result = generate(
            topic="success habits",
            content_type="blog",
            corpus_path="corpus.jsonl",
        )
        assert result.content is None
        assert result.error == "API Error"
