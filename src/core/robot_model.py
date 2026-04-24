from dataclasses import dataclass

@dataclass(frozen=True)
class RobotModel:
    # Geometry
    wheel_radius: float
    wheel_base: float

    # Motion limits
    max_wheel_speed: float
    max_linear_speed: float
    max_angular_speed: float

    # Control tuning defaults
    default_linear_gain: float = 1.0
    default_angular_gain: float = 2.5