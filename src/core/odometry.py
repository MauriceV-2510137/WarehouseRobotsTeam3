import math
from core.pose import Pose
from core.robot_model import RobotModel

class OdometryEstimator:
    def __init__(self, model: RobotModel):
        self.model = model

        self.r = model.wheel_radius
        self.L = model.wheel_base

        self._prev_left = None
        self._prev_right = None

        self.pose = Pose()

    def update(self, left_enc: float, right_enc: float) -> Pose:

        # Initialize
        if self._prev_left is None:
            self._prev_left = left_enc
            self._prev_right = right_enc
            return self.pose

        # Wheel travel distances
        dl = (left_enc - self._prev_left) * self.r
        dr = (right_enc - self._prev_right) * self.r

        self._prev_left = left_enc
        self._prev_right = right_enc

        # Differential drive model
        d_center = (dl + dr) / 2.0
        d_theta = (dr - dl) / self.L

        # Midpoint integration (important stability improvement)
        theta_mid = self.pose.theta + d_theta / 2.0

        self.pose.x += d_center * math.cos(theta_mid)
        self.pose.y += d_center * math.sin(theta_mid)
        self.pose.theta += d_theta

        # Normalize angle
        self.pose.theta = math.atan2(
            math.sin(self.pose.theta),
            math.cos(self.pose.theta)
        )

        return self.pose