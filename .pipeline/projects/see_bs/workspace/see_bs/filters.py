"""BS detection filters — Scott Adams techniques."""

from __future__ import annotations

from see_bs.models import NewsArticle

# ---------------------------------------------------------------------------
# Filter result type
# ---------------------------------------------------------------------------

FilterResult = dict  # {"score": float, "explanation": str}

# ---------------------------------------------------------------------------
# 1. Scott Alexander rule
# ---------------------------------------------------------------------------

def filter_scott_alexander_rule(article: NewsArticle) -> FilterResult:
    """Flag claims that would be embarrassing if the opposite were true.

    Heuristic: articles with very strong, unqualified language ("everyone knows",
    "obviously", "no one disputes") that could be embarrassing if reversed
    score higher for BS.
    """
    strong_words = [
        "everyone knows", "obviously", "no one disputes", "undoubtedly",
        "clearly", "evidently", "plainly", "absolutely", "certainly",
        "unquestionably", "beyond doubt", "it is obvious", "it is clear",
    ]
    content_lower = (article.title + " " + article.content).lower()
    matches = [w for w in strong_words if w in content_lower]
    if matches:
        score = min(100, 30 + 15 * len(matches))
        explanation = (
            f"Scott Alexander rule: found {len(matches)} strong/absolutist phrase(s) "
            f"({', '.join(matches[:3])}). If the opposite were true, the author "
            f"would look foolish — a BS signal."
        )
    else:
        score = 10
        explanation = (
            "Scott Alexander rule: no absolutist language detected. Low BS signal."
        )
    return {"score": score, "explanation": explanation}


# ---------------------------------------------------------------------------
# 2. Gellman Amnesia
# ---------------------------------------------------------------------------

def filter_gellman_amnesia(article: NewsArticle) -> FilterResult:
    """Simulate how the same story would read from the opposing viewpoint.

    If the framing is heavily one-sided (only one perspective quoted,
    opposing view absent), flag it.
    """
    # Heuristic: look for absence of opposing-view indicators
    opposing_indicators = [
        "critics say", "opponents argue", "however", "conversely",
        "on the other hand", "but critics", "yet others", "some argue",
        "others disagree", "counterargument", "dissenting", "opposition",
    ]
    content_lower = (article.title + " " + article.content).lower()
    opposing_matches = [w for w in opposing_indicators if w in content_lower]

    if len(opposing_matches) == 0:
        score = 70
        explanation = (
            "Gellman Amnesia: no opposing viewpoints found in the text. "
            "If the opposing side wrote this story, it would read very differently — "
            "a BS signal."
        )
    elif len(opposing_matches) <= 1:
        score = 45
        explanation = (
            f"Gellman Amnesia: only {len(opposing_matches)} opposing indicator(s) "
            f"found ({opposing_matches[0] if opposing_matches else 'none'}). "
            f"Likely one-sided framing."
        )
    else:
        score = 15
        explanation = (
            f"Gellman Amnesia: {len(opposing_matches)} opposing indicators found. "
            f"Reasonable balance of perspectives."
        )
    return {"score": score, "explanation": explanation}


# ---------------------------------------------------------------------------
# 3. Reporter identity analysis
# ---------------------------------------------------------------------------

def filter_reporter_identity(article: NewsArticle) -> FilterResult:
    """Weight credibility based on who is reporting (source outlet, author track record)."""
    score = 50  # neutral baseline
    parts: list[str] = []

    # Outlet bias
    bias = article.outlet_bias.lower()
    if bias == "center":
        score -= 10
        parts.append("center outlet (low bias)")
    elif bias in ("left", "right"):
        score += 15
        parts.append(f"{bias}-leaning outlet")
    elif bias == "extreme":
        score += 30
        parts.append("extreme outlet")
    else:
        score += 5
        parts.append("unknown outlet bias")

    # Author track record
    track = article.author_track_record.lower()
    if track == "reliable":
        score -= 15
        parts.append("reliable author")
    elif track == "mixed":
        score += 5
        parts.append("mixed author track record")
    elif track == "unreliable":
        score += 25
        parts.append("unreliable author")
    else:
        score += 5
        parts.append("unknown author track record")

    score = max(0, min(100, score))
    explanation = f"Reporter identity: {'; '.join(parts)}. BS score component: {score}."
    return {"score": score, "explanation": explanation}


# ---------------------------------------------------------------------------
# 4. Incentive alignment check
# ---------------------------------------------------------------------------

def filter_incentive_alignment(article: NewsArticle) -> FilterResult:
    """Flag stories where the reporter/outlet has a conflict of interest."""
    incentives = article.incentives or []
    if incentives:
        score = min(100, 20 + 15 * len(incentives))
        explanation = (
            f"Incentive alignment: {len(incentives)} potential conflict(s) detected "
            f"({', '.join(incentives[:3])}). Reporter may benefit from this narrative — "
            f"a BS signal."
        )
    else:
        score = 10
        explanation = (
            "Incentive alignment: no obvious conflicts of interest listed. "
            "Low BS signal from this filter."
        )
    return {"score": score, "explanation": explanation}


# ---------------------------------------------------------------------------
# Registry of all filters
# ---------------------------------------------------------------------------

ALL_FILTERS = [
    filter_scott_alexander_rule,
    filter_gellman_amnesia,
    filter_reporter_identity,
    filter_incentive_alignment,
]
