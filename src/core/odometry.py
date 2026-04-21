import math
from src.core.pose import Pose

WHEEL_RADIUS = 0.033   # TurtleBot3 Burger
WHEEL_BASE   = 0.160

class OdometryEstimator:
    def __init__(self, wheel_radius=WHEEL_RADIUS, wheel_base=WHEEL_BASE):
        self.wheel_radius  = wheel_radius
        self.wheel_base    = wheel_base
        self._prev_left    = 0.0
        self._prev_right   = 0.0
        self.pose          = Pose()

    def update(self, left_enc: float, right_enc: float, yaw: float) -> Pose:
        dl = (left_enc  - self._prev_left)  * self.wheel_radius
        dr = (right_enc - self._prev_right) * self.wheel_radius

        self._prev_left  = left_enc
        self._prev_right = right_enc

        d = (dl + dr) / 2.0
        self.pose.theta = yaw
        self.pose.x += d * math.cos(yaw)
        self.pose.y += d * math.sin(yaw)

        return self.pose