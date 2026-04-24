import math
from core.pose import Pose

class Navigator:
    def __init__(self):
        self.target = None

        self.position_tolerance = 0.15
        self.angle_tolerance = 0.1

        self.k_linear = 1.0
        self.k_angular = 2.5

        self.max_linear = 0.6
        self.max_angular = 1.5

    def set_target(self, x: float, y: float):
        self.target = (x, y)

    def clear(self):
        self.target = None

    def is_done(self) -> bool:
        return self.target is None

    def compute(self, pose: Pose) -> tuple[float, float]:
        if self.target is None:
            return 0.0, 0.0

        tx, ty = self.target

        dx = tx - pose.x
        dy = ty - pose.y

        distance = math.hypot(dx, dy)

        # Stop condition
        if distance < self.position_tolerance:
            self.target = None
            return 0.0, 0.0

        # Heading
        target_angle = math.atan2(dy, dx)
        angle_error = target_angle - pose.theta

        angle_error = math.atan2(
            math.sin(angle_error),
            math.cos(angle_error)
        )

        # --- Control strategy ---
        # If facing wrong direction -> rotate first
        if abs(angle_error) > 0.5:
            linear = 0.0
        else:
            linear = self.k_linear * distance

        angular = self.k_angular * angle_error

        # Clamp
        linear = min(self.max_linear, linear)
        angular = max(-self.max_angular, min(self.max_angular, angular))

        return linear, angular