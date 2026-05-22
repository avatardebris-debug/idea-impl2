"""Core library functions: create records, query attributes, and match profiles."""

import json
import math
from typing import Iterable, List, Literal, Optional

from .models import DEFAULT_ATTRIBUTES, PlayerAttribute

__all__ = [
    "create_player",
    "get_attribute",
    "get_all_attributes",
    "euclidean_distance",
    "cosine_similarity",
    "match_players",
    "save_players",
    "load_players",
]


# ------------------------------------------------------------------
# Record helpers
# ------------------------------------------------------------------

def create_player(name: str, **attrs: float) -> PlayerAttribute:
    """Create a new PlayerAttribute record.

    Parameters
    ----------
    name : str
        Player name.
    **attrs : float
        Optional attribute overrides (e.g. speed=80, shooting=90).

    Returns
    -----
    PlayerAttribute
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Player name must be a non-empty string.")
    for attr_name, value in attrs.items():
        if attr_name not in DEFAULT_ATTRIBUTES:
            raise ValueError(
                f"Unknown attribute '{attr_name}'. "
                f"Valid: {list(DEFAULT_ATTRIBUTES)}"
            )
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"Attribute '{attr_name}' must be a number, got {type(value).__name__}"
            )
    return PlayerAttribute(name=name, **attrs)


def get_attribute(player: PlayerAttribute, attr_name: str) -> float:
    """Retrieve a single attribute value from a player record."""
    if not isinstance(player, PlayerAttribute):
        raise TypeError("player must be a PlayerAttribute instance")
    return player.get(attr_name)


def get_all_attributes(player: PlayerAttribute) -> dict:
    """Return a dict of all attribute values for a player."""
    if not isinstance(player, PlayerAttribute):
        raise TypeError("player must be a PlayerAttribute instance")
    return player.to_dict()


# ------------------------------------------------------------------
# Matching helpers
# ------------------------------------------------------------------

def euclidean_distance(a: PlayerAttribute, b: PlayerAttribute) -> float:
    """Compute the Euclidean distance between two player profiles."""
    if not isinstance(a, PlayerAttribute):
        raise TypeError("a must be a PlayerAttribute instance")
    if not isinstance(b, PlayerAttribute):
        raise TypeError("b must be a PlayerAttribute instance")
    sum_sq = 0.0
    for attr in DEFAULT_ATTRIBUTES:
        diff = a.get(attr) - b.get(attr)
        sum_sq += diff * diff
    return math.sqrt(sum_sq)


def cosine_similarity(a: PlayerAttribute, b: PlayerAttribute) -> float:
    """Compute cosine similarity between two player profiles (0–1)."""
    if not isinstance(a, PlayerAttribute):
        raise TypeError("a must be a PlayerAttribute instance")
    if not isinstance(b, PlayerAttribute):
        raise TypeError("b must be a PlayerAttribute instance")
    dot = 0.0
    mag_a = 0.0
    mag_b = 0.0
    for attr in DEFAULT_ATTRIBUTES:
        va = a.get(attr)
        vb = b.get(attr)
        dot += va * vb
        mag_a += va * va
        mag_b += vb * vb
    denom = math.sqrt(mag_a) * math.sqrt(mag_b)
    if denom == 0:
        return 0.0
    return dot / denom


def match_players(
    target: PlayerAttribute,
    candidates: Iterable[PlayerAttribute],
    *,
    metric: Literal["cosine", "euclidean"] = "cosine",
    top_n: Optional[int] = None,
) -> List[dict]:
    """Match a target player profile against a list of candidates.

    Parameters
    ----------
    target : PlayerAttribute
        The reference profile to match against.
    candidates : Iterable[PlayerAttribute]
        Player profiles to compare.
    metric : str
        Distance metric: ``"cosine"`` (higher is better) or
        ``"euclidean"`` (lower is better).
    top_n : int or None
        If given, return only the top *n* matches.

    Returns
    -----
    list[dict]
        Each entry is ``{"player": PlayerAttribute, "score": float}``
        sorted by best match first.
    """
    if not isinstance(target, PlayerAttribute):
        raise TypeError("target must be a PlayerAttribute instance")
    if metric not in ("cosine", "euclidean"):
        raise ValueError(f"Unknown metric: {metric!r}. Valid: ['cosine', 'euclidean']")
    if top_n is not None and (not isinstance(top_n, int) or top_n < 1):
        raise ValueError("top_n must be a positive integer")

    scores = []
    for c in candidates:
        if not isinstance(c, PlayerAttribute):
            raise TypeError("Each candidate must be a PlayerAttribute instance")
        if metric == "cosine":
            score = cosine_similarity(target, c)
        elif metric == "euclidean":
            # Invert so higher is better (max possible distance ≈ 100*sqrt(6) ≈ 245)
            dist = euclidean_distance(target, c)
            score = 1.0 - (dist / 245.0)
        else:
            raise ValueError(f"Unknown metric: {metric!r}")
        scores.append({"player": c, "score": round(score, 4)})

    # Sort descending by score
    scores.sort(key=lambda x: x["score"], reverse=True)

    if top_n is not None:
        scores = scores[:top_n]

    return scores


def save_players(players: List[PlayerAttribute], filepath: str) -> None:
    """Save a list of players to a JSON file.

    Parameters
    ----------
    players : list[PlayerAttribute]
        Players to serialize.
    filepath : str
        Destination file path.
    """
    data = [p.to_json() for p in players]
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def load_players(filepath: str) -> List[PlayerAttribute]:
    """Load a list of players from a JSON file.

    Parameters
    ----------
    filepath : str
        Source file path.

    Returns
    -----
    list[PlayerAttribute]
    """
    with open(filepath, "r") as f:
        data = json.load(f)
    return [PlayerAttribute.from_json(entry) for entry in data]
