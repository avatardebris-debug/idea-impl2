"""Formation definitions for the football simulator.

Provides pre-defined formations (I-Formation, Shotgun, Wildcat, etc.)
that place 11 offensive and 11 defensive players at standard positions.
"""

from __future__ import annotations

from typing import List, Tuple
from .entities import Player, Formation


# Standard player positions (relative to line of scrimmage)
# Format: (name, jersey, max_speed_mph, agility, strength, offset_x, offset_y)

OFFENSIVE_POSITIONS = {
    "LT": (72, 5.0, 0.6, 1.5, -2.5, 0.0),
    "LG": (65, 4.5, 0.5, 1.8, -1.0, 0.0),
    "C": (52, 4.0, 0.5, 2.0, 0.0, 0.0),
    "RG": (66, 4.5, 0.5, 1.8, 1.0, 0.0),
    "RT": (78, 5.0, 0.6, 1.5, 2.5, 0.0),
    "WR1": (10, 10.0, 0.95, 0.8, -3.0, 15.0),
    "WR2": (15, 9.5, 0.9, 0.75, 3.0, -15.0),
    "TE": (85, 7.0, 0.7, 1.2, 4.0, 3.0),
    "FB": (40, 6.0, 0.6, 1.5, 1.0, 4.0),
    "RB": (28, 8.5, 0.85, 1.0, 0.0, 5.0),
    "QB": (12, 7.0, 0.7, 0.9, 0.0, 7.0),
}

DEFENSIVE_POSITIONS = {
    "DE1": (97, 7.0, 0.8, 1.5, -3.5, 0.0),
    "DE2": (94, 7.0, 0.8, 1.5, 3.5, 0.0),
    "DT1": (99, 8.0, 0.6, 2.0, -1.0, 0.0),
    "DT2": (98, 8.0, 0.6, 2.0, 1.0, 0.0),
    "LB1": (55, 6.5, 0.75, 1.5, -2.0, 5.0),
    "LB2": (54, 6.5, 0.75, 1.5, 2.0, 5.0),
    "LB3": (50, 6.0, 0.7, 1.3, 0.0, 8.0),
    "CB1": (2, 9.0, 0.95, 0.9, -3.0, 2.0),
    "CB2": (24, 9.0, 0.95, 0.9, 3.0, 2.0),
    "FS": (30, 7.5, 0.85, 0.8, 0.0, 12.0),
    "SS": (21, 7.0, 0.8, 1.0, 0.0, 9.0),
}


def create_offensive_player(
    name: str,
    jersey: int,
    max_speed_mph: float,
    agility: float,
    strength: float,
    offset_x: float,
    offset_y: float,
    line_of_scrimmage_x: float,
) -> Player:
    """Create an offensive player at a given offset from the LOS.

    Args:
        name: Player name.
        jersey: Jersey number.
        max_speed_mph: Max speed in mph.
        agility: Agility factor.
        strength: Strength factor.
        offset_x: X offset from LOS.
        offset_y: Y offset from LOS.
        line_of_scrimmage_x: X-coordinate of the LOS.

    Returns:
        A Player instance.
    """
    x = line_of_scrimmage_x + offset_x
    y = 26.665 + offset_y  # Center of field is y=26.665
    return Player(
        player_id=f"off_{name}_{jersey}",
        position=(x, y),
        max_speed_yd_s=max_speed_mph * 0.488889,
        acceleration_rate=3.0,
        agility=agility,
        strength=strength,
        radius=0.5,
        name=name,
        team="offense",
        jersey_number=jersey,
    )


def create_defensive_player(
    name: str,
    jersey: int,
    max_speed_mph: float,
    agility: float,
    strength: float,
    offset_x: float,
    offset_y: float,
    line_of_scrimmage_x: float,
) -> Player:
    """Create a defensive player at a given offset from the LOS.

    Args:
        name: Player name.
        jersey: Jersey number.
        max_speed_mph: Max speed in mph.
        agility: Agility factor.
        strength: Strength factor.
        offset_x: X offset from LOS.
        offset_y: Y offset from LOS.
        line_of_scrimmage_x: X-coordinate of the LOS.

    Returns:
        A Player instance.
    """
    x = line_of_scrimmage_x + offset_x
    y = 26.665 + offset_y
    return Player(
        player_id=f"def_{name}_{jersey}",
        position=(x, y),
        max_speed_yd_s=max_speed_mph * 0.488889,
        acceleration_rate=3.0,
        agility=agility,
        strength=strength,
        radius=0.5,
        name=name,
        team="defense",
        jersey_number=jersey,
    )


def create_formation(
    formation_name: str = "i_formation",
    line_of_scrimmage_x: float = 20.0,
) -> Formation:
    """Create a standard formation with 11 offensive and 11 defensive players.

    Args:
        formation_name: Name of the formation (currently only "i_formation" supported).
        line_of_scrimmage_x: X-coordinate of the line of scrimmage.

    Returns:
        A Formation instance with 22 players.
    """
    formation = Formation(
        name=formation_name,
        line_of_scrimmage_x=line_of_scrimmage_x,
    )

    # Create offensive players
    for pos_name, (jersey, speed, agi, str_, ox, oy) in OFFENSIVE_POSITIONS.items():
        player = create_offensive_player(
            name=pos_name,
            jersey=jersey,
            max_speed_mph=speed,
            agility=agi,
            strength=str_,
            offset_x=ox,
            offset_y=oy,
            line_of_scrimmage_x=line_of_scrimmage_x,
        )
        formation.add_offensive_player(player)

    # Create defensive players
    for pos_name, (jersey, speed, agi, str_, ox, oy) in DEFENSIVE_POSITIONS.items():
        player = create_defensive_player(
            name=pos_name,
            jersey=jersey,
            max_speed_mph=speed,
            agility=agi,
            strength=str_,
            offset_x=ox,
            offset_y=oy,
            line_of_scrimmage_x=line_of_scrimmage_x,
        )
        formation.add_defensive_player(player)

    return formation


def get_available_formations() -> List[str]:
    """Get list of available formation names.

    Returns:
        List of formation name strings.
    """
    return ["i_formation"]


def create_formation_from_dict(data: dict) -> Formation:
    """Create a formation from a dictionary.

    Args:
        data: Dictionary with 'formation_name' and optional 'line_of_scrimmage_x'.

    Returns:
        A Formation instance.
    """
    formation_name = data.get("formation_name", "i_formation")
    los = data.get("line_of_scrimmage_x", 20.0)
    return create_formation(formation_name, los)
