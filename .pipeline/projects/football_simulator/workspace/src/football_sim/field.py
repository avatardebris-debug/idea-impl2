"""Field geometry module for the football simulator.

Provides the Field class with regulation-size geometry for NFL, College,
and High School fields, including yard-line markings, hash marks, and
endzone boundaries.
"""

from __future__ import annotations

from typing import List, Tuple, Optional
from dataclasses import dataclass
from .config import Config


@dataclass(frozen=True)
class YardLine:
    """Represents a yard-line marking on the field.

    Attributes:
        yard: Yard line number (0-100 within field of play).
        x: X-coordinate of the yard line in yards from the home goal line.
    """
    yard: int
    x: float


@dataclass(frozen=True)
class HashMark:
    """Represents a hash mark on the field.

    Attributes:
        yard: Yard line number where the hash mark is located.
        x: X-coordinate of the hash mark.
        y_offset: Offset from field center (positive = right, negative = left).
    """
    yard: int
    x: float
    y_offset: float


@dataclass(frozen=True)
class Endzone:
    """Represents an endzone on the field.

    Attributes:
        depth: Depth of the endzone in yards.
        start: Start position (x) of the endzone.
        end: End position (x) of the endzone.
        team: 'home' or 'away' indicating which endzone.
    """
    depth: float
    start: float
    end: float
    team: str


