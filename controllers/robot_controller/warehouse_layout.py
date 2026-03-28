from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

@dataclass(frozen=True)
class Aisle:
    index: int
    entry: Vec2
    target: Vec2

AISLES: dict[int, Aisle] = {
    0: Aisle(0, entry=Vec2(-2.0, 0.3), target=Vec2(-2.0, 2.0)),
    1: Aisle(1, entry=Vec2( 0.0, 0.3), target=Vec2( 0.0, 2.0)),
    2: Aisle(2, entry=Vec2( 2.0, 0.3), target=Vec2( 2.0, 2.0)),
}

# The resting places for the robots
ROBOT_HOMES: dict[str, Vec2] = {
    "robot0": Vec2(0.0, -0.5),
    "robot1": Vec2(0.5, -0.5),
    "robot2": Vec2(1.0, -0.5),
}
HOME_DEFAULT = Vec2(0.0, -0.5)