"""Tests for video_ingestor.question_answering."""

import pytest
from unittest.mock import patch, MagicMock

from video_ingestor.question_answering import QuestionAnswerer, QandAError


class TestQuestionAnswerer:
    def test_answer_with_mocked_harness_and_store(self):
        """Test Q&A with mocked LLM harness and vector store."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "The answer is 42",
            "citations": [{"text": "Relevant chunk", "similarity": 0.9}],
            "confidence": 0.95,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = [
            {"text": "Relevant chunk", "similarity": 0.9, "start": 0.0, "end": 5.0}
        ]

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("What is the answer?", "test-job")

        assert result["answer"] == "The answer is 42"
        assert result["confidence"] == 0.95
        assert len(result["citations"]) == 1
        mock_harness.generate_json.assert_called_once()
        mock_store.search.assert_called_once()

    def test_answer_with_no_relevant_chunks(self):
        """Test Q&A when no relevant chunks are found."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "I don't know",
            "citations": [],
            "confidence": 0.1,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("Unknown question?", "test-job")

        assert result["answer"] == "I don't know"
        assert result["confidence"] == 0.1
        assert result["citations"] == []

    def test_answer_with_custom_top_k(self):
        """Test Q&A with custom top_k parameter."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Answer",
            "citations": [],
            "confidence": 0.5,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("Test?", "test-job", top_k=5)

        assert result["answer"] == "Answer"
        # Verify top_k was passed to search
        mock_store.search.assert_called_with("test-job", "Test?", top_k=5)

    def test_answer_with_custom_max_context_length(self):
        """Test Q&A with custom max_context_length parameter."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Answer",
            "citations": [],
            "confidence": 0.5,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("Test?", "test-job", max_context_length=2000)

        assert result["answer"] == "Answer"

    def test_answer_handles_harness_exception(self):
        """Test that Q&A handles LLM errors gracefully."""
        mock_harness = MagicMock()
        mock_harness.generate_json.side_effect = Exception("LLM error")

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)

        with pytest.raises(QandAError, match="Question answering failed"):
            qa.answer("Test?", "test-job")

    def test_answer_handles_store_exception(self):
        """Test that Q&A handles vector store errors gracefully."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Fallback answer",
            "citations": [],
            "confidence": 0.1,
        }

        mock_store = MagicMock()
        mock_store.search.side_effect = Exception("Store error")

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("Test?", "test-job")

        assert result["answer"] == "Fallback answer"
        assert result["confidence"] == 0.1

    def test_answer_with_high_confidence(self):
        """Test Q&A with high confidence answer."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Definitive answer",
            "citations": [{"text": "Evidence", "similarity": 0.95}],
            "confidence": 0.98,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = [{"text": "Evidence", "similarity": 0.95}]

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("Test?", "test-job")

        assert result["confidence"] == 0.98
        assert result["answer"] == "Definitive answer"

    def test_answer_with_low_confidence(self):
        """Test Q&A with low confidence answer."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Uncertain answer",
            "citations": [],
            "confidence": 0.2,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("Test?", "test-job")

        assert result["confidence"] == 0.2

    def test_answer_with_multiple_citations(self):
        """Test Q&A with multiple citations."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Multi-citation answer",
            "citations": [
                {"text": "Citation 1", "similarity": 0.9},
                {"text": "Citation 2", "similarity": 0.85},
            ],
            "confidence": 0.88,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = [
            {"text": "Citation 1", "similarity": 0.9},
            {"text": "Citation 2", "similarity": 0.85},
        ]

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("Test?", "test-job")

        assert len(result["citations"]) == 2
        assert result["citations"][0]["text"] == "Citation 1"
        assert result["citations"][1]["text"] == "Citation 2"

    def test_answer_with_missing_keys_in_response(self):
        """Test that Q&A handles missing keys in LLM response."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Answer only",
            # Missing citations and confidence
        }

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("Test?", "test-job")

        assert result["answer"] == "Answer only"
        assert result["citations"] == []
        assert result["confidence"] == 0.5  # Default confidence

    def test_answer_with_none_values_in_response(self):
        """Test that Q&A handles None values in LLM response."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": None,
            "citations": None,
            "confidence": None,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("Test?", "test-job")

        assert result["answer"] == "I don't have enough information to answer this question."
        assert result["citations"] == []
        assert result["confidence"] == 0.0

    def test_answer_with_empty_question(self):
        """Test Q&A with empty question."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Empty question answer",
            "citations": [],
            "confidence": 0.5,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("", "test-job")

        assert result["answer"] == "Empty question answer"

    def test_answer_with_special_characters_in_question(self):
        """Test Q&A with special characters in question."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Special chars answer",
            "citations": [],
            "confidence": 0.5,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("What's @#$%?", "test-job")

        assert result["answer"] == "Special chars answer"

    def test_answer_with_unicode_question(self):
        """Test Q&A with unicode in question."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Unicode answer",
            "citations": [],
            "confidence": 0.5,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer("こんにちは？", "test-job")

        assert result["answer"] == "Unicode answer"

    def test_answer_with_custom_system_prompt(self):
        """Test Q&A with custom system prompt."""
        mock_harness = MagicMock()
        mock_harness.generate_json.return_value = {
            "answer": "Custom prompt answer",
            "citations": [],
            "confidence": 0.5,
        }

        mock_store = MagicMock()
        mock_store.search.return_value = []

        qa = QuestionAnswerer(harness=mock_harness, vector_store=mock_store)
        result = qa.answer(
            "Test?",
            "test-job",
            system_prompt="You are a custom assistant"
        )

        assert result["answer"] == "Custom prompt answer"
