"""Player Attribute Library — match football players by their attributes."""

__version__ = "1.0.0"

# Data model
from .models import PlayerAttribute

# Core functions
from .core import (
    create_player,
    get_attribute,
    get_all_attributes,
    match_players,
    save_players,
    load_players,
)

__all__ = [
    "PlayerAttribute",
    "create_player",
    "get_attribute",
    "get_all_attributes",
    "match_players",
    "save_players",
    "load_players",
]
