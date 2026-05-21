"""see_bs — News BS detection based on Scott Adams techniques.

Public API:
    from see_bs import filter_news
    result = filter_news(article)
"""

__version__ = "0.1.0"

from see_bs.engine import ScoreEngine, AnalysisResult  # noqa: F401
from see_bs.models import NewsArticle  # noqa: F401
from see_bs.filters import ALL_FILTERS  # noqa: F401


def filter_news(article: NewsArticle) -> AnalysisResult:
    """Top-level public API: analyze a news article for BS.

    Args:
        article: A :class:`NewsArticle` instance.

    Returns:
        An :class:`AnalysisResult` with BS score, per-filter breakdown, and summary.
    """
    return ScoreEngine.analyze(article)
