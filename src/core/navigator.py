import math
from core.pose import Pose
from core.robot_model import RobotModel

class Navigator:
    def __init__(self, model: RobotModel):
        self.target = None
        self._model = model

        self.position_tolerance = 0.1
        self.angle_tolerance = 0.08

        self.k_linear = model.default_linear_gain
        self.k_angular = model.default_angular_gain

    def set_target(self, x: float, y: float):
        self.target = (x, y)

    def clear(self):
        self.target = None

    def is_done(self) -> bool:
        return self.target is None
    
    def _normalize_angle(self, a: float) -> float:
        return math.atan2(math.sin(a), math.cos(a))

    def compute(self, pose: Pose) -> tuple[float, float]:
        if self.target is None:
            return 0.0, 0.0

        tx, ty = self.target

        dx = tx - pose.x
        dy = ty - pose.y

        distance = math.hypot(dx, dy)

        # --- Stop condition ---
        if distance < self.position_tolerance:
            self.target = None
            return 0.0, 0.0

        target_angle = math.atan2(dy, dx)
        angle_error = self._normalize_angle(target_angle - pose.theta)

        # --- Angular control ---
        angular = self.k_angular * angle_error
        angular = max(-self._model.max_angular_speed, min(self._model.max_angular_speed, angular))

        # --- Linear control (smooth + stable) ---
        alignment = math.cos(angle_error)

        # prevent backward motion
        alignment = max(0.0, alignment)

        # slow down when misaligned OR close to target
        linear = self.k_linear * distance * alignment

        # soft cap
        linear = min(linear, self._model.max_linear_speed)

        # final safety clamp near target behavior
        if abs(angle_error) > 0.8:
            linear = 0.0

        return linear, angular