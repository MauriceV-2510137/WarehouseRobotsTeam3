import math
from core.pose import Pose

class OdometryEstimator:
    def __init__(self, wheel_radius: float, wheel_base: float):
        self.r = wheel_radius
        self.L = wheel_base

        self._prev_left = None
        self._prev_right = None

        self.pose = Pose()

    def update(self, left_enc: float, right_enc: float) -> Pose:
        # First call initialization
        if self._prev_left is None:
            self._prev_left = left_enc
            self._prev_right = right_enc
            return self.pose

        # Wheel displacement
        dl = (left_enc - self._prev_left) * self.r
        dr = (right_enc - self._prev_right) * self.r

        self._prev_left = left_enc
        self._prev_right = right_enc

        # Differential drive kinematics
        d = (dl + dr) / 2.0
        dtheta = (dr - dl) / self.L

        # Midpoint integration (more stable)
        theta_mid = self.pose.theta + dtheta / 2.0

        self.pose.x += d * math.cos(theta_mid)
        self.pose.y += d * math.sin(theta_mid)
        self.pose.theta += dtheta

        # Normalize angle
        self.pose.theta = math.atan2(
            math.sin(self.pose.theta),
            math.cos(self.pose.theta)
        )

        return self.pose