class Field:
    """Regulation football field with geometry and markings.

    Supports NFL (120yd total), College (120yd total), and High School (110yd total)
    field configurations. Uses a coordinate system where x=0 is the home team's
    goal line and x increases toward the opponent's endzone.

    Coordinate system:
        - x-axis: yards from home goal line (0 to field_length_yards)
        - y-axis: yards from left sideline (0 to field_width_yards)
        - Field center is at (field_of_play_yards/2, field_width_yards/2)
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize the field.

        Args:
            config: Field configuration. If None, defaults to NFL config.
        """
        self._config = config or Config(field_type="nfl")
        self._yard_lines: List[YardLine] = []
        self._hash_marks: List[HashMark] = []
        self._endzones: List[Endzone] = []
        self._build_field()

    def _build_field(self) -> None:
        """Build all field geometry elements."""
        self._build_yard_lines()
        self._build_hash_marks()
        self._build_endzones()

    def _build_yard_lines(self) -> None:
        """Build yard-line markings for the field of play."""
        self._yard_lines = []
        for yard in range(0, int(self._config.field_of_play_yards) + 1):
            x = float(yard)
            self._yard_lines.append(YardLine(yard=yard, x=x))

    def _build_hash_marks(self) -> None:
        """Build hash mark positions."""
        self._hash_marks = []
        spacing = self._config.hash_mark_spacing_yards
        half_width = self._config.field_width_yards / 2.0

        for yard in range(0, int(self._config.field_of_play_yards) + 1):
            if yard % spacing == 0:
                x = float(yard)
                # Hash marks are typically 1 yard from the center on each side
                # For NFL/College: 70'6" from each sideline = 1.333 yards from center
                # For HS: varies but we use configurable width
                offset = self._config.hash_mark_width
                self._hash_marks.append(HashMark(
                    yard=yard,
                    x=x,
                    y_offset=-offset
                ))
                self._hash_marks.append(HashMark(
                    yard=yard,
                    x=x,
                    y_offset=offset
                ))

    def _build_endzones(self) -> None:
        """Build endzone definitions."""
        field_length = self._config.field_length_yards
        endzone_depth = self._config.endzone_depth_yards
        field_of_play = self._config.field_of_play_yards

        # Home endzone: x=0 to x=endzone_depth
        self._endzones.append(Endzone(
            depth=endzone_depth,
            start=0.0,
            end=endzone_depth,
            team="home"
        ))

        # Away endzone: x=field_length - endzone_depth to x=field_length
        self._endzones.append(Endzone(
            depth=endzone_depth,
            start=field_length - endzone_depth,
            end=field_length,
            team="away"
        ))

    # --- Properties ---

    @property
    def config(self) -> Config:
        """Get the field configuration."""
        return self._config

    @property
    def length_yards(self) -> float:
        """Total field length in yards (including endzones)."""
        return self._config.field_length_yards

    @property
    def width_yards(self) -> float:
        """Field width in yards."""
        return self._config.field_width_yards

    @property
    def field_of_play_yards(self) -> float:
        """Field of play length (excluding endzones) in yards."""
        return self._config.field_of_play_yards

    @property
    def endzone_depth_yards(self) -> float:
        """Endzone depth in yards."""
        return self._config.endzone_depth_yards

    @property
    def home_goal_line_x(self) -> float:
        """X-coordinate of the home team's goal line."""
        return 0.0

    @property
    def away_goal_line_x(self) -> float:
        """X-coordinate of the away team's goal line."""
        return self._config.field_of_play_yards

    @property
    def home_endzone(self) -> Endzone:
        """Get the home team's endzone."""
        return self._endzones[0]

    @property
    def away_endzone(self) -> Endzone:
        """Get the away team's endzone."""
        return self._endzones[1]

    @property
    def yard_lines(self) -> List[YardLine]:
        """Get all yard-line markings."""
        return list(self._yard_lines)

    @property
    def hash_marks(self) -> List[HashMark]:
        """Get all hash marks."""
        return list(self._hash_marks)

    @property
    def endzones(self) -> List[Endzone]:
        """Get all endzones."""
        return list(self._endzones)

    # --- Coordinate helpers ---

    def is_in_field_of_play(self, x: float) -> bool:
        """Check if an x-coordinate is within the field of play.

        Args:
            x: X-coordinate in yards.

        Returns:
            True if x is within the field of play (0 to 100).
        """
        return 0.0 <= x <= self._config.field_of_play_yards

    def is_in_endzone(self, x: float) -> Optional[str]:
        """Check if an x-coordinate is in an endzone.

        Args:
            x: X-coordinate in yards.

        Returns:
            'home' if in home endzone, 'away' if in away endzone, None if not in endzone.
        """
        if self.home_endzone.start <= x <= self.home_endzone.end:
            return "home"
        if self.away_endzone.start <= x <= self.away_endzone.end:
            return "away"
        return None

    def is_in_bounds(self, x: float, y: float) -> bool:
        """Check if a position is within the field boundaries.

        Args:
            x: X-coordinate in yards.
            y: Y-coordinate in yards.

        Returns:
            True if position is within field boundaries.
        """
        return (0.0 <= x <= self.length_yards and
                0.0 <= y <= self.width_yards)

    def yards_to_line(self, x: float) -> int:
        """Convert an x-coordinate to the nearest yard line number.

        For the field of play, returns the yard line number (0-100).
        For endzones, returns the distance from the nearest goal line.

        Args:
            x: X-coordinate in yards.

        Returns:
            Yard line number.
        """
        if x < 0:
            return 0
        if x > self._config.field_of_play_yards:
            return 100
        return int(round(x))

    def get_yard_line_at(self, x: float) -> Optional[YardLine]:
        """Get the yard line at a given x-coordinate.

        Args:
            x: X-coordinate in yards.

        Returns:
            YardLine object or None if not in field of play.
        """
        for yl in self._yard_lines:
            if abs(yl.x - x) < 0.01:
                return yl
        return None

    def get_hash_marks_at_yard(self, yard: int) -> List[HashMark]:
        """Get hash marks at a specific yard line.

        Args:
            yard: Yard line number (0-100).

        Returns:
            List of hash marks at that yard line.
        """
        return [hm for hm in self._hash_marks if hm.yard == yard]

    def get_line_of_scrimmage_yard(self, x: float) -> int:
        """Get the line of scrimmage as a yard line number.

        Args:
            x: X-coordinate of the line of scrimmage.

        Returns:
            Yard line number (1-100, where 1 is own 1-yard line).
        """
        if x <= 0:
            return 1
        if x >= self._config.field_of_play_yards:
            return 100
        return max(1, min(100, int(round(x))))

    def get_field_position_string(self, x: float) -> str:
        """Convert an x-coordinate to a human-readable field position string.

        Args:
            x: X-coordinate in yards.

        Returns:
            String like "Own 25", "Opp 10", "Endzone", etc.
        """
        if x <= 0:
            return "Own Goal Line"
        if x >= self._config.field_of_play_yards:
            return "Opp Goal Line"
        if x <= 50:
            return f"Own {int(round(x))}"
        else:
            return f"Opp {int(round(self._config.field_of_play_yards - x))}"

    def __repr__(self) -> str:
        return (f"Field(type={self._config.field_type}, "
                f"length={self.length_yards}yd, "
                f"width={self.width_yards}yd, "
                f"endzones={self.endzone_depth_yards}yd)")
