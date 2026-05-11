"""Player entity physics engine.

Provides the Player class as a rigid body with position, velocity,
acceleration, and configurable attributes. Supports deterministic
movement with configurable acceleration curves and directional change
penalties.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple


# Conversion constants
MPH_TO_YD_PER_S = 1.0 / 1.093613  # 1 mph ≈ 0.9144 m/s, 1 yd = 0.9144 m → 1 mph = 0.4572 m/s / 0.9144 = 0.5 yd/s... let me compute properly
# 1 mph = 1609.344 m / 3600 s = 0.44704 m/s
# 1 yd = 0.9144 m
# 1 mph = 0.44704 / 0.9144 yd/s = 0.488889 yd/s
MPH_TO_YD_PER_S = 0.488889


@dataclass
class Player:
    """Rigid body player entity with physics.

    Attributes:
        player_id: Unique identifier for the player.
        position: (x, y) position in yards.
        velocity: (vx, vy) velocity in yards/second.
        max_speed_yd_s: Maximum speed in yards/second.
        acceleration_rate: Acceleration rate in yards/second².
        agility: Agility factor (0.0-1.0). Lower agility means larger
                 directional change penalty. 1.0 = no penalty.
        strength: Player strength (used for collision mass).
        radius: Player collision radius in yards.
        name: Human-readable name.
        team: 'offense' or 'defense'.
        jersey_number: Jersey number.
        _current_speed: Current speed magnitude (computed).
    """

    player_id: str
    position: Tuple[float, float] = (0.0, 0.0)
    velocity: Tuple[float, float] = (0.0, 0.0)
    max_speed_yd_s: float = 0.0
    acceleration_rate: float = 0.0
    agility: float = 1.0
    strength: float = 1.0
    radius: float = 0.5  # yards
    name: str = "Player"
    team: str = "offense"
    jersey_number: int = 0

    # Internal state
    _current_speed: float = 0.0
    _heading_angle: float = 0.0  # radians, 0 = along +x axis

    def __post_init__(self):
        """Compute derived values after initialization."""
        self._current_speed = math.sqrt(
            self.velocity[0] ** 2 + self.velocity[1] ** 2
        )
        if self.velocity[0] != 0 or self.velocity[1] != 0:
            self._heading_angle = math.atan2(self.velocity[1], self.velocity[0])

    @classmethod
    def from_mph(cls, player_id: str, max_speed_mph: float, **kwargs) -> Player:
        """Create a player with max speed given in mph.

        Args:
            player_id: Unique identifier.
            max_speed_mph: Maximum speed in miles per hour.
            **kwargs: Additional Player attributes.

        Returns:
            A new Player instance.
        """
        max_speed_yd_s = max_speed_mph * MPH_TO_YD_PER_S
        return cls(max_speed_yd_s=max_speed_yd_s, player_id=player_id, **kwargs)

    @property
    def x(self) -> float:
        """X-coordinate."""
        return self.position[0]

    @property
    def y(self) -> float:
        """Y-coordinate."""
        return self.position[1]

    @property
    def vx(self) -> float:
        """X-velocity."""
        return self.velocity[0]

    @property
    def vy(self) -> float:
        """Y-velocity."""
        return self.velocity[1]

    @property
    def speed_yd_s(self) -> float:
        """Current speed in yards/second."""
        return self._current_speed

    @property
    def speed_mph(self) -> float:
        """Current speed in miles per hour."""
        return self._current_speed / MPH_TO_YD_PER_S

    @property
    def heading_angle(self) -> float:
        """Current heading angle in radians."""
        return self._heading_angle

    def set_position(self, x: float, y: float) -> None:
        """Set player position directly.

        Args:
            x: X-coordinate in yards.
            y: Y-coordinate in yards.
        """
        self.position = (x, y)

    def set_velocity(self, vx: float, vy: float) -> None:
        """Set player velocity directly.

        Args:
            vx: X-velocity in yards/second.
            vy: Y-velocity in yards/second.
        """
        self.velocity = (vx, vy)
        self._current_speed = math.sqrt(vx ** 2 + vy ** 2)
        if vx != 0 or vy != 0:
            self._heading_angle = math.atan2(vy, vx)

    def accelerate_toward(self, target_x: float, target_y: float, dt: float) -> None:
        """Accelerate toward a target position for a given time step.

        Uses a configurable acceleration curve to approach max speed.
        The acceleration is applied in the direction of the target.

        Args:
            target_x: Target X-coordinate.
            target_y: Target Y-coordinate.
            dt: Time step in seconds.
        """
        # Direction to target
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx ** 2 + dy ** 2)

        if dist < 0.001:
            return  # Already at target

        # Normalize direction
        dir_x = dx / dist
        dir_y = dy / dist

        # Calculate desired velocity (toward target, capped at max speed)
        desired_speed = min(self.max_speed_yd_s, self.acceleration_rate * dt)

        # Apply agility penalty for directional changes
        current_speed = self._current_speed
        if current_speed > 0.01:
            # Angle between current heading and desired direction
            cos_angle = (self.velocity[0] * dir_x + self.velocity[1] * dir_y) / current_speed
            cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp
            angle_diff = math.acos(cos_angle)
            # Agility reduces effective acceleration when turning
            turn_penalty = 1.0 - (1.0 - self.agility) * (angle_diff / math.pi)
            turn_penalty = max(0.1, turn_penalty)  # Minimum 10% effectiveness
        else:
            turn_penalty = 1.0

        effective_accel = self.acceleration_rate * turn_penalty * dt
        
        # New speed: can only increase up to desired_speed, but never decrease
        # If already going faster than desired, keep current speed but change direction
        new_speed = min(current_speed + effective_accel, desired_speed)
        # When turning sharply, the player loses speed proportional to the turn angle
        # and inversely proportional to agility
        if current_speed > 0.01 and angle_diff > math.pi / 4:
            # Sharp turn penalty: reduce speed based on turn angle and agility
            sharp_penalty = (angle_diff / math.pi) * (1.0 - self.agility) * 0.5
            new_speed = max(0.0, new_speed * (1.0 - sharp_penalty))

        # Update velocity
        new_vx = dir_x * new_speed
        new_vy = dir_y * new_speed

        self.velocity = (new_vx, new_vy)
        self._current_speed = new_speed
        self._heading_angle = math.atan2(new_vy, new_vx)

    def step(self, dt: float) -> None:
        """Advance player position by one time step.

        Position is updated based on current velocity. Velocity is not
        modified here (use accelerate_toward or apply_force for that).

        Args:
            dt: Time step in seconds.
        """
        new_x = self.x + self.vx * dt
        new_y = self.y + self.vy * dt
        self.position = (new_x, new_y)

    def apply_force(self, fx: float, fy: float, dt: float) -> None:
        """Apply a force to the player for a time step.

        Force is converted to acceleration using mass (strength).

        Args:
            fx: Force in X direction.
            fy: Force in Y direction.
            dt: Time step in seconds.
        """
        mass = max(1.0, self.strength)  # Mass proportional to strength
        ax = fx / mass
        ay = fy / mass

        new_vx = self.vx + ax * dt
        new_vy = self.vy + ay * dt

        self.velocity = (new_vx, new_vy)
        self._current_speed = math.sqrt(new_vx ** 2 + new_vy ** 2)
        if new_vx != 0 or new_vy != 0:
            self._heading_angle = math.atan2(new_vy, new_vx)

    def stop(self) -> None:
        """Stop the player (set velocity to zero)."""
        self.velocity = (0.0, 0.0)
        self._current_speed = 0.0

    def distance_to(self, other: Player) -> float:
        """Distance to another player.

        Args:
            other: Another Player instance.

        Returns:
            Distance in yards.
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def is_colliding_with(self, other: Player) -> bool:
        """Check if this player is colliding with another.

        Args:
            other: Another Player instance.

        Returns:
            True if players are within combined radii.
        """
        return self.distance_to(other) <= (self.radius + other.radius)

    def to_dict(self) -> dict:
        """Serialize player state to dictionary.

        Returns:
            Dictionary with player state.
        """
        return {
            "player_id": self.player_id,
            "position": list(self.position),
            "velocity": list(self.velocity),
            "speed_yd_s": self._current_speed,
            "speed_mph": self.speed_mph,
            "heading_angle": self._heading_angle,
            "max_speed_yd_s": self.max_speed_yd_s,
            "acceleration_rate": self.acceleration_rate,
            "agility": self.agility,
            "strength": self.strength,
            "radius": self.radius,
            "name": self.name,
            "team": self.team,
            "jersey_number": self.jersey_number,
        }

    def __repr__(self) -> str:
        return (f"Player(id={self.player_id}, pos=({self.x:.1f},{self.y:.1f}), "
                f"vel=({self.vx:.2f},{self.vy:.2f}), "
                f"speed={self.speed_mph:.1f}mph, name={self.name})")


