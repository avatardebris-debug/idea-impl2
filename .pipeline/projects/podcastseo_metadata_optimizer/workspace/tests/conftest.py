"""Shared fixtures for PodcastSEO tests."""

from pathlib import Path
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def srt_file():
    return str(FIXTURES_DIR / "sample_tech.srt")


@pytest.fixture
def vtt_file():
    return str(FIXTURES_DIR / "sample_health.vtt")


@pytest.fixture
def txt_file():
    return str(FIXTURES_DIR / "sample_business.txt")


@pytest.fixture
def large_srt_file():
    return str(FIXTURES_DIR / "large_tech.srt")


@pytest.fixture
def empty_file(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("")
    return str(f)


@pytest.fixture
def single_word_file(tmp_path):
    f = tmp_path / "single.txt"
    f.write_text("machine learning")
    return str(f)
