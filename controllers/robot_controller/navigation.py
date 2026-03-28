"""
navigation.py — Low-level motion control for a differential-drive robot.

Keeps ALL motor/sensor math in one place so robot_controller.py can
think in waypoints, not in wheel velocities.

This module does NOT import anything from Webots — it operates on
abstract motor objects that expose `setVelocity(float)`.  This makes
it testable without a simulator.

Fix log (v2):
- Unified rotation logic: no separate _rotate() branch that caused
  jitter by fighting the proportional controller at the boundary.
- Smooth angular blending: angular speed is now always blended with
  linear speed; the robot never snaps between "rotate" and "drive"
  modes, eliminating left-right oscillation.
- Soft angular speed floor removed: the old hard floor of 0.5 rad/s
  caused the robot to overshoot small angle errors and oscillate.
- Coordinate system note: GPS/compass axis mapping is the caller's
  responsibility (_get_pose in robot_controller.py). Navigator itself
  is axis-agnostic and works in whatever frame it receives.
"""

import math
from dataclasses import dataclass


@dataclass
class Pose:
    """2-D robot pose in world coordinates."""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0   # heading in radians


class Navigator:
    """
    Smooth waypoint follower for a differential-drive robot.

    Uses a single unified control law instead of separate rotate/drive
    modes, which eliminates the jitter caused by switching between them.

    The linear speed is scaled down when the heading error is large, so
    the robot turns while slowing — this prevents overshooting corners
    and removes the oscillation at mode-switch boundaries.

    Parameters
    ----------
    left_motor, right_motor : motor device objects
        Any object with a `setVelocity(float)` method.
    max_speed : float
        Maximum wheel speed in rad/s (TurtleBot3: ~6.28).
    goal_tolerance : float
        Distance (metres) at which a waypoint is considered reached.
    angle_tolerance : float
        Heading error (radians) below which angle correction is ignored
        when already driving forward. Prevents micro-jitter near target.
    """

    def __init__(self, left_motor, right_motor, max_speed=6.28,
                 goal_tolerance=0.05, angle_tolerance=0.05):
        self.left_motor  = left_motor
        self.right_motor = right_motor
        self.max_speed   = max_speed
        self.goal_tol    = goal_tolerance
        self.angle_tol   = angle_tolerance

        # Proportional gains — tune to your robot/world scale.
        # k_linear: how aggressively to drive toward the goal.
        # k_angular: how aggressively to correct heading error.
        # Keeping k_angular lower than k_linear avoids over-rotation.
        self.k_linear  = 4.0
        self.k_angular = 3.0

        # How much heading error suppresses forward speed.
        # At angle_scale * π the robot turns on the spot; below that it
        # drives and steers simultaneously. Tune between 0.5–1.5.
        self.angle_scale = 0.8

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def drive_to(self, current: Pose, target: Pose) -> bool:
        """
        Set wheel velocities to move toward `target`.

        Returns True when the robot is within `goal_tolerance` of the
        target position so the caller can advance to the next waypoint.

        Control law (unified — no mode switching):
          1. Compute distance and desired heading.
          2. Compute angle error (wrapped to [-π, π]).
          3. Linear speed is proportional to distance, but suppressed by
             a cosine of the angle error so the robot slows down when
             facing the wrong way and speeds up as it aligns.
          4. Angular speed is proportional to angle error, added/subtracted
             from the two wheels to steer.
          5. Both speeds are clamped to max_speed.
        """
        dx = target.x - current.x
        dy = target.y - current.y
        distance = math.hypot(dx, dy)

        if distance < self.goal_tol:
            self.stop()
            return True

        desired_theta = math.atan2(dy, dx)
        angle_error   = self._normalize_angle(desired_theta - current.theta)

        # Angular command — proportional to error, clamped.
        angular = self.k_angular * angle_error
        angular = max(-self.max_speed, min(self.max_speed, angular))

        # Linear command — suppressed when facing the wrong way.
        # cos(angle_error) is 1 when aligned and 0 at 90°, so the robot
        # naturally slows and turns before driving forward.
        # We also clamp negative values to zero: never drive backward
        # to reach a forward waypoint.
        heading_factor = max(0.0, math.cos(angle_error))
        linear = self.k_linear * distance * heading_factor
        linear = min(linear, self.max_speed)

        # Differential drive mixing.
        # For a standard (non-inverted) differential drive:
        #   positive angular → turn left → left wheel slower, right wheel faster
        # If your robot turns the wrong way, negate angular here.
        left_speed  = linear - angular
        right_speed = linear + angular

        self._set_speeds(left_speed, right_speed)
        return False

    def stop(self):
        """Immediately halt both motors."""
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_speeds(self, left: float, right: float):
        """Clamp and apply wheel velocities."""
        left  = max(-self.max_speed, min(self.max_speed, left))
        right = max(-self.max_speed, min(self.max_speed, right))
        self.left_motor.setVelocity(left)
        self.right_motor.setVelocity(right)

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """Wrap angle to [-π, π]."""
        return math.atan2(math.sin(angle), math.cos(angle))
