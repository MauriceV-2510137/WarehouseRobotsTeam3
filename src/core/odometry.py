import math
from core.pose import Pose

WHEEL_RADIUS = 0.033   # TurtleBot3 Burger
WHEEL_BASE   = 0.160

class OdometryEstimator:
    def __init__(self, wheel_radius=WHEEL_RADIUS, wheel_base=WHEEL_BASE):
        self.wheel_radius  = wheel_radius
        self.wheel_base    = wheel_base
        self._prev_left    = 0.0
        self._prev_right   = 0.0
        self._prev_theta   = 0.0
        self.pose          = Pose()

    def update(self, left_enc: float, right_enc: float, yaw: float) -> Pose:
        dl = (left_enc  - self._prev_left)  * self.wheel_radius
        dr = (right_enc - self._prev_right) * self.wheel_radius

        self._prev_left  = left_enc
        self._prev_right = right_enc

        d = (dl + dr) / 2.0
        
        # Use wheel encoders for heading instead of compass
        # This is more stable for differential drive robots
        d_theta = (dr - dl) / self.wheel_base
        self._prev_theta += d_theta
        
        # Normalize theta to [-pi, pi]
        self.pose.theta = (self._prev_theta + math.pi) % (2 * math.pi) - math.pi
        
        self.pose.x += d * math.cos(self.pose.theta)
        self.pose.y += d * math.sin(self.pose.theta)

        return self.pose