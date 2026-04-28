import math
from core.pose import Pose
from core.robot_model import RobotModel

class OdometryEstimator:

    def __init__(self, model: RobotModel) -> None:
        self.r = model.wheel_radius   
        self.L = model.wheel_base     

        self._prev_left: float | None = None
        self._prev_right: float | None = None

        self.pose = Pose()

    def update(self, left_enc: float, right_enc: float, true_heading: float | None = None) -> Pose:
        if self._prev_left is None:
            self._prev_left  = left_enc
            self._prev_right = right_enc
            if true_heading is not None:
                self.pose.theta = true_heading
            return self.pose

        # Arc lengths since last step
        dl = (left_enc  - self._prev_left)  * self.r
        dr = (right_enc - self._prev_right) * self.r

        self._prev_left  = left_enc
        self._prev_right = right_enc

        d_center = (dl + dr) / 2.0
        d_theta  = (dr - dl) / self.L

        # Inside OdometryEstimator.update()
        if abs(d_theta) < 1e-6:
            self.pose.x += d_center * math.cos(self.pose.theta)
            self.pose.y += d_center * math.sin(self.pose.theta)
        else:
            radius = d_center / d_theta
            # Standard 2D rotation for Y-left
            self.pose.x += radius * (math.sin(self.pose.theta + d_theta) - math.sin(self.pose.theta))
            self.pose.y += radius * (math.cos(self.pose.theta) - math.cos(self.pose.theta + d_theta))

        # FUSION: Use absolute heading if provided, otherwise dead-reckon
        if true_heading is not None:
            self.pose.theta = true_heading
        else:
            self.pose.theta += d_theta
            self.pose.theta = math.atan2(math.sin(self.pose.theta), math.cos(self.pose.theta))

        return self.pose

    def reset(self, pose: Pose | None = None) -> None:
        self.pose = pose if pose is not None else Pose()
        self._prev_left  = None
        self._prev_right = None