@dataclass
class Formation:
    """A formation of 22 players (11 offense, 11 defense).

    Attributes:
        name: Formation name.
        offensive_players: List of 11 offensive Player instances.
        defensive_players: List of 11 defensive Player instances.
        line_of_scrimmage_x: X-coordinate of the line of scrimmage.
    """

    name: str
    offensive_players: list[Player] = field(default_factory=list)
    defensive_players: list[Player] = field(default_factory=list)
    line_of_scrimmage_x: float = 0.0

    @property
    def total_players(self) -> int:
        """Total number of players in the formation."""
        return len(self.offensive_players) + len(self.defensive_players)

    @property
    def is_complete(self) -> bool:
        """Check if formation has exactly 11 offensive and 11 defensive players."""
        return (len(self.offensive_players) == 11 and
                len(self.defensive_players) == 11)

    def add_offensive_player(self, player: Player) -> None:
        """Add a player to the offensive side.

        Args:
            player: Player instance (team should be 'offense').
        """
        player.team = "offense"
        self.offensive_players.append(player)

    def add_defensive_player(self, player: Player) -> None:
        """Add a player to the defensive side.

        Args:
            player: Player instance (team should be 'defense').
        """
        player.team = "defense"
        self.defensive_players.append(player)

    def get_players_by_team(self, team: str) -> list[Player]:
        """Get all players of a given team.

        Args:
            team: 'offense' or 'defense'.

        Returns:
            List of Player instances.
        """
        if team == "offense":
            return self.offensive_players
        elif team == "defense":
            return self.defensive_players
        else:
            raise ValueError(f"Unknown team: {team}")

    def step_all(self, dt: float) -> None:
        """Step all players in the formation.

        Args:
            dt: Time step in seconds.
        """
        for player in self.offensive_players + self.defensive_players:
            player.step(dt)

    def to_dict(self) -> dict:
        """Serialize formation state to dictionary.

        Returns:
            Dictionary with formation state.
        """
        return {
            "name": self.name,
            "line_of_scrimmage_x": self.line_of_scrimmage_x,
            "offensive_players": [p.to_dict() for p in self.offensive_players],
            "defensive_players": [p.to_dict() for p in self.defensive_players],
        }

    def __repr__(self) -> str:
        return (f"Formation(name={self.name}, "
                f"off={len(self.offensive_players)}, "
                f"def={len(self.defensive_players)}, "
                f"LOS={self.line_of_scrimmage_x:.1f})")
