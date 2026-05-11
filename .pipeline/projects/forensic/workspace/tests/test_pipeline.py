"""Tests for forensic pipeline."""

import pytest
from forensic.pipeline import ForensicPipeline
from forensic.models import RiskLevel


class TestForensicPipeline:
    def test_init(self):
        pipeline = ForensicPipeline(db_path=":memory:")
        assert pipeline.db is not None
        assert pipeline.analyzer is not None

    def test_generate_report_no_filing(self):
        pipeline = ForensicPipeline(db_path=":memory:")
        with pytest.raises(ValueError):
            pipeline.generate_report("NONEXISTENT")

    def test_analyze_filing_no_filing(self):
        pipeline = ForensicPipeline(db_path=":memory:")
        with pytest.raises(ValueError):
            pipeline.analyze_filing("NONEXISTENT")
