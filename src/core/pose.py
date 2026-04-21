from dataclasses import dataclass
import math

@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0  # radians, from compass