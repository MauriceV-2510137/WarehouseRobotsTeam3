import math
from core.pose import Pose

class Navigator:
    def __init__(self, position_tolerance=0.1, angle_tolerance=0.05):
        self.target = None
        self.position_tolerance = position_tolerance
        self.angle_tolerance    = angle_tolerance

    def set_target(self, x: float, y: float):
        self.target = (x, y)

    def is_done(self) -> bool:
        return self.target is None

    def compute(self, pose: Pose) -> tuple[float, float]:
        """
        Returns (linear_speed, angular_speed) toward the target.
        Returns (0, 0) if no target or target reached.
        """
        if self.target is None:
            return 0.0, 0.0

        tx, ty = self.target
        dx = tx - pose.x
        dy = ty - pose.y
        distance = math.hypot(dx, dy)

        if distance < self.position_tolerance:
            self.target = None
            return 0.0, 0.0

        # Angle to target vs current heading
        angle_to_target = math.atan2(dy, dx)
        angle_error = angle_to_target - pose.theta

        # Normalize to [-pi, pi]
        angle_error = (angle_error + math.pi) % (2 * math.pi) - math.pi

        # Proportional control
        angular = 1.5 * angle_error
        linear  = 0.5 * distance if abs(angle_error) < 0.3 else 0.0  # move only when roughly aligned

        return linear, angular