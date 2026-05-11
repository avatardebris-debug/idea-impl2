"""Ball physics engine for the football simulator.

Provides the Ball class with position, velocity, spin, gravity,
and air resistance. Supports pass trajectory calculation, catch
detection, and fumble detection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# Physics constants
GRAVITY = 32.174  # ft/s² → convert to yd/s²
GRAVITY_YD_S2 = GRAVITY / 3.0  # ~10.7247 yd/s²
AIR_RESISTANCE_COEFF = 0.02  # per frame (60 fps)
BALL_RADIUS = 0.15  # yards (football is ~11in long, ~6.5in diameter)
BALL_MASS = 0.91  # lbs (standard NFL football)


@dataclass
class CollisionEvent:
    """A collision event between entities."""
    timestamp: float
    entity_a: str
    entity_b: str
    pre_velocities: dict
    post_velocities: dict
    force: float

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "entity_a": self.entity_a,
            "entity_b": self.entity_b,
            "pre_velocities": self.pre_velocities,
            "post_velocities": self.post_velocities,
            "force": self.force,
        }


@dataclass
class Ball:
    """A football with physics properties.

    Attributes:
        ball_id: Unique identifier for the ball.
        position: (x, y) position in yards from field origin.
        velocity: (vx, vy) velocity in yd/s.
        spin: Spin rate in revolutions per second (RPS).
        gravity: Gravity constant in yd/s².
        air_resistance: Air resistance coefficient.
        radius: Ball radius in yards.
        mass: Ball mass in lbs.
        is_active: Whether the ball is in play.
        is_thrown: Whether the ball has been thrown.
        is_caught: Whether the ball has been caught.
        is_fumbled: Whether the ball has been fumbled.
        thrower_id: ID of the player who threw the ball.
        catcher_id: ID of the player who caught the ball.
        carrier_id: ID of the player currently carrying the ball.
        trajectory: List of (x, y, t) points along the trajectory.
        collision_events: List of collision events involving the ball.
    """
    ball_id: str = "ball_1"
    position: Tuple[float, float] = (0.0, 0.0)
    velocity: Tuple[float, float] = (0.0, 0.0)
    spin: float = 0.0
    gravity: float = GRAVITY_YD_S2
    air_resistance: float = AIR_RESISTANCE_COEFF
    radius: float = BALL_RADIUS
    mass: float = BALL_MASS
    is_active: bool = False
    is_thrown: bool = False
    is_caught: bool = False
    is_fumbled: bool = False
    thrower_id: Optional[str] = None
    catcher_id: Optional[str] = None
    carrier_id: Optional[str] = None
    trajectory: List[Tuple[float, float, float]] = field(default_factory=list)
    collision_events: List[CollisionEvent] = field(default_factory=list)

    @property
    def x(self) -> float:
        return self.position[0]

    @property
    def y(self) -> float:
        return self.position[1]

    @property
    def vx(self) -> float:
        return self.velocity[0]

    @property
    def vy(self) -> float:
        return self.velocity[1]

    @property
    def speed_yd_s(self) -> float:
        return math.sqrt(self.vx ** 2 + self.vy ** 2)

    @property
    def speed_mph(self) -> float:
        return self.speed_yd_s / 0.488889

    @property
    def is_in_play(self) -> bool:
        return self.is_active and not self.is_caught and not self.is_fumbled

    def throw(
        self,
        target_x: float,
        target_y: float,
        thrower_id: str,
        dt: float = 1.0 / 60.0,
    ) -> Ball:
        """Throw the ball toward a target position.

        Calculates a parabolic trajectory to reach the target.

        Args:
            target_x: Target x position in yards.
            target_y: Target y position in yards.
            thrower_id: ID of the player throwing the ball.
            dt: Time step in seconds.

        Returns:
            Self for chaining.
        """
        self.is_active = True
        self.is_thrown = True
        self.thrower_id = thrower_id
        self.is_caught = False
        self.is_fumbled = False
        self.catcher_id = None
        self.carrier_id = None
        self.trajectory = []

        dx = target_x - self.position[0]
        dy = target_y - self.position[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance < 0.01:
            # Too close to throw - just set velocity toward target
            self.velocity = (dx * 10, dy * 10)
            return self

        # Calculate throw velocity to reach target
        # Using projectile motion: y = y0 + vy*t - 0.5*g*t²
        # We want the ball to reach (target_x, target_y) at some time t
        # For simplicity, use a fixed flight time proportional to distance
        flight_time = max(distance / 50.0, 0.3)  # min 0.3s flight time

        # Horizontal velocity (constant, ignoring air resistance for initial calc)
        vx = dx / flight_time
        # Vertical velocity (to counteract gravity and reach target height)
        # target_y = self.y + vy*flight_time - 0.5*gravity*flight_time²
        vy = (dy + 0.5 * self.gravity * flight_time ** 2) / flight_time

        # Apply air resistance to initial velocity
        vx *= (1.0 - self.air_resistance)
        vy *= (1.0 - self.air_resistance)

        self.velocity = (vx, vy)

        # Record initial position
        self.trajectory.append((self.x, self.y, 0.0))

        return self

    def step(self, dt: float = 1.0 / 60.0) -> Ball:
        """Update ball position by one time step.

        Args:
            dt: Time step in seconds.

        Returns:
            Self for chaining.
        """
        if not self.is_active:
            return self

        # If trajectory is empty and ball is thrown, record initial position
        if not self.trajectory and self.is_thrown:
            self.trajectory.append((self.x, self.y, 0.0))

        # Record current position before updating
        current_time = sum(
            p[2] for p in self.trajectory
        ) + dt if self.trajectory else dt
        self.trajectory.append((self.x, self.y, current_time))

        # Apply gravity to vertical velocity
        self.velocity = (self.vx, self.vy - self.gravity * dt)

        # Apply air resistance
        speed = self.speed_yd_s
        if speed > 0.01:
            drag_factor = 1.0 - self.air_resistance
            self.velocity = (
                self.vx * drag_factor,
                self.vy * drag_factor,
            )

        # Update position
        new_x = self.x + self.vx * dt
        new_y = self.y + self.vy * dt
        self.position = (new_x, new_y)

        return self

    def _ensure_initial_position_recorded(self) -> None:
        """Ensure the initial position is recorded in the trajectory.

        This is called when the ball becomes active to record the starting position.
        """
        if not self.trajectory:
            self.trajectory.append((self.x, self.y, 0.0))

    def catch(
        self,
        catcher_id: str,
        catcher_position: Tuple[float, float],
        catcher_radius: float = 0.5,
    ) -> bool:
        """Attempt to catch the ball.

        Args:
            catcher_id: ID of the player attempting to catch.
            catcher_position: (x, y) position of the catcher.
            catcher_radius: Radius of the catcher in yards.

        Returns:
            True if the ball was caught, False otherwise.
        """
        if not self.is_thrown or self.is_caught or self.is_fumbled:
            return False

        dx = self.x - catcher_position[0]
        dy = self.y - catcher_position[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Ball is caught if within combined radius
        if distance <= self.radius + catcher_radius:
            self.is_caught = True
            self.catcher_id = catcher_id
            self.carrier_id = catcher_id
            self.velocity = (0.0, 0.0)
            self.position = catcher_position
            self.trajectory.append((self.x, self.y, 0.0))
            return True

        return False

    def fumble(
        self,
        carrier_id: str,
        carrier_position: Tuple[float, float],
        carrier_strength: float = 1.0,
        defender_strength: float = 1.0,
        collision_force: float = 0.0,
    ) -> bool:
        """Attempt to fumble the ball.

        Args:
            carrier_id: ID of the ball carrier.
            carrier_position: (x, y) position of the carrier.
            carrier_strength: Strength of the carrier (0-2).
            defender_strength: Strength of the defender (0-2).
            collision_force: Force of the collision.

        Returns:
            True if the ball was fumbled, False otherwise.
        """
        if not self.is_caught or self.is_fumbled:
            return False

        # Fumble probability based on strength differential and force
        strength_diff = carrier_strength - defender_strength
        fumble_threshold = 1.0 - strength_diff * 0.3
        fumble_chance = collision_force / (fumble_threshold + 0.01)

        # Simplified: if force exceeds threshold, fumble
        if fumble_chance > 0.5:
            self.is_fumbled = True
            self.carrier_id = None
            self.velocity = (
                self.vx + (collision_force * 0.5),
                self.vy + (collision_force * 0.3),
            )
            self.position = carrier_position
            self.trajectory.append((self.x, self.y, 0.0))
            return True

        return False

    def is_colliding_with(
        self,
        other_position: Tuple[float, float],
        other_radius: float = 0.5,
    ) -> bool:
        """Check if the ball is colliding with another entity.

        Args:
            other_position: (x, y) position of the other entity.
            other_radius: Radius of the other entity in yards.

        Returns:
            True if colliding, False otherwise.
        """
        dx = self.x - other_position[0]
        dy = self.y - other_position[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)
        return distance <= self.radius + other_radius

    def distance_to(self, target_position: Tuple[float, float]) -> float:
        """Calculate distance to a target position.

        Args:
            target_position: (x, y) target position.

        Returns:
            Distance in yards.
        """
        dx = self.x - target_position[0]
        dy = self.y - target_position[1]
        return math.sqrt(dx ** 2 + dy ** 2)

    def reset(self) -> Ball:
        """Reset the ball to its initial state.

        Returns:
            Self for chaining.
        """
        self.is_active = False
        self.is_thrown = False
        self.is_caught = False
        self.is_fumbled = False
        self.thrower_id = None
        self.catcher_id = None
        self.carrier_id = None
        self.velocity = (0.0, 0.0)
        self.trajectory = []
        self.collision_events = []
        return self

    def to_dict(self) -> dict:
        """Serialize the ball to a dictionary.

        Returns:
            Dictionary representation of the ball.
        """
        return {
            "ball_id": self.ball_id,
            "position": [self.x, self.y],
            "velocity": [self.vx, self.vy],
            "spin": self.spin,
            "is_active": self.is_active,
            "is_thrown": self.is_thrown,
            "is_caught": self.is_caught,
            "is_fumbled": self.is_fumbled,
            "thrower_id": self.thrower_id,
            "catcher_id": self.catcher_id,
            "carrier_id": self.carrier_id,
            "trajectory": self.trajectory,
        }

    def __repr__(self) -> str:
        state = "inactive"
        if self.is_active:
            if self.is_caught:
                state = "caught"
            elif self.is_fumbled:
                state = "fumbled"
            elif self.is_thrown:
                state = "thrown"
        return (
            f"Ball({self.ball_id}, pos=({self.x:.2f}, {self.y:.2f}), "
            f"vel=({self.vx:.2f}, {self.vy:.2f}), state={state})"
        )
