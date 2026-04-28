import math
from core.pose import Pose
from core.robot_model import RobotModel

class Navigator:

    def __init__(self, model: RobotModel) -> None:
        self._model = model

        self.target: tuple[float, float] | None = None
        self._reached_target = False

        self.position_tolerance = 0.02   # metres

        self.k_linear  = model.default_linear_gain
        self.k_angular = model.default_angular_gain

    # -------------------------------------------------------------------
    # Target management
    # -------------------------------------------------------------------
    def set_target(self, x: float, y: float) -> None:
        self.target = (x, y)
        self._reached_target = False

    def clear(self) -> None:
        self.target = None
        self._reached_target = False

    def has_target(self) -> bool:
        return self.target is not None

    def reached_target(self) -> bool:
        return self._reached_target

    def clear_reached(self) -> None:
        """Consume the one-shot 'reached' flag after the caller has acted on it."""
        self._reached_target = False

    def is_idle(self) -> bool:
        return self.target is None and not self._reached_target

    # -------------------------------------------------------------------
    # Velocity computation
    # -------------------------------------------------------------------
    def compute(self, pose: Pose) -> tuple[float, float]:
        if self.target is None:
            return 0.0, 0.0

        tx, ty = self.target
        dx = tx - pose.x
        dy = ty - pose.y
        distance = math.hypot(dx, dy)

        # --- Arrival check ---
        if distance < self.position_tolerance:
            self.target          = None
            self._reached_target = True
            return 0.0, 0.0

        # --- Bearing to target ---
        target_angle = math.atan2(dy, dx)
        angle_error  = self._normalize_angle(target_angle - pose.theta)

        # --- Angular control ---
        angular = self.k_angular * angle_error
        angular = max(-self._model.max_angular_speed,
                      min( self._model.max_angular_speed, angular))

        # --- Linear control ---
        # alignment smoothly reduces forward speed as misalignment grows.
        alignment = max(0.0, math.cos(angle_error))
        linear    = self.k_linear * distance * alignment
        linear    = min(linear, self._model.max_linear_speed)

        # Hard stop when angle error is large to avoid overshooting.
        if abs(angle_error) > 0.8:
            linear = 0.0

        return linear, angular

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    @staticmethod
    def _normalize_angle(a: float) -> float:
        """Wrap angle to (-pi, pi]."""
        return math.atan2(math.sin(a), math.cos(a))