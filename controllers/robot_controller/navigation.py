import math
from dataclasses import dataclass

@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0

    def distance_to(self, target_x: float, target_y: float) -> float:
        return math.hypot(target_x - self.x, target_y - self.y)

    def heading_error(self, target_x: float, target_y: float) -> float:
        desired = math.atan2(target_y - self.y, target_x - self.x)
        diff = desired - self.theta
        return math.atan2(math.sin(diff), math.cos(diff))

class WheelController:
    def __init__(self, left, right, max_speed: float):
        self._left = left
        self._right = right
        self._max = max_speed

    def drive(self, linear: float, angular: float):
        l = max(-self._max, min(self._max, linear - angular))
        r = max(-self._max, min(self._max, linear + angular))
        self._left.setVelocity(l)
        self._right.setVelocity(r)

    def stop(self):
        self._left.setVelocity(0.0)
        self._right.setVelocity(0.0)