"""Tests for keyword_extractor.py."""

import pytest
from podcastseo.keyword_extractor import KeywordExtractor
from podcastseo.transcript_parser import TranscriptParser


class TestKeywordExtractorExtract:
    """Tests for keyword extraction."""

    def test_extract_returns_list(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        extractor = KeywordExtractor(top_n=10)
        keywords = extractor.extract(result["text"], top_n=10)
        assert isinstance(keywords, list)

    def test_extract_returns_dicts(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        extractor = KeywordExtractor(top_n=10)
        keywords = extractor.extract(result["text"], top_n=10)
        assert all(isinstance(k, dict) for k in keywords)

    def test_extract_has_required_keys(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        extractor = KeywordExtractor(top_n=10)
        keywords = extractor.extract(result["text"], top_n=10)
        for kw in keywords:
            assert "keyword" in kw
            assert "score" in kw
            assert "category" in kw
            assert "occurrences" in kw

    def test_extract_respects_top_n(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        extractor = KeywordExtractor(top_n=5)
        keywords = extractor.extract(result["text"], top_n=5)
        assert len(keywords) == 5

    def test_extract_sorted_by_score(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        extractor = KeywordExtractor(top_n=10)
        keywords = extractor.extract(result["text"], top_n=10)
        scores = [k["score"] for k in keywords]
        assert scores == sorted(scores, reverse=True)

    def test_extract_no_duplicates(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        extractor = KeywordExtractor(top_n=20)
        keywords = extractor.extract(result["text"], top_n=20)
        keywords_list = [k["keyword"] for k in keywords]
        assert len(keywords_list) == len(set(keywords_list))

    def test_extract_categories_assigned(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        extractor = KeywordExtractor(top_n=10)
        keywords = extractor.extract(result["text"], top_n=10)
        categories = {k["category"] for k in keywords}
        assert len(categories) > 0

    def test_extract_empty_text(self):
        extractor = KeywordExtractor(top_n=10)
        keywords = extractor.extract("", top_n=10)
        assert keywords == []

    def test_extract_single_word(self, single_word_file):
        parser = TranscriptParser()
        result = parser.parse_raw(single_word_file)
        extractor = KeywordExtractor(top_n=5)
        keywords = extractor.extract(result["text"], top_n=5)
        assert len(keywords) == 1
        assert keywords[0]["keyword"] == "machine"

    def test_extract_scores_are_floats(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        extractor = KeywordExtractor(top_n=10)
        keywords = extractor.extract(result["text"], top_n=10)
        assert all(isinstance(k["score"], float) for k in keywords)

    def test_extract_occurrences_are_ints(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        extractor = KeywordExtractor(top_n=10)
        keywords = extractor.extract(result["text"], top_n=10)
        assert all(isinstance(k["occurrences"], int) for k in keywords)

    def test_extract_rounded_scores(self, srt_file):
        parser = TranscriptParser()
        result = parser.parse_raw(srt_file)
        extractor = KeywordExtractor(top_n=10)
        keywords = extractor.extract(result["text"], top_n=10)
        for kw in keywords:
            assert len(str(kw["score"]).split(".")[-1]) <= 4


class TestKeywordExtractorStopWords:
    """Tests for stop word handling."""

    def test_stop_words_excluded(self):
        extractor = KeywordExtractor(top_n=10)
        text = "the and is a of in to for on with at by from this that"
        keywords = extractor.extract(text, top_n=10)
        for kw in keywords:
            assert kw["keyword"] not in extractor.stop_words


class TestKeywordExtractorCategories:
    """Tests for category assignment."""

    def test_technical_keywords(self):
        extractor = KeywordExtractor(top_n=10)
        text = "machine learning neural networks deep learning artificial intelligence"
        keywords = extractor.extract(text, top_n=10)
        tech_keywords = [k for k in keywords if k["category"] == "technical"]
        assert len(tech_keywords) > 0

    def test_health_keywords(self):
        extractor = KeywordExtractor(top_n=10)
        text = "nutrition gut health probiotics prebiotics inflammation diet"
        keywords = extractor.extract(text, top_n=10)
        health_keywords = [k for k in keywords if k["category"] == "health"]
        assert len(health_keywords) > 0

    def test_business_keywords(self):
        extractor = KeywordExtractor(top_n=10)
        text = "remote work hybrid business strategy leadership innovation"
        keywords = extractor.extract(text, top_n=10)
        business_keywords = [k for k in keywords if k["category"] == "business"]
        assert len(business_keywords) > 0

    def test_general_keywords(self):
        extractor = KeywordExtractor(top_n=10)
        text = "hello world test example sample demo"
        keywords = extractor.extract(text, top_n=10)
        general_keywords = [k for k in keywords if k["category"] == "general"]
        assert len(general_keywords) > 0


class TestKeywordExtractorPerformance:
    """Performance tests."""

    def test_large_file_performance(self, large_srt_file):
        import time
        parser = TranscriptParser()
        result = parser.parse_raw(large_srt_file)
        extractor = KeywordExtractor(top_n=20)
        start = time.time()
        keywords = extractor.extract(result["text"], top_n=20)
        elapsed = time.time() - start
        assert elapsed < 30  # Should complete in under 30 seconds
        assert len(keywords) == 20
